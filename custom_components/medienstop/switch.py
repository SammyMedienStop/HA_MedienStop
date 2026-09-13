# custom_components/medienstop/switch.py
# Globale Schalter (am Hub-Gerät "MedienStop"):
#   - System aktiv   : steuert, ob die Zeitschleife prüft
#   - Ferien heute   : erzwingt den Ferien-Tagtyp
#   - Elternzeit     : Override -> TV bleibt erlaubt (Erwachsene schauen)
#   - Essenspause    : "Jetzt wird gegessen" -> Hart-Aus, nichts startbar
# (Der Fernseher ist KEIN eigener Schalter mehr, sondern eine im Setup
#  ausgewählte Entity, die MedienStop schaltet.)

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .entity import MedienStopEntity, hub_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        MSSwitch(manager, "system_active", "System aktiv", "mdi:power-settings", restore=True),
        MSSwitch(manager, "holiday", "Ferien heute", "mdi:beach", restore=True),
        MSSwitch(manager, "parent_override", "Elternzeit", "mdi:account-supervisor", restore=True),
        MSSwitch(manager, "meal_pause", "Essenspause", "mdi:silverware-fork-knife"),
        MSSwitch(manager, "parent_autooff_enabled", "Elternzeit Auto-Aus", "mdi:timer-off-outline", restore=True),
    ])


class MSSwitch(MedienStopEntity, SwitchEntity, RestoreEntity):
    """Generischer Schalter, der ein bool-Attribut des Managers spiegelt."""

    def __init__(self, manager, key: str, name: str, icon: str, restore: bool = False) -> None:
        super().__init__(manager)
        self._key = key
        self._restore = restore
        self._attr_translation_key = key
        self._attr_icon = icon
        self._attr_unique_id = f"{self._entry_id}_{key}"
        self._attr_device_info = hub_device(self._entry_id)

    async def async_added_to_hass(self) -> None:
        # Persistente Schalter (z.B. Ferien) ihren letzten Zustand wiederherstellen.
        if self._restore:
            await RestoreEntity.async_added_to_hass(self)
            last = await self.async_get_last_state()
            if last is not None and last.state in ("on", "off"):
                setattr(self.manager, self._key, last.state == "on")
        self._subscribe_updates()

    @property
    def is_on(self) -> bool:
        return bool(getattr(self.manager, self._key))

    async def async_turn_on(self, **kwargs) -> None:
        await self._check_user()
        self._apply(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._check_user()
        self._apply(False)

    async def _check_user(self) -> None:
        """Hub-Schalter sind Elternsache: Kind-Benutzer dürfen sie nicht umlegen.

        HA setzt vor jedem Service-Aufruf den Kontext an der Entity
        (`async_set_context`), darin steckt der auslösende Benutzer. Ohne
        diese Prüfung könnte ein Kind z.B. die Elternzeit einschalten und
        damit unbegrenzt fernsehen.
        """
        ctx = getattr(self, "_context", None)
        await self.manager.async_check_user(
            getattr(ctx, "user_id", None), None, f"Schalter '{self.name or self._key}'"
        )

    def _apply(self, value: bool) -> None:
        _LOGGER.warning("MedienStop.de: Schalter '%s' -> %s (manuell)", self._key, value)
        setattr(self.manager, self._key, value)
        # NOT-AUS: "System aktiv" aus -> eine bereits geplante Abschaltung sofort
        # verwerfen (nicht erst beim naechsten Tick in 15/60 Sekunden).
        if self._key == "system_active" and not value:
            self.manager._cancel_off()
        # Sofortige Nebenwirkungen auf den Fernseher:
        if self._key == "parent_autooff_enabled":
            self.manager._schedule_autooff()   # Zeitplan neu setzen
        if self._key == "meal_pause" and value:
            self.manager._set_tv(False)        # Essenspause an -> TV aus
        elif self._key == "parent_override" and value:
            self.manager.pause_all_running()   # Elternzeit an -> laufende Kinder pausieren
            self.manager._set_tv(True)         # ... und TV darf an (Erwachsene)
        self.manager._enforce_tv()
        self.manager._sync_webhooks()
        self.manager._notify()
