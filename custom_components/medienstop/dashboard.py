# custom_components/medienstop/dashboard.py
# -----------------------------------------------------------------------------
# Eingebauter Dashboard-GENERATOR (flache Tabs).
#
# WICHTIG gegen "Entitaet nicht gefunden":
#   Beim Umbenennen von Geräten kann HA auch die Entitaets-IDs ändern
#   (sensor.kind_1_restzeit -> sensor.lukas_restzeit). Damit das Dashboard
#   trotzdem immer passt, arbeitet der Generator mit einem "ids"-Mapping:
#   Schlüssel = stabile Kennung (z.B. "kind_1_remaining"), Wert = ECHTE
#   Entity-ID. Der Button füllt dieses Mapping aus der Entity-Registry.
#   Ohne Mapping (Standalone) werden die Standard-IDs verwendet.
# -----------------------------------------------------------------------------

from __future__ import annotations

import yaml  # in Home Assistant immer vorhanden

DAYS = [("werktag", "Werktag"), ("wochenende", "Wochenende"), ("ferien", "Ferien")]

# Standard-Entity-IDs der Hub-Schalter (wenn nichts umbenannt wurde).
_HUB_DEFAULTS = {
    "tv_active": "binary_sensor.medienstop_fernseher_aktiv",
    "system_active": "switch.medienstop_system_aktiv",
    "holiday": "switch.medienstop_ferien_heute",
    "parent_override": "switch.medienstop_elternzeit",
    "meal_pause": "switch.medienstop_essenspause",
    "parent_autooff_enabled": "switch.medienstop_elternzeit_auto_aus",
    "parent_autooff_time": "time.medienstop_elternzeit_auto_aus_zeit",
    "parent_url_active": "text.medienstop_de_elternmodus_hook_aktiv",
    "parent_url_inactive": "text.medienstop_de_elternmodus_hook_inaktiv",
    "parent_watched": "sensor.medienstop_de_elternzeit_heute",
    "parent_watched_week": "sensor.medienstop_de_elternzeit_woche",
    "parent_watched_month": "sensor.medienstop_de_elternzeit_monat",
    "parent_watched_year": "sensor.medienstop_de_elternzeit_jahr",
}


def _default_eid(suffix: str) -> str:
    """Konventionelle Entity-ID aus der stabilen Kennung (Fallback)."""
    if suffix in _HUB_DEFAULTS:
        return _HUB_DEFAULTS[suffix]
    # Kinder: "kind_<n>_<art>" (art kann mehrteilig sein, z.B. watched_week)
    if suffix.startswith("kind_"):
        parts = suffix.split("_")
        base = f"kind_{parts[1]}"
        art = "_".join(parts[2:])
        return {
            "remaining": f"sensor.{base}_restzeit",
            "watched": f"sensor.{base}_heute_geschaut",
            "watched_week": f"sensor.{base}_diese_woche",
            "watched_month": f"sensor.{base}_dieser_monat",
            "watched_year": f"sensor.{base}_dieses_jahr",
            "status": f"sensor.{base}_status",
            "pin": f"text.{base}_pin",
            "profile": f"select.{base}_profil",
            "url_active": f"text.{base}_hook_aktiv",
            "url_inactive": f"text.{base}_hook_inaktiv",
        }.get(art, f"sensor.{suffix}")
    # Profile: Budgets + Zeitfenster
    if "_budget_" in suffix:
        return f"number.{suffix}"
    if suffix.endswith("_start") or suffix.endswith("_ende"):
        return f"time.{suffix}"
    return suffix


