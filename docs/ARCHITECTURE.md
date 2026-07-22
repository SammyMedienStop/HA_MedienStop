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
Wählt `video_<reason>` + `delay_<reason>`, spielt Video via `_play_media`,
plant TV-Aus nach `delay` s (`async_call_later` → `_do_off`). Guard `_off_pending`
verhindert Wiederholung. `_cancel_off()` bricht ab (z. B. wenn wieder berechtigt
oder Start). Ist keine URL gesetzt → sofort aus (delay 0).

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
!meal_pause`; Wechsel → `url_active/inactive` per HTTP GET. Elternmodus analog.

## Dashboard-Generator (`dashboard.py`)
`build_dashboard(num_children, num_profiles, child_names, profile_names, ids,
tab_users, admin_users)`. `ids` kommt aus `resolve_entity_ids(hass, entry_id)`
(Entity-Registry, unique_id→entity_id) → robust gegen umbenannte Entities.
Sichtbarkeit: Kinder-Tab `visible=[kid_user]`, Eltern-Tabs `visible=admin_users`.
Button „Dashboard-Vorlage erstellen" + Service `create_dashboard` posten das YAML
als Benachrichtigung.
