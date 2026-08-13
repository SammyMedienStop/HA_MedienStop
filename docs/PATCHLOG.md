# Patchlog (technisches Entwickler-Log)

Chronologie der wichtigsten Fixes mit **Symptom → Ursache → Lösung**. Ergänzt die
nutzerseitige `CHANGELOG.md` um das „Warum".

## [2.5.0] Alexa konnte keine eigenen Audiodateien abspielen
- **Symptom:** Ein als Video-Player eingetragenes Echo blieb bei Datei-Ansagen stumm;
  der Media-Browser meldete „Mediaplayer unterstützt kein Auswählen aus Medienquellen".
- **Ursache:** Zwei unabhängige Grenzen. (a) Die `alexa_media`-Integration
  implementiert kein `browse_media` → daher die Media-Browser-Meldung. (b) Amazon
  erlaubt eigene Audios **nur** über einen SSML-`<audio>`-Tag; `media_player.play_media`
  mit beliebigen URLs funktioniert bei Alexa nicht (Issue alandtse/alexa_media_player
  #3163, geschlossen als „amazonissue / not planned"). Zusätzlich prüft Amazon das
  Format streng: MPEG **Version 2**, **48 kbps** CBR, **16000/22050/24000 Hz**, ≤ 240 s,
  erreichbar über **öffentliches HTTPS**. Die mitgelieferten MP3 waren MPEG1 / ~86 kbps
  VBR / 48000 Hz und verletzten damit drei von vier Vorgaben — Amazon lehnt sie
  **ohne jede Fehlermeldung** ab.
- **Lösung:** `_speak_audio_url()` sendet `<audio src='…'/>` als `notify.alexa_media`
  mit `type: "tts"` (reiner Text nutzt weiterhin `announce`). `_target_is_alexa()`
  erkennt das Ziel über die Entity-Registry und lehnt Videos/`media-source://` mit
  erklärender Meldung ab, statt still zu scheitern. Die MP3 in `media/` wurden
  in-place konvertiert (`-b:a 48k -ar 24000 -ac 1`, ohne ID3/Xing-Header) und werden
  über `raw.githubusercontent.com` als **Vorlagen** angeboten — dadurch braucht ein
  Endnutzer für die mitgelieferten Ansagen weder Nabu Casa noch das Kopieren von
  Dateien. Für eigene Dateien ist `<config>/www/` der einzige gangbare Ort, weil
  `/local/…` **ohne** Auth-Token ausgeliefert wird; `media_source`-URLs scheitern,
  weil Amazons Abrufer kein Token besitzt.

## [2.5.0] Options-Flow: Datenverluste und starrer Durchlauf
- **Symptom:** Für eine kleine Änderung an einer Ansage musste man vier Formulare
  durchklicken; ein einmal gesetztes Video ließ sich nie wieder entfernen.
- **Ursachen (mehrere, alle im selben Code):**
  * `async_step_init` baute `self._new` von Null auf und `async_update_entry(data=…)`
    **ersetzte** `entry.data` komplett → alles musste unterwegs neu eingesammelt werden.
  * `_collect_videos` hatte einen Rückfall `elif cur.get("id")` — eine Einbahnstraße:
    leere Felder stellten den alten Wert wieder her, Löschen war unmöglich.
  * `int(user_input.get(…, 10) or 10)` machte aus einer **0** eine 10 (identisch in
    `__init__.py`), eine Verzögerung von 0 s war nicht einstellbar.
  * `if entry:` verwarf Einträge, die nur eine Verzögerung hatten.
  * `_collect_names`/`_collect_visibility` iterierten nur `1..num_children` → beim
    Verringern der Kinderzahl gingen Namen und Tab-Zuordnungen unwiderruflich verloren.
  * `async_update_entry` + `async_create_entry(data={})` lösten **zwei** Reloads aus.
- **Lösung:** `async_show_menu` als Einstieg, jeder Bereich speichert selbst per
  Merge (`{**entry.data, **changes}`); Quellen-Modell (`src`) statt implizitem
  Vorrang; `as_int()` statt `or default`; Namen/Tab-Zuordnungen werden gemerged;
  `async_create_entry(data=dict(entry.options))` vermeidet den zweiten Reload.
  Rückwärtskompatibilität über `normalize_announce()` **ohne** Migration — die alte
  Form wird beim Lesen verstanden, die neue erst beim nächsten Speichern geschrieben.
  Der Media-Browser bleibt die einzige Ausnahme vom „leer = gelöscht"-Prinzip: er
  startet technisch bedingt immer leer, daher bedeutet leer dort „bisherige behalten".

## [2.4.1] Prüfung starb nach dem Verstellen der Auto-Aus-Zeit (Kern-Bug)
- **Symptom:** Nach einiger Zeit reagierte die Integration nicht mehr — Fernseher
  wurde nicht abgeschaltet, Sensor „Letzte Prüfung" fror ein, Hooks feuerten nicht.
- **Ursache:** `_schedule_autooff()` meldete neben `_unsub_autooff` auch
  `_unsub_enforce` (15-s-Tick), `_unsub_tvstate` (TV-Listener) und `_unsub_off` ab —
  und registrierte sie **nie wieder**. Der Block war erkennbar aus `shutdown()`
  kopiert. Beim Start blieb das folgenlos, weil `start_clock()` `_schedule_autooff()`
  **vor** der Registrierung aufruft; aber jeder spätere Aufruf (Auto-Aus-Schalter,
  Auto-Aus-Zeit ändern, Restore der Zeit-Entity) legte die Hintergrundprüfung
  dauerhaft lahm. Zusätzlich verfälschte `self.last_reset = now().date()` die
  Wochen-/Monats-Rollover-Erkennung in `_midnight`.
- **Lösung:** `_schedule_autooff()` fasst nur noch den Auto-Aus-Zeitgeber an.
  Stub-Test: `start_clock()` → `set_autooff_time(...)` → `_unsub_enforce` muss
  identisch bleiben.

## [2.4.1] „System aktiv = aus" wirkte nicht
- **Symptom:** Trotz ausgeschaltetem Schalter wurde der Fernseher weiter abgeschaltet.
- **Ursache:** `_goodbye_then_off` plant die Abschaltung via `async_call_later` bis zu
  600 s im Voraus. `_do_off()` (und `_set_tv()` selbst) prüften `system_active` nicht,
  und `_cancel_off()` lag in `_enforce_tick`/`_loop` **hinter** den Early-Returns —
  eine schwebende Abschaltung wurde bei deaktiviertem System also nie abgebrochen.
- **Lösung:** Zentrales Sicherheitsnetz in `_set_tv()` (beide Richtungen), expliziter
  Guard in `_do_off()`, `_cancel_off()` vor die Early-Returns gezogen, und
  `switch.py::_apply` bricht beim Ausschalten sofort ab. **Wichtig beim Weiterbauen:**
  die Zählblöcke (`_scan(decrement=True)`, `parent_watched`) müssen hinter dem
  Early-Return in `_loop` bleiben — sonst liefe die Statistik im Not-Aus weiter.

## [2.4.1] Hooks feuerten nie (und meldeten keinen Fehler)
- **Symptom:** Die hinterlegten Hook-URLs lösten nichts aus; im Protokoll stand nichts.
- **Ursache:** `_fire_webhook` benutzte **HTTP GET**. Home-Assistant-Webhook-Trigger
  akzeptieren per Default nur POST/PUT und antworten auf GET mit **405**. Der
  Antwort-Status wurde nie geprüft (keine Exception → `except` griff nicht), und der
  einzige Erfolgs-Log lief auf **INFO**, das bei diesem Nutzer nicht geschrieben wird
  (siehe Gotcha weiter unten). Ergebnis: vollkommen stille Fehlfunktion. Zusätzlich
  wurde die Response nie freigegeben (kein `async with`) → Connection-Leak.
- **Lösung:** POST als Primärweg, GET nur als Rückfall bei 405/501, Status auswerten,
  Erfolg **und** Fehler auf WARNING loggen, `async with` verwenden.
- **Nachgelagert:** `_parent_was_active`/`_was_active` überleben keinen Neustart,
  `parent_override` per Restore aber schon → nach jedem Neustart feuerte fälschlich
  `parent_url_active`. Gelöst über `_webhooks_primed`: der erste Lauf gleicht die
  Merker nur ab, ohne zu feuern. **Offen:** `child["state"]` wird weiterhin nicht
  persistiert, ein vor dem Neustart laufendes Kind wird also nicht mit „inaktiv"
  quittiert (Kandidat für `RestoreSensor` in einer späteren Version).

## [2.0.2] Zeitfenster-Ende zeigte falsches Video
- **Symptom:** Bei Erreichen der End-Uhrzeit (z. B. 20 Uhr) kam das „kein Timer"-
  Video (notimer) statt des „Schlafenszeit"-Videos (limit).
- **Ursache:** `_enforce_tick` (alle 15 s) rief immer `_goodbye_then_off("notimer")`.
  Es feuerte VOR dem Minuten-Loop (der „limit" gekannt hätte) und blockierte ihn
  via `_off_pending`.
- **Lösung:** Gemeinsame Methode `_scan(daytype, decrement)` liefert
  (authorized, reason) für BEIDE Prüfungen. Bei Fensterende → „limit" + Kind
  pausieren (danach gilt „notimer" für erneute TV-Starts). timeup weiterhin beim
  Herunterzählen auf 0.

## [2.0.1] Restzeit nach Neustart auf Default (90→60)
- **Symptom:** Budget 90 eingestellt (Feld zeigt 90), aber am nächsten Tag / nach
  Neustart nur 60 min freigegeben.
- **Ursache:** `apply_budgets_now()` wurde in `MedienStopManager.__init__` aufgerufen
  — BEVOR die RestoreNumber die 90 wiederhergestellt hatten. Restzeit wurde daher
  aus den **Default-Budgets** (Werktag=60) gesetzt und bei Neustart nicht korrigiert.
- **Lösung:** (a) `apply_budgets_now()` aus `__init__` entfernt; in
  `async_setup_entry` NACH dem Restore nur für Kinder ohne wiederhergestellte
  Restzeit anwenden. (b) `RemainingSensor` ist jetzt `RestoreSensor` → Restzeit
  übersteht Neustart (Flag `_remaining_restored`).

## [pre-2.0.1] Elternmodus ging bei ungewolltem HA-Neustart verloren → TV aus
- **Symptom:** „Fernseher ging aus, obwohl Elternmodus aktiv war" (~12 Uhr; im Log
  ein ungewollter Neustart um 12:02).
- **Ursache:** `parent_override` war transient; nach Neustart wieder False →
  niemand berechtigt → Abschaltung.
- **Lösung:** `parent_override`-Switch mit `restore=True` (wie holiday/system_active).

## [pre-2.0.1] Elternmodus endete bei idle/unavailable-Blip → dann Video+Aus
- **Ursache:** `_on_tv_state` reagierte auf ALLE „Aus"-Zustände inkl.
  `idle/unavailable/unknown`. Kurzer Blip der Panasonic-Entity beendete Elternmodus,
  danach griff die Abschalt-Logik.
- **Lösung:** Nur `_TV_HARD_OFF_STATES={"off","standby"}` UND vorher „an".

## [pre-2.0.0] „Prüfung lief gar nicht" — Fernseher ging nie aus, Heartbeat „Unbekannt"
- **Symptom:** Sensor „Letzte Prüfung" = Unbekannt; TV wurde nie abgeschaltet.
- **Ursache (Kern-Bug):** Timer-Callbacks (`_loop`, `_enforce_tick`, `_midnight`,
  `_autooff_fire`) waren normale Methoden → HA führte sie im **Executor-Thread** aus.
  Dort schlagen `async_create_task` (turn_off) und `async_dispatcher_send` fehl.
- **Lösung:** `@callback`-Dekorator auf alle Zeitgeber-Callbacks → laufen im Eventloop.
- **Diagnose eingebaut:** Diagnose-Button (persistent_notification mit vollem Zustand),
  Heartbeat-Sensor „Letzte Prüfung", `_diag_log` (später auf WARNING angehoben, weil
  INFO bei diesem Nutzer nicht ins Log geschrieben wird).

## Video-Streaming / Panasonic
- **Symptom:** Statt Stream öffnete sich der TV-Browser; zeitweise „gar nichts".
- **Ursache 1:** Vorab-Auflösung von `media-source://` in eine HTTP-URL — der TV
  konnte sie nicht laden. **Lösung:** media-source **direkt** an play_media schicken
  (HA löst pro Gerät auf), `blocking=True`, Fehler-Notification.
- **Ursache 2 (geräteabhängig):** `panasonic_viera`-`play_media` öffnet URLs im
  TV-Browser (bekanntes Verhalten; auch Samsung/LG/AndroidTV). **Lösung:** separater
  **Video-Player** (`CONF_VIDEO_PLAYER`, Cast/Chromecast oder DLNA Digital Media
  Renderer). `media_target()` bevorzugt ihn.

## Weitere designrelevante Entscheidungen
- **Entity-IDs stabil halten:** Beim Umbenennen von Geräten kann HA Entity-IDs
  ändern. Der Dashboard-Generator löst deshalb über die **Entity-Registry**
  (`resolve_entity_ids`) auf statt fester IDs.
- **Tab-Sichtbarkeit update-fest:** in `entry.data` (tab_users/admin_users) statt nur
  im Dashboard-YAML → der Generator schreibt `visible:` reproduzierbar.
- **Anzeigename „MedienStop.de", Domain bleibt `medienstop`:** nur sichtbare Strings
  geändert, niemals die Domain/IDs.
- **Nur ein Kind gleichzeitig**, Kinder können nicht stoppen, Start bei Restzeit 0
  gesperrt; Essenspause = Hart-Aus; „Schulnacht"-Tagtyp (Fr+Sa=Wochenende).
