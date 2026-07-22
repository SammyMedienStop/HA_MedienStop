# custom_components/medienstop/config_flow.py
# -----------------------------------------------------------------------------
# EINRICHTUNGS-WIZARD von MedienStop.
#   Schritt 1 (user)      : Anzahl Kinder + Profile + Fernseh-Entity (optional)
#   Schritt 2 (names)     : Namen für jedes Kind und jedes Profil
#   Schritt 3 (dashboard) : Variante des Kinder-Dashboards
# Die Namen werden zu den GERAETENAMEN -> daraus ergeben sich auch die
# Entitaets-IDs (z.B. sensor.lukas_restzeit). Später änderbar über
# "Konfigurieren" oder durch Umbenennen der Geräte.
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ADMIN_USERS,
    CONF_KID_DASHBOARD,
    CONF_NAMES,
    CONF_NUM_CHILDREN,
    CONF_NUM_PROFILES,
    CONF_TAB_USERS,
    CONF_TV_ENTITY,
    CONF_VIDEO_PLAYER,
    CONF_VIDEOS,
    DOMAIN,
    KID_DASH_VARIANTS,
    MAX_CHILDREN,
    MAX_PROFILES,
    MIN_CHILDREN,
    MIN_PROFILES,
    child_id,
    child_name,
    profile_id,
    profile_name,
)


def _count(min_v: int, max_v: int) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=min_v, max=max_v, step=1,
                                      mode=selector.NumberSelectorMode.BOX))


def _mediaplayer_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="media_player"))


def _tv_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig())


async def _user_options(hass) -> list[dict]:
    """Echte (nicht system-generierte) Benutzer als Auswahl."""
    users = await hass.auth.async_get_users()
    out = []
    for u in users:
        if getattr(u, "system_generated", False) or not getattr(u, "is_active", True):
            continue
        out.append({"value": u.id, "label": u.name or u.id})
    return out


def _user_selector(options: list[dict], multiple: bool = False) -> selector.SelectSelector:
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=options, multiple=multiple, custom_value=False,
        mode=selector.SelectSelectorMode.DROPDOWN))


def _collect_visibility(user_input: dict, num_children: int) -> tuple[dict, list]:
    tab_users = {}
    for i in range(1, num_children + 1):
        v = user_input.get(f"user_{child_id(i)}")
        if v:
            tab_users[child_id(i)] = v
    admin = user_input.get("admin_users") or []
    return tab_users, admin


def _visibility_schema(num_children: int, options: list[dict], data: dict) -> vol.Schema:
    tab_users = data.get(CONF_TAB_USERS, {})
    fields: dict = {}
    # Eltern zuerst (sehen die Eltern-/Einstellungs-Tabs)
    fields[vol.Optional("admin_users",
                        description={"suggested_value": data.get(CONF_ADMIN_USERS, [])})] = \
        _user_selector(options, multiple=True)
    # dann optional je Kind ein Benutzer (sieht nur seinen Tab)
    for i in range(1, num_children + 1):
        cid = child_id(i)
        key = f"user_{cid}"
        cur = tab_users.get(cid)
        opt = {"suggested_value": cur} if cur else {}
        fields[vol.Optional(key, description=opt)] = _user_selector(options)
    return vol.Schema(fields)


def _dashboard_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(options=list(KID_DASH_VARIANTS),
                                      translation_key="kid_dashboard",
                                      mode=selector.SelectSelectorMode.DROPDOWN))


def _names_schema(num_children: int, num_profiles: int, names: dict) -> vol.Schema:
    """Dynamisches Formular: ein Textfeld je Kind und je Profil."""
    fields: dict = {}
    for i in range(1, num_children + 1):
        cid = child_id(i)
        fields[vol.Optional(f"name_{cid}",
                            default=names.get(cid, child_name(i)))] = selector.TextSelector()
    for p in range(1, num_profiles + 1):
        pid = profile_id(p)
        fields[vol.Optional(f"name_{pid}",
                            default=names.get(pid, profile_name(p)))] = selector.TextSelector()
    return vol.Schema(fields)


