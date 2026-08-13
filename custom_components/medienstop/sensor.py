# custom_components/medienstop/sensor.py
# Pro Kind: Restzeit, geschaute Zeit (Heute/Woche/Monat/Jahr), Status.
# Plus am Hub: "Letzte Prüfung" (Heartbeat).

from __future__ import annotations

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import MedienStopEntity, child_device, hub_device


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    entities: list = []
    for cid in manager.children:
        entities.append(RemainingSensor(manager, cid))
        entities.append(WatchedSensor(manager, cid, "watched", "Heute geschaut", "watched"))
        entities.append(WatchedSensor(manager, cid, "watched_week", "Diese Woche", "watched_week"))
        entities.append(WatchedSensor(manager, cid, "watched_month", "Dieser Monat", "watched_month"))
        entities.append(WatchedSensor(manager, cid, "watched_year", "Dieses Jahr", "watched_year"))
        entities.append(StatusSensor(manager, cid))
    # Elternzeit-Statistik am Hub (Heute / Woche / Monat / Jahr)
    for key, name in [
        ("parent_watched", "Elternzeit heute"),
        ("parent_watched_week", "Elternzeit Woche"),
        ("parent_watched_month", "Elternzeit Monat"),
        ("parent_watched_year", "Elternzeit Jahr"),
    ]:
        entities.append(ParentWatchedSensor(manager, key, name))
    entities.append(LastCheckSensor(manager))
    async_add_entities(entities)


class _ChildBase(MedienStopEntity):
    def __init__(self, manager, cid: str) -> None:
        super().__init__(manager)
        self._cid = cid
        self._attr_device_info = child_device(
            self._entry_id, cid, manager.children[cid]["name"]
        )


class RemainingSensor(_ChildBase, RestoreSensor):
    """Verbleibende Minuten - ueberlebt einen Neustart (sonst Reset auf Standard)."""

    _attr_translation_key = "remaining"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-outline"

    def __init__(self, manager, cid: str) -> None:
        super().__init__(manager, cid)
        self._attr_unique_id = f"{self._entry_id}_{cid}_remaining"

    @property
    def native_value(self) -> int:
        return self.manager.children[self._cid]["remaining"]

    async def async_added_to_hass(self) -> None:
        await RestoreSensor.async_added_to_hass(self)
        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            try:
                self.manager.children[self._cid]["remaining"] = int(last.native_value)
                self.manager.children[self._cid]["_remaining_restored"] = True
            except (ValueError, TypeError):
                pass
        self._subscribe_updates()


class WatchedSensor(_ChildBase, RestoreSensor):
    """Geschaute Minuten (Heute/Woche/Monat/Jahr); überlebt Neustart."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:eye-check-outline"

    def __init__(self, manager, cid: str, key: str, name: str, uid: str) -> None:
        super().__init__(manager, cid)
        self._key = key
        self._attr_translation_key = uid
        self._attr_unique_id = f"{self._entry_id}_{cid}_{uid}"

    @property
    def native_value(self) -> int:
        return self.manager.children[self._cid][self._key]

    async def async_added_to_hass(self) -> None:
        await RestoreSensor.async_added_to_hass(self)
        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            try:
                self.manager.children[self._cid][self._key] = int(last.native_value)
            except (ValueError, TypeError):
                pass
        self._subscribe_updates()


class StatusSensor(_ChildBase, SensorEntity):
    _attr_translation_key = "status"
    _attr_icon = "mdi:television-guide"

    def __init__(self, manager, cid: str) -> None:
        super().__init__(manager, cid)
        self._attr_unique_id = f"{self._entry_id}_{cid}_status"

    @property
    def native_value(self) -> str:
        return self.manager.status_text(self._cid)

    @property
    def extra_state_attributes(self) -> dict:
        m = self.manager
        child = m.children[self._cid]
        profile = m._profile_of(self._cid)
        daytype = m.current_daytype()
        start, end = profile["windows"][daytype]
        return {
            "profil": profile["name"],
            "tagtyp": daytype,
            "restzeit": child["remaining"],
            "kann_starten": m.can_start(self._cid),
            "pin_aktiv": bool(child["pin"]),
            "fenster_von": start.strftime("%H:%M"),
            "fenster_bis": end.strftime("%H:%M"),
        }


class ParentWatchedSensor(MedienStopEntity, RestoreSensor):
    """Minuten mit aktiver Elternzeit (Heute/Woche/Monat/Jahr) - am Hub; überlebt Neustart."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:account-supervisor"

    def __init__(self, manager, key: str, name: str) -> None:
        super().__init__(manager)
        self._key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{self._entry_id}_{key}"
        self._attr_device_info = hub_device(self._entry_id)

    @property
    def native_value(self) -> int:
        return int(getattr(self.manager, self._key, 0))

    async def async_added_to_hass(self) -> None:
        await RestoreSensor.async_added_to_hass(self)
        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            try:
                setattr(self.manager, self._key, int(last.native_value))
            except (ValueError, TypeError):
                pass
        self._subscribe_updates()


class LastCheckSensor(MedienStopEntity, SensorEntity):
    """Zeitstempel der letzten Hintergrund-Prüfung (Heartbeat, ~alle 15s)."""

    _attr_translation_key = "last_check"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:heart-pulse"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{self._entry_id}_last_check"
        self._attr_device_info = hub_device(self._entry_id)

    @property
    def native_value(self):
        return self.manager.last_check

    @property
    def extra_state_attributes(self) -> dict:
        # Der Heartbeat tickt auch bei Not-Aus weiter (er ist der Lebensbeweis der
        # Integration) - deshalb hier dazusagen, in welchem Modus geprueft wird.
        aktiv = bool(self.manager.system_active)
        return {
            "system_aktiv": aktiv,
            "modus": "aktiv" if aktiv else "NOT-AUS - kein Eingriff in den Fernseher, keine Statistik",
        }
