# custom_components/medienstop/button.py
# Knopf am Hub: "Dashboard-Vorlage erstellen".
# Erzeugt aus der eingestellten Anzahl + den echten Gerätenamen ein fertiges
# Dashboard-YAML (ein Tab je Kind/Profil) und zeigt es als kopierbare
# Benachrichtigung. Auch ohne Technikwissen nutzbar.

from __future__ import annotations

import time

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .dashboard import build_dashboard_yaml
from .entity import (
    MedienStopEntity,
    child_device,
    device_display_name,
    hub_device,
    resolve_entity_ids,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    entities = [GenerateDashboardButton(manager), DiagnoseButton(manager),
                VideoTestButton(manager, "timeup"),
                VideoTestButton(manager, "limit"),
                VideoTestButton(manager, "notimer"),
                ResetStatsAllButton(manager)]
    # Pro Kind ein eigener "Statistik zurücksetzen"-Knopf.
    for cid in manager.children:
        entities.append(ResetStatsChildButton(manager, cid))
    async_add_entities(entities)


def _lang(hass) -> str:
    """"en" wenn die HA-Sprache Englisch ist, sonst "de"."""
    return "en" if (hass.config.language or "de")[:2].lower() == "en" else "de"


# Zweisprachige Benachrichtigungs-Texte (folgt der HA-Sprache).
_NOTIF = {
    "de": {
        "dash_title": "MedienStop.de – Dashboard-Vorlage",
        "dash_instructions": (
            "**So baust du daraus dein Dashboard (kein Technikwissen noetig):**\n\n"
            "1. Einstellungen -> Dashboards -> *Dashboard hinzufügen* -> leeres Dashboard.\n"
            "2. Dashboard öffnen, oben rechts Stift (Bearbeiten), dann drei Punkte -> "
            "**Raw-Konfigurationseditor**.\n"
            "3. Den Text unten komplett markieren, kopieren, dort einfuegen -> Speichern.\n\n"
            "Aufbau: je ein Tab für **Eltern**, für jedes **Profil** und für jedes **Kind**. "
            "In jedem Kinder-Tab kannst du über *Tab bearbeiten -> Sichtbarkeit* festlegen, "
            "welcher Benutzer ihn sieht.\n\n---\n"
        ),
        "dash_template_for": "_Vorlage für {c} Kind(er) und {p} Profil(e):_",
        "diag_title": "MedienStop.de – Diagnose",
        "diag_intro": (
            "Aktueller Zustand von MedienStop. 'TV müsste AUS sein: True' und der "
            "Fernseher läuft trotzdem? Dann schaut bitte ins Protokoll nach "
            "'MedienStop schaltet Fernseher turn_off'."
        ),
        "reset_title": "MedienStop.de – Statistik zurücksetzen",
        "reset_all_label": "ALLE Kinder",
        "reset_arm": (
            "⚠️ Sicherheitsabfrage: Zum Zurücksetzen der Statistik von {name} bitte "
            "innerhalb von {secs} Sekunden ERNEUT auf denselben Knopf drücken."
        ),
        "reset_done": "Statistik von {name} wurde zurückgesetzt.",
    },
    "en": {
        "dash_title": "MedienStop.de – Dashboard template",
        "dash_instructions": (
            "**How to build your dashboard (no tech skills needed):**\n\n"
            "1. Settings -> Dashboards -> *Add dashboard* -> empty dashboard.\n"
            "2. Open the dashboard, top-right pencil (Edit), then the three dots -> "
            "**Raw configuration editor**.\n"
            "3. Select all the text below, copy it, paste it there -> Save.\n\n"
            "Layout: one tab each for **Parents**, every **Profile** and every **Child**. "
            "In each child tab you can set who may see it via *Edit tab -> Visibility*.\n\n---\n"
        ),
        "dash_template_for": "_Template for {c} child(ren) and {p} profile(s):_",
        "diag_title": "MedienStop.de – Diagnostics",
        "diag_intro": (
            "Current state of MedienStop. 'TV müsste AUS sein: True' but the TV is still "
            "running? Then check the log for 'MedienStop schaltet Fernseher turn_off'."
        ),
        "reset_title": "MedienStop.de – Reset statistics",
        "reset_all_label": "ALL children",
        "reset_arm": (
            "⚠️ Safety check: to reset the statistics of {name}, please press the same "
            "button AGAIN within {secs} seconds."
        ),
        "reset_done": "Statistics of {name} have been reset.",
    },
}


class GenerateDashboardButton(MedienStopEntity, ButtonEntity):
    _attr_translation_key = "make_dashboard"
    _attr_icon = "mdi:view-dashboard-edit"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_make_dashboard"
        self._attr_device_info = hub_device(self._entry_id)

    async def async_press(self) -> None:
        m = self.manager
        lang = _lang(self.hass)
        t = _NOTIF[lang]
        # Echte (ggf. umbenannte) Namen einsammeln.
        child_names = {
            cid: device_display_name(self.hass, self._entry_id, cid, m.children[cid]["name"])
            for cid in m.children
        }
        profile_names = {
            pid: device_display_name(self.hass, self._entry_id, pid, m.profiles[pid]["name"])
            for pid in m.profiles
        }
        ids = resolve_entity_ids(self.hass, self._entry_id)
        yaml_str = build_dashboard_yaml(
            m.num_children, m.num_profiles, child_names, profile_names, ids,
            m.tab_users, m.admin_users, lang,
        )
        message = (
            t["dash_instructions"]
            + t["dash_template_for"].format(c=m.num_children, p=m.num_profiles) + "\n\n"
            + "```yaml\n" + yaml_str + "```\n"
        )
        await self.hass.services.async_call(
            "persistent_notification", "create",
            {"title": t["dash_title"], "message": message,
             "notification_id": "medienstop_dashboard"}, blocking=False,
        )


class DiagnoseButton(MedienStopEntity, ButtonEntity):
    """Zeigt als Benachrichtigung, warum der TV (nicht) abschaltet -
    und löst die Abschalt-Prüfung sofort aus."""

    _attr_translation_key = "diagnose"
    _attr_icon = "mdi:stethoscope"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_diagnose"
        self._attr_device_info = hub_device(self._entry_id)

    async def async_press(self) -> None:
        t = _NOTIF[_lang(self.hass)]
        report = self.manager.diagnostics_text()
        # Prüfung sofort auslösen (schaltet den TV ab, falls noetig).
        self.manager._enforce_tv()
        message = t["diag_intro"] + "\n\n```\n" + report + "\n```\n"
        await self.hass.services.async_call(
            "persistent_notification", "create",
            {"title": t["diag_title"], "message": message,
             "notification_id": "medienstop_diagnose"}, blocking=False,
        )


class VideoTestButton(MedienStopEntity, ButtonEntity):
    """Spielt eine Ansage sofort ab (Test) - ohne auf Zeitablauf zu warten.

    Der Knopf fuer "timeup" behaelt aus Bestandsschutz seine alte unique_id
    (`_video_test`), damit bestehende Dashboards/Automatisierungen weiterlaufen.
    """

    _attr_icon = "mdi:movie-open-play"

    def __init__(self, manager, which: str = "timeup") -> None:
        super().__init__(manager)
        self._which = which
        suffix = "video_test" if which == "timeup" else f"video_test_{which}"
        self._attr_translation_key = suffix
        self._attr_unique_id = f"{self._entry_id}_{suffix}"
        self._attr_device_info = hub_device(self._entry_id)

    async def async_press(self) -> None:
        from .const import DOMAIN, SERVICE_TEST_VIDEO
        await self.hass.services.async_call(
            DOMAIN, SERVICE_TEST_VIDEO, {"which": self._which}, blocking=False)


class _ResetConfirmButton(MedienStopEntity, ButtonEntity):
    """Reset-Knopf mit Zwei-Stufen-Sicherheitsabfrage.

    Entity-Buttons haben auf der Geräteseite KEINEN nativen Bestätigungsdialog.
    Lösung: Der 1. Druck 'stellt scharf' und zeigt einen Warnhinweis; erst der
    2. Druck innerhalb von _WINDOW Sekunden setzt die Statistik wirklich zurück.
    So kann man nicht aus Versehen mit einem Klick alles löschen.
    """

    _WINDOW = 15.0  # Sekunden Zeitfenster für die Bestätigung

    def _reset_label(self) -> str:
        """Anzeigename für die Meldung - von der Unterklasse gesetzt."""
        return ""

    def _do_reset(self) -> None:
        """Führt den eigentlichen Reset aus - von der Unterklasse gesetzt."""
        raise NotImplementedError

    async def async_press(self) -> None:
        t = _NOTIF[_lang(self.hass)]
        now = time.monotonic()
        if now < getattr(self, "_armed_until", 0.0):
            # 2. Druck innerhalb des Zeitfensters -> wirklich zurücksetzen.
            self._armed_until = 0.0
            self._do_reset()
            msg = t["reset_done"].format(name=self._reset_label())
        else:
            # 1. Druck -> nur scharfstellen und nachfragen.
            self._armed_until = now + self._WINDOW
            msg = t["reset_arm"].format(name=self._reset_label(), secs=int(self._WINDOW))
        await self.hass.services.async_call(
            "persistent_notification", "create",
            {"title": t["reset_title"], "message": msg,
             "notification_id": f"medienstop_reset_{self._attr_unique_id}"},
            blocking=False,
        )


class ResetStatsAllButton(_ResetConfirmButton):
    """Setzt die Statistik ALLER Kinder zurück - am Hub (mit Sicherheitsabfrage)."""

    _attr_translation_key = "reset_stats_all"
    _attr_icon = "mdi:backup-restore"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_reset_stats_all"
        self._attr_device_info = hub_device(self._entry_id)

    def _reset_label(self) -> str:
        return _NOTIF[_lang(self.hass)]["reset_all_label"]

    def _do_reset(self) -> None:
        self.manager.reset_statistics(None, "all")


class ResetStatsChildButton(_ResetConfirmButton):
    """Setzt die Statistik EINES Kindes zurück - am Kind-Gerät (mit Sicherheitsabfrage)."""

    _attr_translation_key = "reset_stats"
    _attr_icon = "mdi:eye-refresh-outline"

    def __init__(self, manager, cid: str) -> None:
        super().__init__(manager)
        self._cid = cid
        self._attr_unique_id = f"{self._entry_id}_{cid}_reset_stats"
        self._attr_device_info = child_device(
            self._entry_id, cid, manager.children[cid]["name"]
        )

    def _reset_label(self) -> str:
        return device_display_name(
            self.hass, self._entry_id, self._cid, self.manager.children[self._cid]["name"]
        )

    def _do_reset(self) -> None:
        self.manager.reset_statistics(self._cid, "all")