def build_dashboard(num_children: int, num_profiles: int,
                    child_names: dict | None = None,
                    profile_names: dict | None = None,
                    ids: dict | None = None,
                    tab_users: dict | None = None,
                    admin_users: list | None = None) -> dict:
    """Flache Tab-Struktur: Eltern + je Profil + je Kind."""
    num_children = max(1, int(num_children))
    num_profiles = max(1, int(num_profiles))
    child_names = child_names or {}
    profile_names = profile_names or {}
    ids = ids or {}

    def E(suffix: str) -> str:
        """Echte Entity-ID (aus Registry) oder Standard-Fallback."""
        return ids.get(suffix) or _default_eid(suffix)

    def cname(n): return child_names.get(f"kind_{n}", f"Kind {n}")
    def pname(p): return profile_names.get(f"profil_{p}", f"Profil {p}")

    # --- System-Karte (mit Sammel-Buttons direkt darunter) ------------------
    def system_card():
        system = {"type": "entities", "title": "System", "show_header_toggle": False,
                  "entities": [
                      {"entity": E("tv_active"), "name": "Fernseher aktiv"},
                      {"entity": E("system_active"), "name": "System aktiv"},
                      {"entity": E("holiday"), "name": "Ferien heute"},
                      {"entity": E("parent_override"), "name": "Elternzeit"},
                      {"entity": E("meal_pause"), "name": "Essenspause"},
                      {"entity": E("parent_autooff_enabled"), "name": "Elternzeit Auto-Aus"},
                      {"entity": E("parent_autooff_time"), "name": "Auto-Aus Zeit"},
                  ]}
        buttons = {"type": "horizontal-stack", "cards": [
            {"type": "button", "name": "+15 ALLE", "icon": "mdi:account-multiple-plus",
             "tap_action": {"action": "call-service", "service": "medienstop.add_time",
                            "data": {"child": "alle", "minutes": 15}}},
            {"type": "button", "name": "+30 ALLE", "icon": "mdi:account-multiple-plus",
             "tap_action": {"action": "call-service", "service": "medienstop.add_time",
                            "data": {"child": "alle", "minutes": 30}}},
            {"type": "button", "name": "Budgets anwenden", "icon": "mdi:refresh",
             "tap_action": {"action": "call-service", "service": "medienstop.apply_budgets_now"}},
        ]}
        return {"type": "vertical-stack", "cards": [system, buttons]}

    # --- Eltern-Karte je Kind (mit Stop) ------------------------------------
    def parent_child_card(n, display):
        cid = f"kind_{n}"
        return {
            "type": "entities", "title": display,
            "entities": [
                {"entity": E(f"{cid}_profile")},
                {"entity": E(f"{cid}_pin")},
                {"entity": E(f"{cid}_remaining")},
                {"entity": E(f"{cid}_watched")},
                {"entity": E(f"{cid}_status")},
            ],
            "footer": {"type": "buttons", "entities": [
                {"entity": E(f"{cid}_remaining"), "name": "+15", "icon": "mdi:plus",
                 "tap_action": {"action": "call-service", "service": "medienstop.add_time",
                                "data": {"child": cid, "minutes": 15}}},
                {"entity": E(f"{cid}_remaining"), "name": "+30", "icon": "mdi:plus",
                 "tap_action": {"action": "call-service", "service": "medienstop.add_time",
                                "data": {"child": cid, "minutes": 30}}},
                {"entity": E(f"{cid}_remaining"), "name": "Stop", "icon": "mdi:stop",
                 "tap_action": {"action": "call-service", "service": "medienstop.stop_timer",
                                "data": {"child": cid}}},
            ]},
        }

    # --- Profil-Tab ---------------------------------------------------------
    def profile_view(p, display):
        pid = f"profil_{p}"
        ents = [{"entity": E(f"{pid}_budget_{k}")} for k, _ in DAYS]
        for k, _ in DAYS:
            ents.append({"entity": E(f"{pid}_{k}_start")})
            ents.append({"entity": E(f"{pid}_{k}_ende")})
        return {"title": display, "path": pid, "icon": "mdi:timer-cog-outline",
                "cards": [{"type": "entities", "title": display, "entities": ents}]}

    # --- Kind-Tab (nur Play/Pause) ------------------------------------------
    def kid_view(n, display):
        cid = f"kind_{n}"
        st = E(f"{cid}_status")
        return {
            "title": display, "path": cid, "icon": "mdi:television-play",
            "cards": [
                {"type": "markdown",
                 "content": (f"# {display}\n"
                             f"## Noch {{{{ states('{E(f'{cid}_remaining')}') }}}} Minuten\n"
                             f"Heute geschaut: {{{{ states('{E(f'{cid}_watched')}') }}}} min\n\n"
                             f"Status: {{{{ states('{st}') }}}}")},
                {"type": "horizontal-stack", "cards": [
                    {"type": "conditional",
                     "conditions": [
                         {"entity": st, "state_not": "leer"},
                         {"entity": st, "state_not": "läuft"},
                         {"entity": st, "state_not": "belegt"},
                         {"entity": st, "state_not": "gesperrt"},
                     ],
                     "card": {"type": "button", "name": "Play", "icon": "mdi:play",
                              "tap_action": {"action": "call-service",
                                             "service": "medienstop.start_timer",
                                             "data": {"child": cid}}}},
                    {"type": "conditional",
                     "conditions": [{"entity": st, "state": "läuft"}],
                     "card": {"type": "button", "name": "Pause", "icon": "mdi:pause",
                              "tap_action": {"action": "call-service",
                                             "service": "medienstop.pause_timer",
                                             "data": {"child": cid}}}},
                ]},
            ],
        }

    eltern_cards = [system_card()]
    eltern_cards.append({"type": "horizontal-stack", "cards": [
        {"type": "button", "name": "Test Abschied", "icon": "mdi:movie-open-play",
         "tap_action": {"action": "call-service", "service": "medienstop.test_video",
                        "data": {"which": "timeup"}}},
        {"type": "button", "name": "Test Limit", "icon": "mdi:movie-open-play",
         "tap_action": {"action": "call-service", "service": "medienstop.test_video",
                        "data": {"which": "limit"}}},
        {"type": "button", "name": "Test Hinweis", "icon": "mdi:movie-open-play",
         "tap_action": {"action": "call-service", "service": "medienstop.test_video",
                        "data": {"which": "notimer"}}},
    ]})
    eltern_cards += [parent_child_card(n, cname(n)) for n in range(1, num_children + 1)]
    views = [{"title": "Eltern", "path": "eltern",
              "icon": "mdi:account-supervisor", "cards": eltern_cards}]
    for p in range(1, num_profiles + 1):
        views.append(profile_view(p, pname(p)))
    for n in range(1, num_children + 1):
        views.append(kid_view(n, cname(n)))

    # --- Statistik-Tab: geschaute Zeit + Zuruecksetzen (mit Bestaetigung) ----
    stat_cards = [{
        "type": "button", "name": "Statistik ALLE zurücksetzen",
        "icon": "mdi:backup-restore",
        "tap_action": {
            "action": "call-service", "service": "medienstop.reset_statistics",
            "data": {"child": "alle"},
            "confirmation": {"text": "Wirklich die Statistik ALLER Kinder zurücksetzen?"},
        },
    }]
    for n in range(1, num_children + 1):
        cid = f"kind_{n}"
        ents = {"type": "entities", "title": cname(n), "entities": [
            {"entity": E(f"{cid}_watched"), "name": "Heute"},
            {"entity": E(f"{cid}_watched_week"), "name": "Diese Woche"},
            {"entity": E(f"{cid}_watched_month"), "name": "Dieser Monat"},
            {"entity": E(f"{cid}_watched_year"), "name": "Dieses Jahr"},
        ]}
        reset_btn = {
            "type": "button", "name": "Zurücksetzen", "icon": "mdi:eye-refresh-outline",
            "tap_action": {
                "action": "call-service", "service": "medienstop.reset_statistics",
                "data": {"child": cid},
                "confirmation": {"text": f"Statistik von {cname(n)} wirklich zurücksetzen?"},
            },
        }
        stat_cards.append({"type": "vertical-stack", "cards": [ents, reset_btn]})
    # Elternzeit-Statistik (am Hub gezählt)
    stat_cards.append({"type": "entities", "title": "Elternzeit", "entities": [
        {"entity": E("parent_watched"), "name": "Heute"},
        {"entity": E("parent_watched_week"), "name": "Diese Woche"},
        {"entity": E("parent_watched_month"), "name": "Dieser Monat"},
        {"entity": E("parent_watched_year"), "name": "Dieses Jahr"},
    ]})
    # Diagramm: Fernsehzeit pro Tag (Balken) je Kind + Elternzeit (nutzt HA-Langzeitstatistik).
    graph_entities = [E(f"kind_{n}_watched") for n in range(1, num_children + 1)]
    graph_entities.append(E("parent_watched"))
    stat_cards.append({
        "type": "statistics-graph", "title": "Fernsehzeit pro Tag (Minuten)",
        "chart_type": "bar", "period": "day", "days_to_show": 30,
        "stat_types": ["change"], "entities": graph_entities,
    })
    views.append({"title": "Statistik", "path": "statistik",
                  "icon": "mdi:chart-bar", "cards": stat_cards})

    # --- Hooks-Tab: Webhook-URLs (Aktiv/Inaktiv) ----------------------------
    hook_cards = [{"type": "markdown",
                   "content": "### Webhook-URLs\nWerden per HTTP aufgerufen, wenn ein "
                              "Timer startet/stoppt bzw. der Elternmodus wechselt."}]
    for n in range(1, num_children + 1):
        cid = f"kind_{n}"
        hook_cards.append({"type": "entities", "title": cname(n), "entities": [
            {"entity": E(f"{cid}_url_active"), "name": "Aktiv-URL"},
            {"entity": E(f"{cid}_url_inactive"), "name": "Inaktiv-URL"},
        ]})
    hook_cards.append({"type": "entities", "title": "Elternmodus", "entities": [
        {"entity": E("parent_url_active"), "name": "Aktiv-URL"},
        {"entity": E("parent_url_inactive"), "name": "Inaktiv-URL"},
    ]})
    views.append({"title": "Hooks", "path": "hooks",
                  "icon": "mdi:webhook", "cards": hook_cards})

    # --- Sichtbarkeit je Benutzer (persistent in der Integration) -----------
    tu = tab_users or {}
    admin_vis = [{"user": u} for u in (admin_users or [])]
    for v in views:
        path = v.get("path") or ""
        if path.startswith("kind_") and tu.get(path):
            # Kinder-Tab: NUR das jeweilige Kind (nicht die Eltern).
            v["visible"] = [{"user": tu[path]}]
        elif admin_vis and (path in ("eltern", "statistik", "video", "hooks")
                            or path.startswith("profil_")):
            # Eltern-/Einstellungs-Tabs: NUR die Eltern.
            v["visible"] = admin_vis

    return {"title": "MedienStop.de", "views": views}


def build_dashboard_yaml(num_children: int, num_profiles: int,
                         child_names: dict | None = None,
                         profile_names: dict | None = None,
                         ids: dict | None = None,
                         tab_users: dict | None = None,
                         admin_users: list | None = None) -> str:
    return yaml.safe_dump(
        build_dashboard(num_children, num_profiles, child_names, profile_names, ids,
                        tab_users, admin_users),
        allow_unicode=True, sort_keys=False,
    )
