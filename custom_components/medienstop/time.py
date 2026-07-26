# custom_components/medienstop/time.py
# Pro Profil (eigenes Gerät) je Tagtyp: Fenster-Start und Fenster-Ende.

from __future__ import annotations

import datetime

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DAY_TYPES, DOMAIN
from .entity import MedienStopEntity, hub_device, profile_device

_LABELS = {"werktag": "Werktag", "wochenende": "Wochenende", "ferien": "Ferien"}
_BOUNDS = {0: ("Start", "mdi:clock-start"), 1: ("Ende", "mdi:clock-end")}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    entities: list = []
    for pid in manager.profiles:
        for daytype in DAY_TYPES:
            entities.append(WindowTime(manager, pid, daytype, 0))
            entities.append(WindowTime(manager, pid, daytype, 1))
    entities.append(AutoOffTime(manager))
    async_add_entities(entities)


class WindowTime(MedienStopEntity, TimeEntity, RestoreEntity):
    def __init__(self, manager, pid: str, daytype: str, bound: int) -> None:
        super().__init__(manager)
        self._pid = pid
        self._daytype = daytype
        self._bound = bound
        label, icon = _BOUNDS[bound]
        self._attr_icon = icon
        self._attr_translation_key = f"{daytype}_{label.lower()}"
        self._attr_unique_id = f"{self._entry_id}_{pid}_{daytype}_{label.lower()}"
        self._attr_device_info = profile_device(
            self._entry_id, pid, manager.profiles[pid]["name"]
        )

    @property
    def native_value(self) -> datetime.time:
        return self.manager.profiles[self._pid]["windows"][self._daytype][self._bound]

    async def async_set_value(self, value: datetime.time) -> None:
        self.manager.profiles[self._pid]["windows"][self._daytype][self._bound] = value
        self.manager._notify()

    async def async_added_to_hass(self) -> None:
        await RestoreEntity.async_added_to_hass(self)
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            try:
                self.manager.profiles[self._pid]["windows"][self._daytype][self._bound] = \
                    datetime.time.fromisoformat(last.state)
            except (ValueError, TypeError):
                pass
        self._subscribe_updates()


class AutoOffTime(MedienStopEntity, TimeEntity, RestoreEntity):
    """Uhrzeit, zu der die Elternzeit automatisch abgeschaltet wird."""

    _attr_translation_key = "parent_autooff_time"
    _attr_icon = "mdi:timer-off-outline"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_parent_autooff_time"
        self._attr_device_info = hub_device(self._entry_id)

    @property
    def native_value(self) -> datetime.time:
        return self.manager.parent_autooff_time

    async def async_set_value(self, value: datetime.time) -> None:
        self.manager.set_autooff_time(value)

    async def async_added_to_hass(self) -> None:
        await RestoreEntity.async_added_to_hass(self)
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            try:
                self.manager.parent_autooff_time = datetime.time.fromisoformat(last.state)
                self.manager._schedule_autooff()
            except (ValueError, TypeError):
                pass
        self._subscribe_updates()
