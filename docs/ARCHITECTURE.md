# Architektur

## Zentrale Klasse: `MedienStopManager` (`__init__.py`)
Hält den **gesamten Laufzeit-Zustand** pro Config-Entry. Wird in
`async_setup_entry` erzeugt und unter `hass.data[DOMAIN][entry_id]` abgelegt.
Alle Entities lesen/schreiben über diesen Manager. Aktualisierung der UI per
Dispatcher-Signal (`_notify()` → `SIGNAL_UPDATE`).

### setup-Reihenfolge (WICHTIG)
```
async_setup_entry:
  manager = MedienStopManager(...)          # __init__ setzt Defaults, wendet NICHTS an
  await async_forward_entry_setups(...)     # HIER restaurieren alle Restore-Entities
  # danach: Budget nur für Kinder OHNE wiederhergestellte Restzeit anwenden
  manager.start_clock()                     # registriert die Timer
```
`__init__` ruft **absichtlich kein** `apply_budgets_now()` mehr auf (früher Bug:
Restzeit wurde auf Default gesetzt, bevor 90 min restauriert waren → siehe PATCHLOG).

## Datenmodell
- `self.profiles[pid]` = `{name, budgets:{daytype:min}, windows:{daytype:[start,end]}}`
- `self.children[cid]` = `{name, profile:pid, pin, remaining, state,
   _remaining_restored, watched, watched_week/month/year, url_active, url_inactive,
   _was_active}`
- Globale Schalter: `system_active, holiday, parent_override, meal_pause,
  parent_autooff_enabled, parent_autooff_time`
- TV/Video: `tv_entity_id` (An/Aus + Erkennung), `video_player_id` (Streamen),
  `video_timeup/limit/notimer (+ _type)`, `delay_timeup/limit/notimer`
- Webhooks: `parent_url_active/inactive`, je Kind `url_active/inactive`
- Sichtbarkeit: `tab_users {cid:user}`, `admin_users [user]`

## Zeitgeber (in `start_clock`)
| Zeitgeber | Intervall | Zweck |
|---|---|---|
| `_loop` (@callback) | 60 s | laufende Timer herunterzählen + Abschalt-Entscheidung |
| `_enforce_tick` (@callback) | 15 s | schnelle Abschalt-Prüfung (NICHT herunterzählen) + Heartbeat `last_check` |
| `_midnight` (@callback) | täglich 00:00:05 | Restzeit = Budget des Tagtyps; watched-Reset (Tag/Woche/Monat/Jahr per Grenzvergleich) |
| `_autooff_fire` (@callback) | täglich zur `parent_autooff_time` | Elternmodus abschalten |
| `_on_tv_state` (@callback) | State-Event der `tv_entity_id` | bei echtem Aus: Timer pausieren + Elternmodus beenden |

