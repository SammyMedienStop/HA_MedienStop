# custom_components/medienstop/text.py
# Pro Kind: PIN + zwei Webhook-URLs (aktiv/inaktiv).
# Am Hub: zwei Webhook-URLs für den Elternmodus (aktiv/inaktiv).
# Die URLs werden bei Start/Stop bzw. Elternmodus-Wechsel per HTTP GET aufgerufen.

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .entity import MedienStopEntity, child_device, hub_device


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    entities: list = []
    for cid in manager.children:
        entities.append(PinText(manager, cid))
        entities.append(ChildUrlText(manager, cid, "url_active", "Hook aktiv"))
        entities.append(ChildUrlText(manager, cid, "url_inactive", "Hook inaktiv"))
    entities.append(ParentUrlText(manager, "parent_url_active", "Elternmodus Hook aktiv"))
    entities.append(ParentUrlText(manager, "parent_url_inactive", "Elternmodus Hook inaktiv"))
    async_add_entities(entities)


class PinText(MedienStopEntity, TextEntity, RestoreEntity):
    _attr_name = "PIN"
    _attr_icon = "mdi:form-textbox-password"
    _attr_native_min = 0
    _attr_native_max = 12
    _attr_mode = TextMode.PASSWORD
    _attr_pattern = r"[0-9]*"

    def __init__(self, manager, cid: str) -> None:
        super().__init__(manager)
        self._cid = cid
        self._attr_unique_id = f"{self._entry_id}_{cid}_pin"
        self._attr_device_info = child_device(self._entry_id, cid, manager.children[cid]["name"])

    @property
    def native_value(self) -> str:
        return self.manager.children[self._cid]["pin"]

    async def async_set_value(self, value: str) -> None:
        self.manager.set_pin(self._cid, value)

    async def async_added_to_hass(self) -> None:
        await RestoreEntity.async_added_to_hass(self)
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            self.manager.children[self._cid]["pin"] = last.state
        self._subscribe_updates()


class _UrlBase(MedienStopEntity, TextEntity, RestoreEntity):
    """Gemeinsame Basis für URL-Eingabefelder."""

    _attr_icon = "mdi:webhook"
    _attr_native_max = 255
    _attr_mode = TextMode.TEXT

    def _read(self) -> str:
        raise NotImplementedError

    def _write(self, value: str) -> None:
        raise NotImplementedError

    @property
    def native_value(self) -> str:
        return self._read()

    async def async_set_value(self, value: str) -> None:
        self._write(value or "")
        self.manager._notify()

    async def async_added_to_hass(self) -> None:
        await RestoreEntity.async_added_to_hass(self)
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            self._write(last.state)
        self._subscribe_updates()


class ChildUrlText(_UrlBase):
    def __init__(self, manager, cid: str, key: str, name: str) -> None:
        super().__init__(manager)
        self._cid = cid
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{self._entry_id}_{cid}_{key}"
        self._attr_device_info = child_device(self._entry_id, cid, manager.children[cid]["name"])

    def _read(self) -> str:
        return self.manager.children[self._cid][self._key]

    def _write(self, value: str) -> None:
        self.manager.children[self._cid][self._key] = value


class ParentUrlText(_UrlBase):
    def __init__(self, manager, attr: str, name: str) -> None:
        super().__init__(manager)
        self._attr = attr
        self._attr_name = name
        self._attr_unique_id = f"{self._entry_id}_{attr}"
        self._attr_device_info = hub_device(self._entry_id)

    def _read(self) -> str:
        return getattr(self.manager, self._attr)

    def _write(self, value: str) -> None:
        setattr(self.manager, self._attr, value)
