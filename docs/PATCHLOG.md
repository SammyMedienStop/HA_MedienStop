# Patchlog (technisches Entwickler-Log)

Chronologie der wichtigsten Fixes mit **Symptom → Ursache → Lösung**. Ergänzt die
nutzerseitige `CHANGELOG.md` um das „Warum".

## [2.7.1] Play-Knopf trotz gesperrter Zeit — Status und Startbefehl waren uneinig
- **Symptom:** (Screenshot eines Nutzers, Freitag 21.08.2026, 17:33) Kind-Tab zeigt
  „Noch 30 Minuten", Status **„bereit"** und einen **Play-Knopf**. Drückt das Kind ihn,
  kommt „Die Aktion medienstop/start_timer konnte nicht ausgeführt werden. Außerhalb
  der erlaubten Zeit für Lina."
- **Ursache:** `status_text()` prüfte `within_window()` **nur im RUNNING-Zweig**. Ein
  ruhendes oder pausiertes Kind außerhalb des Fensters meldete deshalb `bereit` bzw.
  `pausiert`. Das Dashboard blendet den Play-Knopf nur bei
  `{leer, läuft, belegt, gesperrt}` aus — `bereit` rutschte durch. `start_timer()`
  prüfte das Fenster dagegen korrekt und lehnte ab. Zwei Stellen, zwei Meinungen: die
  Oberfläche bot eine Aktion an, die nie funktionieren konnte.
- **Lösung:** Die Fenster-Prüfung wandert in `status_text()` **vor** die
  Zustands-Abfragen: außerhalb des Fensters ist der Status immer `gesperrt`. Der
  RUNNING-Zweig braucht die Prüfung damit nicht mehr. Reihenfolge bleibt
  `Essenspause → leer → gesperrt → läuft → belegt → pausiert → bereit`; `leer` steht
  bewusst vor `gesperrt` (ohne Restzeit ist das Fenster irrelevant).
- **Kein neues Dashboard nötig:** Bereits erzeugte Vorlagen schließen `gesperrt` schon
  aus, der Knopf verschwindet also von selbst.