## Kernstück: `_scan(daytype, decrement)` → (authorized, reason)
Beide Prüfungen (`_loop` mit decrement=True, `_enforce_tick` mit False) nutzen
DIESELBE Logik. `reason ∈ {"timeup","limit",None}`, sonst `None` → „notimer".
- Läuft ein Kind, aber **Fenster vorbei** → `reason="limit"` (Schlafenszeit) und
  Kind wird **pausiert** (damit später „notimer" gilt).
- Läuft ein Kind im Fenster, **Restzeit>0** → `authorized=True`.
- Restzeit ≤0 → `state=IDLE`, `reason="timeup"` (Budget aufgebraucht).
`parent_override` (Elternzeit) setzt `authorized=True` unabhängig davon.

## Abschalt-Sequenz `_goodbye_then_off(reason)`
Wählt `video_<reason>`/`tts_<reason>` + `delay_<reason>`. Ist `tts_<reason>` gesetzt
(Text-Ansage), hat sie **Vorrang** und wird per `_speak()` ausgegeben; sonst wird bei
gesetzter URL `_play_media()` genutzt. Danach TV-Aus nach `delay` s
(`async_call_later` → `_do_off`). Guard `_off_pending` verhindert Wiederholung.
`_cancel_off()` bricht ab (z. B. wenn wieder berechtigt oder Start). Ist weder Text
noch URL gesetzt → sofort aus (delay 0).

## Ansage-Quellen (`const.py` + `announce()`)
Je Grund wird **eine** Quelle gespeichert: `{"src": …, "delay": …}` plus je nach
Quelle `id`/`type`, `file`, `tts` oder `sound`.

| `src` | Bedeutung |
|---|---|
| `auto` | **Standard.** Mitgelieferte Vorlage, erst zur Laufzeit aufgelöst: `bundled_for(reason, audio=is_alexa)` → Audio für ein Echo, sonst Video. Folgt einem Gerätewechsel automatisch. |
| `video_*` / `audio_*` (6 Werte) | mitgelieferte Vorlage, fest gewählt; URL aus `BUNDLED_MEDIA` (raw.githubusercontent, Branch `main`) |
| `media` | eigene Datei aus dem Media-Browser (`media-source://`) |
| `www` | eigene Datei aus `<config>/www/`; nur der **Dateiname** wird gespeichert |
| `url` | frei eingegebene URL |
| `tts` | Text, den Alexa vorliest |
| `sound` | eingebauter Alexa-Klang (`media_content_type="sound"`) |
| `none` | keine Ansage → sofort aus |

`sources_for_target(is_alexa)` liefert die **anbietbare** Teilmenge: An einem Echo
fehlen `video_*` und `media`, an allem anderen `tts` und `sound`. Der Options-Flow
baut sein Auswahlfeld daraus, sodass unmögliche Kombinationen gar nicht erst
wählbar sind. `SRC_MIT_EINGABE` listet die Quellen, die ein zusätzliches Feld
brauchen — nur sie führen in den zweiten Dialogschritt (`async_step_detail`).

`normalize_announce()` liest die **alte** Form aus ≤ 2.4.x (`{id,type,delay,tts}`)
weiter und bildet deren Vorrang ab (TTS schlug Video). Es wird **nichts migriert** —
die neue Form entsteht erst, wenn der Nutzer genau diese Ansage speichert. Deshalb
gibt es weder einen `ConfigEntry.VERSION`-Bump noch `async_migrate_entry`.
`as_int()` ersetzt `int(x or default)`, damit eine Verzögerung von **0** erhalten
bleibt.

**Entscheidung und Ausführung sind getrennt** (seit 2.5.1):

| Funktion | Rolle |
|---|---|
| `_announce_plan(reason, cfg)` | rein, ohne Seiteneffekt → `(art, nutzlast, ctype, meldung)` mit `art ∈ {nein, play, speak, speak_ssml}`. Hier sitzen alle Prüfungen (Ziel vorhanden/verfügbar, Alexa-Grenzen, `auto`-Auflösung). |
| `announce(reason, cfg)` | **beiläufig** — stößt den Dienst nur an. Für `_goodbye_then_off`, wo nichts blockieren darf. Rückgabe heißt „abgeschickt", nicht „hat geklappt". |
| `async_announce(reason, cfg)` | **wartet ab** und liefert den echten Fehlertext. Für den Test-Knopf und `medienstop.test_video`. |

Der Unterschied ist keine Feinheit: Bis 2.5.0 gab es nur die beiläufige Variante, und
weil der Test-Knopf sie benutzte, meldete er **immer** Erfolg — ein stummer Echo war
nicht von einem funktionierenden zu unterscheiden.

Mit `cfg` lassen sich **ungespeicherte** Formularwerte abspielen — das ist der
Test-Knopf im Options-Flow. Die flachen Attribute (`video_*`, `tts_*`, `delay_*`)
bleiben aus Bestandsschutz erhalten und werden aus `media_cfg` abgeleitet.

`_target_is_alexa()` prüft über die Entity-Registry, ob hinter `media_target()` die
Integration `alexa_media` steckt. Ist das so, gilt:
- Videos und `media-source://`-Dateien werden **abgelehnt** (mit erklärender Meldung),
- Audio-URLs laufen über `_speak_audio_url()` → `_ssml_audio()` baut
  **`<speak><audio src="…"/></speak>`** und schickt es als `notify.alexa_media` mit
  **`type: "tts"`** (reiner Text nutzt weiterhin `announce`). Der `<speak>`-Rahmen ist
  Pflicht — ohne ihn verwirft Amazon die Datei kommentarlos (siehe PATCHLOG 2.5.1).

Vor allem anderen prüft `_announce_plan()` den **Zustand des Ziels**: Eine fehlende
Entity oder `unavailable`/`unknown` führt zur Absage mit Klartext. `off` bleibt
zulässig, weil `play_media` einen ausgeschalteten Fernseher aufwecken kann.

## Vorlagen kommen aus dem Heimnetz (seit 2.5.2)
Viele Fernseher und **DLNA-Renderer können kein HTTPS** — sie nehmen `play_media` an
und tun nichts, HTTP 200 inklusive. Deshalb gilt im `play`-Zweig:
`_vorlage_aus_dem_heimnetz()` legt eine `BUNDLED_MEDIA`-Datei einmalig unter
`<config>/www/medienstop/` ab und liefert die `http://`-Adresse aus
`get_url(prefer_external=False)`. Geschrieben wird atomar (`.teil` → `os.replace`),
damit ein Abbruch keine halbe Datei hinterlässt, die später als „schon da" gilt.
Jeder Fehler fällt auf die Original-URL zurück.

Der **Alexa-Zweig geht diesen Weg nicht**: Amazons Server lädt selbst und verlangt
gerade die öffentliche HTTPS-Adresse.

`async_vorlagen_vorladen()` zieht den Download in den Start vor
(`entry.async_create_background_task` in `async_setup_entry`, nach `start_clock()`).
Sonst fiele er mitten in eine Abschaltung, während die Verzögerung schon läuft.
Geladen wird nur, was die Konfiguration braucht — bei Alexa-Zielen und eigenen
Quellen gar nichts.

## Warum Alexa einen Sonderweg braucht
Ein Echo kann per `media_player.play_media` **keine** beliebigen Dateien abspielen.
Der einzige Weg ist ein SSML-`<audio>`-Tag; Amazons Server lädt die Datei dann
**selbst**. Daraus folgen harte Auflagen (Details in `media/README.md`):
MP3 **MPEG Version 2**, **48 kbps** CBR, **16000/22050/24000 Hz**, ≤ 240 s, und
erreichbar über **öffentliches HTTPS mit gültigem Zertifikat**. Passt etwas nicht,
bleibt der Lautsprecher stumm — **ohne Fehlermeldung**.
Deshalb: `<config>/www/` (→ `/local/…`, wird **ohne** Auth-Token ausgeliefert) ist der
einzige gangbare Ort für eigene Dateien; `media_source`-URLs scheitern, weil Amazons
Abrufer kein Token hat. `_public_local_url()` baut die Adresse zur Laufzeit über
`get_url(..., require_ssl=True)`, damit ein Wechsel der externen Adresse nichts bricht.

## Text-Ansage `_speak(text)` / `_async_speak(text)`
Alternative zu Video/Audio-Datei, v. a. für **Alexa/Echo-Lautsprecher**: ruft den
`notify.alexa_media`-Service der (separaten, per HACS installierten) Integration
**Alexa Media Player** auf (`data.type="announce"`), sodass Amazons eigene
Sprachausgabe den Text direkt vorliest – es muss dafür keine Mediendatei gehostet
werden. Existiert der Service nicht (Integration fehlt/nicht eingerichtet) oder
schlägt der Aufruf fehl (z. B. „Communications" für das Gerät in der Alexa-App nicht
aktiviert), gibt es eine `persistent_notification` mit Fehlerhinweis, analog zu
`_play_media`. Zielentity ist wie bei `_play_media` immer `media_target()` – dieselbe
Entity kann also entweder für Video/URL oder für Text-Ansagen konfiguriert werden.

## Tagtyp (`current_daytype`) — „Schulnacht"-Logik
`holiday` → `ferien`. Sonst: `weekday() in (4,5)` (Fr, Sa) → `wochenende`, sonst
`werktag`. D. h. **Sonntag zählt als Werktag** (Montag = Schule).

## Fenster (`within_window`) & Budget (`child_budget`)
`within_window`: `start <= now <= end` (bei start==end = ganztags erlaubt).
`child_budget`: `_profile_of(cid)["budgets"][daytype]`. `apply_budgets_now`: setzt
Restzeit aller Kinder = child_budget (Mitternacht + „Budgets anwenden"-Button).

## Persistenz / Restore
- RestoreNumber: Profil-Budgets, Auto-Aus-Verzögerungen (falls vorhanden)
- RestoreEntity: Zeitfenster (time), Profil-Auswahl (select), PIN + URLs (text)
- RestoreSensor: `remaining` (Restzeit!), `watched*`
- Switches mit `restore=True`: `system_active`, `holiday`, `parent_autooff_enabled`,
  `parent_override` (Elternmodus). **Transient** (kein Restore): `meal_pause`.
- Videos/Sichtbarkeit/TV-Auswahl liegen in `entry.data` (Options-Flow) → per se
  update-fest.

## TV/Video-Steuerung
- `media_target()` = `video_player_id or tv_entity_id`.
- `_tv_is_on()`: True, wenn State NICHT in `_TV_OFF_STATES`
  (`off/unavailable/unknown/none/standby/idle/""`) → deckt media_player ab.
- `_set_tv(on)`: `homeassistant.turn_on/off` auf `tv_entity_id`.
- `_play_media(url,type)`: `media_player.play_media` DIREKT mit
  `media_content_id` (media-source:// oder http) an `media_target()`; blocking,
  Fehler → persistent_notification. Logs auf WARNING.
- `_on_tv_state`: reagiert NUR auf `_TV_HARD_OFF_STATES={"off","standby"}` und nur
  wenn vorher an — sonst würde ein idle/unavailable-Blip fälschlich Elternmodus
  beenden.

## Webhooks (`_sync_webhooks`)
Flankengesteuert: je Kind `active = running & remaining>0 & within_window &
!meal_pause`; Wechsel → `url_active/inactive`. Elternmodus analog.

`_fire_webhook` ruft **HTTP POST** auf (HA-Webhook-Trigger akzeptieren per Default
nur POST/PUT und antworten auf GET mit **405**); nur bei 405/501 wird auf **GET**
zurückgefallen (IFTTT & Co.). Der Antwort-Status wird ausgewertet und Erfolg wie
Misserfolg auf **WARNING** protokolliert — früher wurde per GET gefeuert, der Status
nie geprüft und nur auf INFO geloggt, weshalb HA-Webhooks vollkommen still nie
ausgelöst wurden.

Beim **ersten** `_sync_webhooks()`-Lauf nach dem Start werden die Flanken-Merker nur
abgeglichen (`_webhooks_primed`), ohne zu feuern — sonst meldet ein per RestoreEntity
wiederhergestellter Elternmodus nach jedem Neustart fälschlich eine „aktiv"-Flanke.

> Hook-URLs sind Entity-States und damit auf **255 Zeichen** begrenzt (harte
> HA-Grenze `MAX_LENGTH_STATE_STATE`). HA-Webhook-URLs liegen deutlich darunter.

## Not-Aus: `system_active`
Ist der Schalter **aus**, greift die Integration gar nicht mehr in den Fernseher ein
und zählt nichts mit:
- `_set_tv()` bricht als **zentrales Sicherheitsnetz** jede Schaltung ab (beide
  Richtungen) — deckt auch verzögerte Aufrufer wie `_do_off` ab.
- `_do_off()` verwirft zusätzlich explizit eine bereits geplante Abschaltung
  (`_goodbye_then_off` plant bis zu 600 s im Voraus).
- `_enforce_tick`/`_loop` rufen `_cancel_off()` **vor** ihrem Early-Return; die
  Zählblöcke (`_scan(decrement=True)`, `parent_watched`) liegen bewusst **dahinter**
  → keine Statistik läuft mit.
- `switch.py::_apply` bricht eine schwebende Abschaltung sofort ab, statt auf den
  nächsten Tick zu warten.
- `_on_tv_state` und `_autooff_fire` bleiben ungeguardet: sie führen nur internen
  Zustand nach und schalten selbst nichts.
- `_midnight` läuft weiter — es zählt nichts, sondern setzt das Tagesbudget und
  erkennt Wochen-/Monats-/Jahreswechsel.

## Dashboard-Generator (`dashboard.py`)
`build_dashboard(num_children, num_profiles, child_names, profile_names, ids,
tab_users, admin_users)`. `ids` kommt aus `resolve_entity_ids(hass, entry_id)`
(Entity-Registry, unique_id→entity_id) → robust gegen umbenannte Entities.
Sichtbarkeit: Kinder-Tab `visible=[kid_user]`, Eltern-Tabs `visible=admin_users`.
Button „Dashboard-Vorlage erstellen" + Service `create_dashboard` posten das YAML
als Benachrichtigung.

## Sprache / Zweisprachigkeit (`texts.py`)
Alles Sichtbare folgt der **Home-Assistant-Sprache** (`hass.config.language`: `en` →
Englisch, alles andere → Deutsch):
- Einrichtung, Entity-Namen, Service-Beschreibungen: `strings.json` +
  `translations/{de,en}.json` (HA-Mechanik, beide Dateien synchron halten).
- Dashboard-Generator und Hub-Benachrichtigungen: `lang`-Parameter / `_lang(hass)`
  (`dashboard.py`, `button.py`).
- **Laufzeittexte**, die HA nicht übersetzen kann — `HomeAssistantError`-Meldungen
  (Hinweis im Dashboard), Rückmeldungen der Ansage-Weiche, Diagnose-Bericht,
  Fehler-Benachrichtigungen: zentral in `texts.py` (`TEXTS["de"|"en"]`,
  `t(hass, key, **fmt)`; Manager-Kurzform `self.t(...)`). Neue Nutzertexte gehören
  dorthin, nie als Literal in den Code. Fehlende Schlüssel fallen auf Deutsch zurück.
- Log-Ausgaben (`_LOGGER`) bleiben Deutsch (Entwickler-/Diagnosesicht).
- README: `README.md` (DE) und `README_EN.md` (EN) mit Sprachzeile oben; `info.md`
  (HACS) zweisprachig in einer Datei.