def _collect_names(user_input: dict, num_children: int, num_profiles: int) -> dict:
    names: dict = {}
    for i in range(1, num_children + 1):
        cid = child_id(i)
        names[cid] = user_input.get(f"name_{cid}") or child_name(i)
    for p in range(1, num_profiles + 1):
        pid = profile_id(p)
        names[pid] = user_input.get(f"name_{pid}") or profile_name(p)
    return names


_VIDEO_KEYS = [
    ("timeup", "Zeit/Budget abgelaufen (Abschiedsvideo)"),
    ("limit", "Zeitfenster-Ende (z.B. 20/22 Uhr)"),
    ("notimer", "Kein Timer / ausserhalb Zeit"),
]


def _media_selector() -> selector.MediaSelector:
    return selector.MediaSelector(selector.MediaSelectorConfig())


def _delay_selector() -> selector.NumberSelector:
    return selector.NumberSelector(selector.NumberSelectorConfig(
        min=0, max=600, step=1, mode=selector.NumberSelectorMode.BOX,
        unit_of_measurement="s"))


def _videos_schema(videos: dict) -> vol.Schema:
    fields: dict = {}
    for key, label in _VIDEO_KEYS:
        cur = videos.get(key, {}) or {}
        fields[vol.Optional(f"media_{key}")] = _media_selector()
        url_pre = cur.get("id") if cur.get("id") and not str(cur.get("id")).startswith("media-source") else None
        fields[vol.Optional(f"url_{key}", description={"suggested_value": url_pre})] = selector.TextSelector()
        fields[vol.Optional(f"delay_{key}", default=int(cur.get("delay", 10) or 10))] = _delay_selector()
    return vol.Schema(fields)


def _collect_videos(user_input: dict, existing: dict) -> dict:
    out: dict = {}
    for key, _label in _VIDEO_KEYS:
        media = user_input.get(f"media_{key}")
        url = user_input.get(f"url_{key}")
        delay = int(user_input.get(f"delay_{key}", 10) or 10)
        if media:
            out[key] = {"id": media.get("media_content_id"),
                        "type": media.get("media_content_type"), "delay": delay}
        elif url:
            out[key] = {"id": url, "type": None, "delay": delay}
        elif (existing.get(key, {}) or {}).get("id"):
            keep = dict(existing[key]); keep["delay"] = delay; out[key] = keep
    return out