- **Zusätzlich:** Die Ablehnung nennt jetzt das **geltende Fenster**
  („… (erlaubt 08:00-16:00 Uhr)"). Ohne das war aus der Meldung nicht zu erkennen,
  welches Fenster überhaupt greift — Profil, Tagtyp oder geteilter Sonntag.
- **Nicht die Ursache:** Der 21.08.2026 war ein **Freitag** (zählt bereits als
  Wochenende) und 17:33 ist kein Vormittag — der Sonntags-Fix aus 2.7.0 hätte diesen
  Fall nicht berührt. Warum Linas Fenster damals endete, sagt der Screenshot nicht;
  genau dafür steht das Fenster jetzt in der Meldung.

## [2.7.0] „Kein Fernsehen" am Sonntagvormittag — Sonntag zählte als Werktag
- **Symptom:** (Forum-Meldung) Zeitfenster 8–23 Uhr eingestellt, trotzdem meldet die
  Integration um 11 Uhr „außerhalb der erlaubten Zeit". Mehrfach aufgetreten.
- **Ursache:** Kein Rechenfehler in `within_window` — die „Schulnacht"-Logik zählte
  den **Sonntag als Werktag** (`weekday() in (4,5)` → Wochenende, sonst Werktag).
  Wer das Werktag-Fenster auf „nach der Schule" gestellt hat (z. B. 16–19 Uhr), bekam
  am Sonntag genau dieses Fenster — der gemeldete Vormittag lag davor. Der Fehler trat
  deshalb **nur sonntags** auf, was zu „schon mehrfach vorgekommen" passt. Das
  eingestellte 8–23-Uhr-Fenster war das vom Wochenende und griff nie.
- **Lösung:** Neuer Config-Key `sunday_mode` (Konfigurieren → Grundeinstellungen).
  Standard `split`: `current_daytype()` liefert sonntags den **Wochenend**-Tagtyp
  (Budget + Fenster-Beginn), und die neue Methode `window_bounds()` ersetzt allein das
  Fenster-**Ende** durch das des Werktags — der Vormittag ist frei, die Schulnacht
  bleibt. `wochenende` und `werktag` sind wählbar, `werktag` ist exakt das alte
  Verhalten. `window_bounds()` ist die einzige Stelle mit dieser Sonderregel; alle
  Prüfungen laufen über `within_window()` und erben sie automatisch.
- **Zwei Sicherungen gegen unsinnige Fenster:** Ein Werktag-Fenster mit
  `start == end` („ganztags") kappt nichts, und ein Werktag-Ende **vor** dem
  Wochenend-Beginn würde ein dauerhaft leeres Fenster ergeben — beides lässt das
  Wochenend-Ende stehen, statt den Sonntag komplett zu sperren.
- **Zweite mögliche Ursache derselben Meldung (nicht geändert):** Wird der Fernseher
  eingeschaltet, ohne dass jemand im Dashboard auf Play drückt, läuft kein Timer und
  nach 15 s kommt die Ansage „Keine TV-Zeit". Für Eltern klingt das identisch. Das
  ist gewolltes Verhalten; eine eigene Ansage („Zeit wäre da, aber Play fehlt") wäre
  ein separater Ansage-Grund.

## [2.5.4] Kinder konnten fremde Timer und den Elternmodus bedienen
- **Symptom:** Elternmodus an → Kinder werden zwar pausiert, aber ein Kind konnte
  die Elternzeit wieder ausschalten bzw. den Timer eines Geschwisterkinds
  starten/stoppen. „Kinder dürfen keinen Modus eines anderen stoppen oder starten"
  wurde nicht eingehalten.
- **Ursache:** Es gab **keine serverseitige Berechtigungsprüfung**. Die Services
  (`start_timer`, `pause_timer`, `stop_timer`, `add_time`, …) und die Hub-Switches
  nahmen jeden Aufruf an. Die Absicherung bestand nur aus der Lovelace-Tab-
  Sichtbarkeit (`visible: [{user}]`) – die versteckt aber nur den Reiter; der
  View-Pfad bleibt per URL erreichbar, und Entities sind über die Suche/More-Info
  für jeden angemeldeten Benutzer schaltbar.
- **Lösung:** `MedienStopManager.async_check_user(user_id, cid, action)` wertet die
  bestehende Zuordnung aus *Sichtbarkeit* (`tab_users`, `admin_users`) aus.
  Kind-Benutzer (in `tab_users` eingetragen) dürfen nur `start/pause/stop` für ihr
  eigenes `cid`; alles andere wirft `HomeAssistantError` (erscheint als Meldung im
  Dashboard) und loggt auf WARNING. Frei bleiben: kein Benutzer im Kontext
  (Automationen), `admin_users`, HA-Admins (`hass.auth.async_get_user().is_admin`)
  und Benutzer ohne Zuordnung (Bestandsschutz). Der auslösende Benutzer kommt bei
  Services aus `call.context.user_id`, bei den Switches aus `entity._context`
  (HA setzt ihn vor jedem Entity-Service-Aufruf per `async_set_context`).
  Zusätzlich pausiert `_scan()` laufende Kinder, solange `parent_override` an ist –
  Sicherheitsnetz, damit während der Elternzeit nie Restzeit abläuft oder Statistik
  zählt, egal auf welchem Weg ein Kind auf `running` kam.
- **Nicht abgedeckt (bewusst):** Budgets/Zeitfenster/PIN-Text/Profil-Auswahl sind
  Entities ohne Benutzerprüfung; ein Kind-Benutzer könnte sie über More-Info ändern.
  Falls das gebraucht wird: dieselbe Prüfung in `number/time/text/select.py` einbauen.

## [2.5.2] Fernseher spielte die Vorlage nicht — DLNA-Renderer kann kein HTTPS
- **Symptom:** Test-Knopf gedrückt, Integration meldet Erfolg, Bildschirm bleibt
  schwarz. Am Echo lief dieselbe Ansage einwandfrei.
- **Ursache:** Zwei Schichten. (a) Das eingetragene Ziel war die
  `panasonic_viera`-Entity — die nimmt `play_media` an, streamt aber nicht (bekanntes
  Muster bei Panasonic/Samsung/LG/AndroidTV, siehe Gotcha 6). Der eigentliche Abspieler
  ist der **`dlna_dmr`**-Renderer, der erst existiert, wenn der TV **an** ist.
  (b) Auch mit richtigem Ziel blieb es schwarz: Der Renderer holt sich `https://`-URLs
  nicht. Direkt gegengemessen — identische Datei, identisches Ziel:
  `http://<ha>:8123/local/…` → `state=playing`, `https://raw.githubusercontent.com/…`
  → `state=idle`. `media_player.play_media` liefert in **beiden** Fällen HTTP 200; der
  Fehlschlag ist von HA aus nicht erkennbar. Bei Alexa fällt das nie auf, weil dort
  Amazons Server lädt und HTTPS gerade **verlangt**.
- **Lösung:** `_vorlage_aus_dem_heimnetz()` legt eine mitgelieferte Vorlage einmalig
  unter `<config>/www/medienstop/` ab (atomar über `.teil` + `os.replace`, damit ein
  Abbruch keine halbe Datei hinterlässt) und liefert die `http://`-Adresse aus
  `get_url(prefer_external=False)`. Greift nur für `BUNDLED_MEDIA`-URLs und nur im
  `play`-Zweig — der Alexa-Zweig (`speak_ssml`) behält die GitHub-Adresse. Jeder
  Fehler fällt auf die Original-URL zurück, also nie schlechter als vorher.
  `_async_play_media` gibt zusätzlich die **tatsächlich** genutzte Adresse zurück,
  damit der Test-Knopf nicht die GitHub-URL anzeigt, während lokal abgespielt wird.

## [2.5.2] Download traf genau den falschen Moment
- **Symptom:** Die erste Ansage nach einer Neuinstallation kam mit spürbarer
  Verzögerung — im Zweifel erst, nachdem der Fernseher schon aus war.
- **Ursache:** Die lokale Kopie entstand **lazy**, also beim ersten Abspielen. Genau
  dann läuft aber schon die Abschalt-Verzögerung (Standard 10 s, hier 20 s) gegen
  einen 10-MB-Download.
- **Lösung:** `async_vorlagen_vorladen()` wird in `async_setup_entry` per
  `entry.async_create_background_task` angestoßen — **nach** `start_clock()` und
  bewusst als Task, damit der HA-Start nicht auf das Netz wartet (gemessen: HA nach
  21 s bedienbar, 29 MB nach 44 s vollständig). Ein Reload nach Konfigurationsänderung
  wiederholt es, sodass ein Wechsel des Zielgeräts nachzieht. Geladen wird nur, was die
  aktuelle Konfiguration braucht; Alexa-Ziele und eigene Quellen lösen nichts aus.
- **Merke für die Fehlersuche:** Auf dieser Instanz ist die Datei-Protokollierung
  abgeschaltet (`home-assistant.log` existiert nicht, `/api/error_log` liefert 404).
  Diagnose läuft deshalb über den Options-Flow (`description_placeholders["ergebnis"]`)
  und über Zustandsabfragen, nicht über das Log.

## [2.5.1] Alexa blieb stumm — SSML ohne `<speak>`-Rahmen
- **Symptom:** Audio-Vorlage auf einem Echo ausgewählt, „Jetzt testen" angehakt,
  abgeschickt — **kein Ton**, keine Fehlermeldung, nichts im Protokoll. Der Dialog
  meldete sogar Erfolg.
- **Ursache:** `_speak_audio_url()` schickte `<audio src='…'/>` **ohne** umschließendes
  `<speak>…</speak>`. Der Alexa Media Player erkennt eine Nachricht nur dann als SSML,
  wenn sie in `<speak>` steht; andernfalls verwirft Amazon den `<audio>`-Tag
  kommentarlos. `notify.alexa_media` liefert dabei weiterhin HTTP 200 — der Fehlschlag
  ist von außen nicht sichtbar. (Verifiziert gegen eine echte Instanz: alle drei
  Varianten HTTP 200, hörbar war nur die Fassung mit `<speak>`.)
- **Lösung:** `_ssml_audio()` baut `<speak><audio src="…"/></speak>`, maskiert `&`/`<`/`>`
  in der URL (ein Query-Parameter machte das SSML sonst ungültig — ebenfalls stiller
  Fehlschlag) und setzt die URL in doppelte Anführungszeichen. `target` wird jetzt als
  Liste übergeben, wie `notify.alexa_media` es erwartet.

## [2.5.1] „Jetzt testen" konnte gar nicht fehlschlagen
- **Symptom:** Der Test-Knopf meldete ausnahmslos Erfolg — auch wenn kein Ton kam, das
  Zielgerät nicht existierte oder `notify.alexa_media` gar nicht installiert war.
  Dadurch war jede Fehlersuche blind.
- **Ursache:** `announce()` rief `_speak()`/`_play_media()`, die den Dienst-Aufruf nur
  per `async_create_task` **anstoßen** und sofort zurückkehren. Der Rückgabewert hieß
  faktisch „abgeschickt", wurde aber als „hat geklappt" ausgegeben. Fehler landeten
  bestenfalls in einer persistent_notification, die im Optionsdialog niemand sieht.
- **Lösung:** Entscheidung und Ausführung getrennt: `_announce_plan()` liefert ohne
  Seiteneffekt, *was* zu tun ist; `announce()` bleibt der beiläufige Weg für die
  Abschaltsequenz (dort darf nichts blockieren), neu ist `async_announce()`, das den
  Dienst-Aufruf **abwartet** und den echten Fehlertext zurückgibt. Options-Flow und
  `medienstop.test_video` nutzen die await-Variante; `notify_on_error=False`
  unterdrückt dort die doppelte Benachrichtigung.

## [2.5.1] Totes Zielgerät — Ansagen verschwanden spurlos
- **Symptom:** Alle Ansagen wirkungslos, obwohl Konfiguration und Alexa-Integration in
  Ordnung waren.
- **Ursache:** Als Video-Player war ein Gerät eingetragen, dessen Entity `unavailable`
  war. `media_player.play_media` bzw. `notify.alexa_media` nehmen einen solchen Aufruf
  klaglos entgegen — es passiert nur nichts. Da `media_target()` den Video-Player dem
  Fernseher vorzieht, ging **jede** Ansage an dieses tote Gerät.
- **Lösung:** `_announce_plan()` prüft den Zustand des Ziels: fehlende Entity und
  `unavailable`/`unknown` führen zu einer erklärenden Absage. `off` bleibt zulässig —
  `play_media` kann einen ausgeschalteten Fernseher aufwecken.

## [2.5.1] Ansage-Dialog verleitete zu unmöglichen Kombinationen
- **Symptom:** Man konnte am Echo eine Video-Vorlage wählen oder am Fernseher eine
  Text-Ansage; acht Eingabefelder standen gleichzeitig da, von denen nur eines zählte.
- **Ursache:** Ein einziges statisches Formular mit allen Quellen und allen Feldern —
  Home Assistant kann Felder nicht dynamisch ein-/ausblenden, also wurde alles gezeigt.
- **Lösung:** Dreifach entschärft. (a) Neue Quelle `SRC_AUTO` („Mitgelieferte Ansage"),
  die erst zur Laufzeit über `bundled_for(reason, audio=is_alexa)` in Video oder Audio
  aufgelöst wird — dadurch ist die Kombination nie falsch und folgt einem Gerätewechsel
  automatisch. (b) `sources_for_target()` filtert die Auswahlliste nach dem Ziel, statt
  erst beim Test abzulehnen. (c) Der Dialog ist zweistufig: Schritt 1 nur Quelle,
  Verzögerung, Test; Quellen aus `SRC_MIT_EINGABE` führen in `async_step_detail` mit
  genau einem Feld. Bei den Vorlagen entfällt der zweite Schritt.

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
