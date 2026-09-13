# Referenz (Services, Config, Entities, Zustände)

## Services (Domain `medienstop`)
| Service | Felder | Zweck |
|---|---|---|
| `start_timer` | child, pin? | Play (Kind); nur mit Restzeit>0, im Fenster, nur ein Kind, nicht bei Elternmodus/Essenspause |
| `pause_timer` | child | Pause |
| `stop_timer` | child | Restzeit auf 0 |
| `add_time` | child?, minutes | Minuten gutschreiben; child leer/„alle" = alle Kinder |
| `set_pin` | child, pin? | PIN setzen/löschen |
| `apply_budgets_now` | – | Restzeit sofort = Budget des Tagtyps |
| `create_dashboard` | children?, profiles? | Dashboard-YAML als Benachrichtigung |
| `play_media` | media? / url? / content_type? | beliebiges Medium an TV streamen (Test) |
| `test_video` | which? (timeup/limit/notimer) | konfiguriertes Video sofort abspielen |

**Berechtigung (serverseitig, `MedienStopManager.async_check_user`):** Ist der
auslösende HA-Benutzer (`call.context.user_id`) unter *Sichtbarkeit* einem Kind
zugeordnet (`tab_users`), darf er nur `start_timer`/`pause_timer`/`stop_timer` für
**dieses** Kind; alle anderen Services und die Hub-Switches (Elternzeit, System aktiv,
Ferien, Essenspause, Auto-Aus) werfen `HomeAssistantError`. Frei: `admin_users`,
HA-Admins, Automationen (kein Benutzer im Kontext) und Benutzer ohne Zuordnung.

## Config-Keys (entry.data)
`num_children (1-9)`, `num_profiles (1-5)`, `tv_entity`, `video_player`,
`kid_dashboard`, `names {kind_n/profil_n: Name}`, `tab_users {kind_n: user_id}`,
`admin_users [user_id]`, `videos {timeup/limit/notimer: {src, delay, …}}`,
`parent_kid_tab (bool, Standard true)` – Sammel-Tab „Kinder" im Dashboard, nur für
`admin_users` sichtbar; wirkt erst beim **nächsten Erzeugen** der Dashboard-Vorlage.

Ein Ansage-Eintrag hat immer `src` (Quelle) und `delay` (Sekunden bis TV-Aus), plus
je nach Quelle ein Feld: `id`+`type` (bei `media`/`url`/Vorlagen), `file` (bei `www`,
nur der Dateiname), `tts` oder `sound`. Mögliche `src`-Werte:
`auto` (**Standard** — mitgelieferte Vorlage, erst zur Laufzeit als Audio oder Video
aufgelöst; speichert außer `delay` kein weiteres Feld),
`video_timeup|video_limit|video_notimer|audio_timeup|audio_limit|audio_notimer`
(fest gewählte Vorlagen), `media`, `www`, `url`, `tts`, `sound`, `none`.

> Einträge aus ≤ 2.4.x (`{id, type, delay, tts}`) werden von `normalize_announce()`
> beim Lesen weiterhin verstanden — es wird nichts migriert oder umgeschrieben.
> Details siehe `docs/ARCHITECTURE.md`.

## Entities & entity_id-Muster
Hub-Gerät „MedienStop.de" (Anzeigename; interner Slug „medienstop" bei
Alt-Installationen, „medienstop_de" bei neu angelegten):
- switch: `system_active, holiday, parent_override, meal_pause,
  parent_autooff_enabled`
- time: `parent_autooff_time`
- binary_sensor: `tv_active` → `binary_sensor.…_fernseher_aktiv`
- sensor: `last_check` (Letzte Prüfung, Timestamp/Heartbeat)
- button: `make_dashboard` (Dashboard-Vorlage), `diagnose`, `video_test`
- text (Hub): `parent_url_active/inactive`

Pro Profil (Gerät „Profil X"):
- number: `{pid}_budget_{werktag|wochenende|ferien}`
- time: `{pid}_{daytype}_{start|ende}`

Pro Kind (Gerät „Kind X"):
- sensor: `{cid}_remaining` (Restzeit), `{cid}_watched` (Heute geschaut),
  `{cid}_watched_week|month|year`, `{cid}_status`
- select: `{cid}_profile` (Profil-Zuweisung)
- text: `{cid}_pin`, `{cid}_url_active`, `{cid}_url_inactive`

> Unique-ID-Schema: immer `f"{entry_id}_{suffix}"`. entity_ids können durch
> Umbenennen abweichen → Dashboard nutzt `resolve_entity_ids` (Registry).

## Interne Zustände (`children[cid]["state"]`)
`idle` / `running` / `paused` (Konstanten STATE_*).

## Status-Sensor-Werte (STATUS_*, für Dashboard-Bedingungen)
`leer` (Restzeit 0), `bereit` (Zeit da, nicht gestartet), `läuft`, `pausiert`,
`gesperrt` (läuft, außerhalb Fenster), `belegt` (anderes Kind/Elternzeit aktiv).
Kinder-Play-Button erscheint nur, wenn Status NICHT in
{leer, läuft, belegt, gesperrt}.

## Video-Gründe (reason)
- `timeup` — Tages-Budget aufgebraucht (innerhalb Fenster).
- `limit` — Zeitfenster-Ende erreicht (Schlafenszeit), während ein Kind schaute.
- `notimer` — TV an, aber kein aktiver Timer / außerhalb erlaubter Zeit.
Je Grund eigene URL + eigene Verzögerung (Sekunden bis TV-Aus).

## Tagtypen & Zeitlogik
`werktag` = So–Do, `wochenende` = Fr+Sa, `ferien` = Ferien-Schalter (überschreibt).
Mitternachts-Reset 00:00:05 setzt Restzeit = Budget des dann aktuellen Tagtyps.