class MedienStopConfigFlow(ConfigFlow, domain=DOMAIN):
    """Mehrstufiger Einrichtungs-Assistent."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._data[CONF_NUM_CHILDREN] = int(user_input[CONF_NUM_CHILDREN])
            self._data[CONF_NUM_PROFILES] = int(user_input[CONF_NUM_PROFILES])
            if user_input.get(CONF_TV_ENTITY):
                self._data[CONF_TV_ENTITY] = user_input[CONF_TV_ENTITY]
            if user_input.get(CONF_VIDEO_PLAYER):
                self._data[CONF_VIDEO_PLAYER] = user_input[CONF_VIDEO_PLAYER]
            return await self.async_step_names()
        schema = vol.Schema({
            vol.Required(CONF_NUM_CHILDREN, default=2): _count(MIN_CHILDREN, MAX_CHILDREN),
            vol.Required(CONF_NUM_PROFILES, default=1): _count(MIN_PROFILES, MAX_PROFILES),
            vol.Optional(CONF_TV_ENTITY): _tv_selector(),
            vol.Optional(CONF_VIDEO_PLAYER): _mediaplayer_selector(),
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_names(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        nc, npf = self._data[CONF_NUM_CHILDREN], self._data[CONF_NUM_PROFILES]
        if user_input is not None:
            self._data[CONF_NAMES] = _collect_names(user_input, nc, npf)
            return await self.async_step_visibility()
        return self.async_show_form(step_id="names", data_schema=_names_schema(nc, npf, {}))

    async def async_step_visibility(self, user_input=None) -> ConfigFlowResult:
        nc = self._data[CONF_NUM_CHILDREN]
        options = await _user_options(self.hass)
        if user_input is not None or not options:
            if user_input is not None:
                tab_users, admin = _collect_visibility(user_input, nc)
                self._data[CONF_TAB_USERS] = tab_users
                self._data[CONF_ADMIN_USERS] = admin
            return await self.async_step_dashboard()
        return self.async_show_form(step_id="visibility",
                                    data_schema=_visibility_schema(nc, options, self._data))

    async def async_step_dashboard(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._data[CONF_KID_DASHBOARD] = user_input[CONF_KID_DASHBOARD]
            return self.async_create_entry(title="MedienStop.de", data=self._data)
        schema = vol.Schema({
            vol.Required(CONF_KID_DASHBOARD, default=KID_DASH_VARIANTS[0]): _dashboard_selector(),
        })
        return self.async_show_form(step_id="dashboard", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MedienStopOptionsFlow(config_entry)


class MedienStopOptionsFlow(OptionsFlow):
    """Nachtraegliches Aendern: Anzahl/TV/Dashboard -> dann Namen."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry
        self._new: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        data = dict(self._entry.data)
        if user_input is not None:
            self._new = {
                CONF_NUM_CHILDREN: int(user_input[CONF_NUM_CHILDREN]),
                CONF_NUM_PROFILES: int(user_input[CONF_NUM_PROFILES]),
                CONF_KID_DASHBOARD: user_input[CONF_KID_DASHBOARD],
            }
            if user_input.get(CONF_TV_ENTITY):
                self._new[CONF_TV_ENTITY] = user_input[CONF_TV_ENTITY]
            if user_input.get(CONF_VIDEO_PLAYER):
                self._new[CONF_VIDEO_PLAYER] = user_input[CONF_VIDEO_PLAYER]
            return await self.async_step_names()
        schema = vol.Schema({
            vol.Required(CONF_NUM_CHILDREN,
                         default=data.get(CONF_NUM_CHILDREN, 2)): _count(MIN_CHILDREN, MAX_CHILDREN),
            vol.Required(CONF_NUM_PROFILES,
                         default=data.get(CONF_NUM_PROFILES, 1)): _count(MIN_PROFILES, MAX_PROFILES),
            vol.Optional(CONF_TV_ENTITY,
                         description={"suggested_value": data.get(CONF_TV_ENTITY)}): _tv_selector(),
            vol.Optional(CONF_VIDEO_PLAYER,
                         description={"suggested_value": data.get(CONF_VIDEO_PLAYER)}): _mediaplayer_selector(),
            vol.Required(CONF_KID_DASHBOARD,
                         default=data.get(CONF_KID_DASHBOARD, KID_DASH_VARIANTS[0])): _dashboard_selector(),
        })
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_names(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        nc, npf = self._new[CONF_NUM_CHILDREN], self._new[CONF_NUM_PROFILES]
        if user_input is not None:
            self._new[CONF_NAMES] = _collect_names(user_input, nc, npf)
            return await self.async_step_visibility()
        old_names = self._entry.data.get(CONF_NAMES, {})
        return self.async_show_form(step_id="names", data_schema=_names_schema(nc, npf, old_names))

    async def async_step_visibility(self, user_input=None) -> ConfigFlowResult:
        nc = self._new[CONF_NUM_CHILDREN]
        options = await _user_options(self.hass)
        if user_input is not None or not options:
            if user_input is not None:
                tab_users, admin = _collect_visibility(user_input, nc)
                self._new[CONF_TAB_USERS] = tab_users
                self._new[CONF_ADMIN_USERS] = admin
            else:
                self._new[CONF_TAB_USERS] = self._entry.data.get(CONF_TAB_USERS, {})
                self._new[CONF_ADMIN_USERS] = self._entry.data.get(CONF_ADMIN_USERS, [])
            return await self.async_step_videos()
        return self.async_show_form(step_id="visibility",
                                    data_schema=_visibility_schema(nc, options, self._entry.data))

    async def async_step_videos(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            self._new[CONF_VIDEOS] = _collect_videos(user_input, self._entry.data.get(CONF_VIDEOS, {}))
            self.hass.config_entries.async_update_entry(self._entry, data=self._new)
            return self.async_create_entry(title="", data={})
        # bestehende Videos uebernehmen, falls dieser Schritt nicht erreicht wird
        self._new.setdefault(CONF_VIDEOS, self._entry.data.get(CONF_VIDEOS, {}))
        return self.async_show_form(step_id="videos",
                                    data_schema=_videos_schema(self._entry.data.get(CONF_VIDEOS, {})))
