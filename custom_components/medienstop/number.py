# custom_components/medienstop/number.py
# Pro Profil (eigenes Gerät): 3 Budget-Regler (Werktag/Wochenende/Ferien).

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DAY_TYPES, DOMAIN, MAX_BUDGET
from .entity import MedienStopEntity, profile_device

_LABELS = {"werktag": "Werktag", "wochenende": "Wochenende", "ferien": "Ferien"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    entities: list = []
    for pid in manager.profiles:
        for daytype in DAY_TYPES:
            entities.append(BudgetNumber(manager, pid, daytype))
    async_add_entities(entities)


class BudgetNumber(MedienStopEntity, RestoreNumber):
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_BUDGET
    _attr_native_step = 5
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-cog-outline"

    def __init__(self, manager, pid: str, daytype: str) -> None:
        super().__init__(manager)
        self._pid = pid
        self._daytype = daytype
        self._attr_translation_key = f"budget_{daytype}"
        self._attr_unique_id = f"{self._entry_id}_{pid}_budget_{daytype}"
        self._attr_device_info = profile_device(
            self._entry_id, pid, manager.profiles[pid]["name"]
        )

    @property
    def native_value(self) -> int:
        return self.manager.profiles[self._pid]["budgets"][self._daytype]

    async def async_set_native_value(self, value: float) -> None:
        self.manager.profiles[self._pid]["budgets"][self._daytype] = int(value)
        self.manager._notify()

    async def async_added_to_hass(self) -> None:
        await RestoreNumber.async_added_to_hass(self)
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self.manager.profiles[self._pid]["budgets"][self._daytype] = int(last.native_value)
        self._subscribe_updates()

