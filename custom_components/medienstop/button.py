# custom_components/medienstop/button.py
# Knopf am Hub: "Dashboard-Vorlage erstellen".
# Erzeugt aus der eingestellten Anzahl + den echten Gerätenamen ein fertiges
# Dashboard-YAML (ein Tab je Kind/Profil) und zeigt es als kopierbare
# Benachrichtigung. Auch ohne Technikwissen nutzbar.

from __future__ import annotations

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
                VideoTestButton(manager), ResetStatsAllButton(manager)]
    # Pro Kind ein eigener "Statistik zurücksetzen"-Knopf.
    for cid in manager.children:
        entities.append(ResetStatsChildButton(manager, cid))
    async_add_entities(entities)


_INSTRUCTIONS = (
    "**So baust du daraus dein Dashboard (kein Technikwissen noetig):**\n\n"
    "1. Einstellungen -> Dashboards -> *Dashboard hinzufügen* -> leeres Dashboard.\n"
    "2. Dashboard öffnen, oben rechts Stift (Bearbeiten), dann drei Punkte -> "
    "**Raw-Konfigurationseditor**.\n"
    "3. Den Text unten komplett markieren, kopieren, dort einfuegen -> Speichern.\n\n"
    "Aufbau: je ein Tab für **Eltern**, für jedes **Profil** und für jedes **Kind**. "
    "In jedem Kinder-Tab kannst du über *Tab bearbeiten -> Sichtbarkeit* festlegen, "
    "welcher Benutzer ihn sieht.\n\n"
    "---\n"
)


class GenerateDashboardButton(MedienStopEntity, ButtonEntity):
    _attr_translation_key = "make_dashboard"
    _attr_icon = "mdi:view-dashboard-edit"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_make_dashboard"
        self._attr_device_info = hub_device(self._entry_id)

    async def async_press(self) -> None:
        m = self.manager
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
            m.tab_users, m.admin_users,
        )
        message = (
            _INSTRUCTIONS
            + f"_Vorlage für {m.num_children} Kind(er) und {m.num_profiles} Profil(e):_\n\n"
            + "```yaml\n" + yaml_str + "```\n"
        )
        await self.hass.services.async_call(
            "persistent_notification", "create",
            {"title": "MedienStop.de – Dashboard-Vorlage", "message": message,
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
        report = self.manager.diagnostics_text()
        # Prüfung sofort auslösen (schaltet den TV ab, falls noetig).
        self.manager._enforce_tv()
        message = (
            "Aktueller Zustand von MedienStop. 'TV müsste AUS sein: True' und der "
            "Fernseher läuft trotzdem? Dann schaut bitte ins Protokoll nach "
            "'MedienStop schaltet Fernseher turn_off'.\n\n"
            "```\n" + report + "\n```\n"
        )
        await self.hass.services.async_call(
            "persistent_notification", "create",
            {"title": "MedienStop.de – Diagnose", "message": message,
             "notification_id": "medienstop_diagnose"}, blocking=False,
        )


class VideoTestButton(MedienStopEntity, ButtonEntity):
    """Spielt das Abschiedsvideo sofort ab (Test) - ohne auf Zeitablauf zu warten."""

    _attr_translation_key = "video_test"
    _attr_icon = "mdi:movie-open-play"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_video_test"
        self._attr_device_info = hub_device(self._entry_id)

    async def async_press(self) -> None:
        from .const import DOMAIN, SERVICE_TEST_VIDEO
        await self.hass.services.async_call(
            DOMAIN, SERVICE_TEST_VIDEO, {"which": "timeup"}, blocking=False)


class ResetStatsAllButton(MedienStopEntity, ButtonEntity):
    """Setzt die Statistik (geschaute Zeit) ALLER Kinder zurück - am Hub."""

    _attr_translation_key = "reset_stats_all"
    _attr_icon = "mdi:backup-restore"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_reset_stats_all"
        self._attr_device_info = hub_device(self._entry_id)

    async def async_press(self) -> None:
        self.manager.reset_statistics(None, "all")


class ResetStatsChildButton(MedienStopEntity, ButtonEntity):
    """Setzt die Statistik (geschaute Zeit) EINES Kindes zurück - am Kind-Gerät."""

    _attr_translation_key = "reset_stats"
    _attr_icon = "mdi:eye-refresh-outline"

    def __init__(self, manager, cid: str) -> None:
        super().__init__(manager)
        self._cid = cid
        self._attr_unique_id = f"{self._entry_id}_{cid}_reset_stats"
        self._attr_device_info = child_device(
            self._entry_id, cid, manager.children[cid]["name"]
        )

    async def async_press(self) -> None:
        self.manager.reset_statistics(self._cid, "all")
