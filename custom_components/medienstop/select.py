# custom_components/medienstop/select.py
# Pro Kind (eigenes Gerät): Profil-Zuweisung.
# Die Auswahlmöglichkeiten zeigen die echten Profil-NAMEN (Gerätenamen),
# damit umbenannte Profile auch hier korrekt erscheinen.

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .entity import MedienStopEntity, child_device, device_display_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ProfileSelect(manager, cid) for cid in manager.children])


class ProfileSelect(MedienStopEntity, SelectEntity, RestoreEntity):
    _attr_translation_key = "profile"
    _attr_icon = "mdi:account-cog"

    def __init__(self, manager, cid: str) -> None:
        super().__init__(manager)
        self._cid = cid
        self._attr_unique_id = f"{self._entry_id}_{cid}_profile"
        self._attr_device_info = child_device(
            self._entry_id, cid, manager.children[cid]["name"]
        )

    def _pname(self, pid: str) -> str:
        # Echter (ggf. umbenannter) Profilname, sonst der interne Standardname.
        return device_display_name(
            self.hass, self._entry_id, pid, self.manager.profiles[pid]["name"]
        )

    @property
    def options(self) -> list[str]:
        return [self._pname(pid) for pid in self.manager.profiles]

    @property
    def current_option(self) -> str:
        return self._pname(self.manager.children[self._cid]["profile"])

    async def async_select_option(self, option: str) -> None:
        # Angezeigten Namen -> Profil-ID zurückübersetzen.
        for pid in self.manager.profiles:
            if self._pname(pid) == option:
                self.manager.children[self._cid]["profile"] = pid
                break
        self.manager._notify()

    async def async_added_to_hass(self) -> None:
        await RestoreEntity.async_added_to_hass(self)
        last = await self.async_get_last_state()
        if last is not None and last.state in self.options:
            await self.async_select_option(last.state)
        self._subscribe_updates()
