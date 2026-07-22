# custom_components/medienstop/binary_sensor.py
# Ein Status-Sensor am Hub: ist der (ausgewählte) Fernseher gerade an?
# Spiegelt den Zustand der im Setup gewählten TV-Entity wider und aktualisiert
# sich automatisch, wenn diese sich aendert.

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN
from .entity import MedienStopEntity, hub_device


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TvActiveBinarySensor(manager)])


class TvActiveBinarySensor(MedienStopEntity, BinarySensorEntity):
    """An, wenn der ausgewählte Fernseher läuft."""

    _attr_name = "Fernseher aktiv"
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_icon = "mdi:television"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_tv_active"
        self._attr_device_info = hub_device(self._entry_id)

    @property
    def is_on(self) -> bool:
        # Nutzt die TV-Prüfung des Managers (False, wenn keine TV-Entity gewählt).
        return self.manager._tv_is_on()

    async def async_added_to_hass(self) -> None:
        # Auf Manager-Signale hoeren ...
        self._subscribe_updates()
        # ... UND direkt auf Zustandsänderungen der echten TV-Entity reagieren.
        tv = self.manager.tv_entity_id
        if tv:
            self.async_on_remove(
                async_track_state_change_event(self.hass, [tv], self._tv_changed)
            )

    @callback
    def _tv_changed(self, _event) -> None:
        self.async_write_ha_state()
