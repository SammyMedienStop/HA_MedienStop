# custom_components/medienstop/entity.py
# -----------------------------------------------------------------------------
# Gemeinsame Basis (Mixin) + Geräte-Definitionen.
#
# GRUPPIERUNG (gegen das "chaotische" Bild):
#   - 1 Hub-Gerät "MedienStop.de"  -> globale Schalter
#   - pro Kind   ein eigenes Gerät "Kind X"   (untergeordnet dem Hub)
#   - pro Profil ein eigenes Gerät "Profil X" (untergeordnet dem Hub)
#
# NAMEN: Alle Entities nutzen has_entity_name=True und tragen nur den kurzen
# Zusatz (z.B. "Restzeit"). Der volle Name ergibt sich aus dem GERAETENAMEN.
# -> Benennst du das Gerät "Kind 1" in z.B. "Max" um, heissen alle seine
#    Entities automatisch "Max Restzeit", "Max PIN" usw. So gibst du dem Kind
#    einen Namen, ganz ohne Extra-Feld.
# -----------------------------------------------------------------------------

from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, SIGNAL_UPDATE


def hub_device(entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="MedienStop.de",
        manufacturer="Patrick",
        model="Bildschirmzeit-Steuerung",
    )


def child_device(entry_id: str, cid: str, name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_{cid}")},
        name=name,
        manufacturer="Patrick",
        model="Kind",
        via_device=(DOMAIN, entry_id),
    )


def profile_device(entry_id: str, pid: str, name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_{pid}")},
        name=name,
        manufacturer="Patrick",
        model="Profil",
        via_device=(DOMAIN, entry_id),
    )


def device_display_name(hass, entry_id: str, suffix: str, fallback: str) -> str:
    """Liefert den (ggf. vom Nutzer umbenannten) Gerätenamen.

    suffix ist z.B. "kind_1" oder "profil_1". So erscheinen im Dashboard und im
    Profil-Auswahlfeld genau die Namen, die du den Geräten gibst.
    """
    try:
        reg = dr.async_get(hass)
        dev = reg.async_get_device(identifiers={(DOMAIN, f"{entry_id}_{suffix}")})
        if dev:
            return dev.name_by_user or dev.name or fallback
    except Exception:  # pragma: no cover - Registry evtl. noch nicht bereit
        pass
    return fallback


def resolve_entity_ids(hass, entry_id: str) -> dict:
    """Mappt stabile Kennungen (unique_id ohne entry-Prefix) auf echte Entity-IDs.

    So findet das Dashboard die Entities auch dann, wenn HA beim Umbenennen die
    Entity-IDs geändert hat (z.B. sensor.kind_1_restzeit -> sensor.lukas_restzeit).
    """
    out: dict[str, str] = {}
    try:
        reg = er.async_get(hass)
        prefix = f"{entry_id}_"
        for ent in er.async_entries_for_config_entry(reg, entry_id):
            uid = ent.unique_id or ""
            suffix = uid[len(prefix):] if uid.startswith(prefix) else uid
            out[suffix] = ent.entity_id
    except Exception:  # pragma: no cover
        pass
    return out


class MedienStopEntity:
    """Mixin: kurze Namen (has_entity_name) + Aktualisierung per Dispatcher."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager) -> None:
        self.manager = manager
        self._entry_id = manager.entry.entry_id

    def _subscribe_updates(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE.format(entry_id=self._entry_id),
                self.async_write_ha_state,
            )
        )

    async def async_added_to_hass(self) -> None:
        self._subscribe_updates()
