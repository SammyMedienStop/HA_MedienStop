# Patchlog (technisches Entwickler-Log)

Chronologie der wichtigsten Fixes mit **Symptom → Ursache → Lösung**. Ergänzt die
nutzerseitige `CHANGELOG.md` um das „Warum".

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
