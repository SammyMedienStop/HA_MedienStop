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
    ALEXA_SOUNDS,
    ANNOUNCE_KEYS,
    ANNOUNCE_SOURCES,
    DEFAULT_BUNDLED,
    DEFAULT_DELAY,
    MAX_DELAY,
    SRC_MEDIA,
    SRC_NONE,
    SRC_SOUND,
    SRC_TTS,
    SRC_URL,
    SRC_WWW,
    as_int,
    normalize_announce,
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


def _media_selector() -> selector.MediaSelector:
    return selector.MediaSelector(selector.MediaSelectorConfig())


def _delay_selector() -> selector.NumberSelector:
    return selector.NumberSelector(selector.NumberSelectorConfig(
        min=0, max=MAX_DELAY, step=1, mode=selector.NumberSelectorMode.BOX,
        unit_of_measurement="s"))


def _source_selector() -> selector.SelectSelector:
    """Ein einziges Auswahlfeld mit allen Quellen - inklusive der sechs
    mitgelieferten Vorlagen, die der Nutzer ohne jede Einrichtung nutzen kann."""
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=list(ANNOUNCE_SOURCES), translation_key="announce_source",
        mode=selector.SelectSelectorMode.DROPDOWN))


def _www_selector(files: list[str]) -> selector.SelectSelector:
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=files, custom_value=True, mode=selector.SelectSelectorMode.DROPDOWN))


def _sound_selector() -> selector.SelectSelector:
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=list(ALEXA_SOUNDS), custom_value=True,
        mode=selector.SelectSelectorMode.DROPDOWN))


def _announce_schema(key: str, cfg: dict, www_files: list[str]) -> vol.Schema:
    """Formular fuer EINE Ansage. Alle Felder sind sichtbar; ausgewertet wird nur,
    was zur gewaehlten Quelle passt (Home Assistant kann Felder nicht dynamisch
    ein-/ausblenden)."""
    src = cfg.get("src") or DEFAULT_BUNDLED.get(key, SRC_NONE)
    cur_url = cfg.get("id", "") if cfg.get("src") == SRC_URL else ""
    return vol.Schema({
        vol.Required("src", default=src): _source_selector(),
        vol.Optional("media"): _media_selector(),
        vol.Optional("www_file",
                     description={"suggested_value": cfg.get("file")}): _www_selector(www_files),
        vol.Optional("url",
                     description={"suggested_value": cur_url or None}): selector.TextSelector(),
        vol.Optional("tts",
                     description={"suggested_value": cfg.get("tts")}): selector.TextSelector(),
        vol.Optional("sound",
                     description={"suggested_value": cfg.get("sound")}): _sound_selector(),
        vol.Optional("delay", default=as_int(cfg.get("delay"), DEFAULT_DELAY)): _delay_selector(),
        vol.Optional("test", default=False): selector.BooleanSelector(),
    })


def _collect_announce(user_input: dict, cur: dict) -> dict:
    """Baut aus den Formularwerten genau EINEN Ansage-Eintrag.

    Die gewaehlte Quelle bestimmt den Wert - es gibt keinen Rueckfall mehr auf
    einen alten Eintrag (frueher liess sich ein einmal gesetztes Video dadurch
    nie wieder loeschen). Zum Entfernen einfach "Keine Ansage" waehlen.
    """
    src = user_input.get("src") or SRC_NONE
    out: dict = {"src": src, "delay": as_int(user_input.get("delay"), DEFAULT_DELAY)}

    if src == SRC_MEDIA:
        media = user_input.get("media") or {}
        if media.get("media_content_id"):
            out["id"] = media["media_content_id"]
            out["type"] = media.get("media_content_type")
        elif cur.get("src") == SRC_MEDIA and cur.get("id"):
            # Der Media-Browser startet technisch bedingt immer leer -> ein leeres
            # Feld bedeutet "bisherige Datei behalten", nicht "loeschen".
            out["id"] = cur["id"]
            out["type"] = cur.get("type")
    elif src == SRC_WWW:
        out["file"] = (user_input.get("www_file") or "").strip()
    elif src == SRC_URL:
        out["id"] = (user_input.get("url") or "").strip()
    elif src == SRC_TTS:
        out["tts"] = (user_input.get("tts") or "").strip()
    elif src == SRC_SOUND:
        out["sound"] = (user_input.get("sound") or "").strip()
    return out


def _www_mp3_files(hass) -> list[str]:
    """Listet Audiodateien in <config>/www/ (fuer die Auswahl eigener Ansagen)."""
    import os
    try:
        root = hass.config.path("www")
        found = []
        for dirpath, _dirs, files in os.walk(root):
            rel = os.path.relpath(dirpath, root)
            for name in files:
                if name.lower().endswith((".mp3", ".mp4", ".wav", ".m4a")):
                    found.append(name if rel == "." else f"{rel}/{name}".replace("\\", "/"))
        return sorted(found)[:100]
    except Exception:  # pragma: no cover - Ordner fehlt o.ae.
        return []


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
    """Menuegesteuerte Einstellungen: jeder Bereich ist einzeln aenderbar und
    speichert fuer sich (frueher ein starrer Durchlauf mit Speichern am Ende)."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    # --- Menue ---------------------------------------------------------------
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Startseite: der Nutzer waehlt gezielt EINEN Bereich.

        Frueher war das ein starrer Durchlauf (Anzahl -> Namen -> Sichtbarkeit ->
        Videos) und gespeichert wurde erst ganz am Ende. Fuer eine kleine Aenderung
        an einer Ansage musste man vier Formulare durchklicken.
        """
        return self.async_show_menu(step_id="init", menu_options=[
            "basis", "names", "visibility",
            "ansage_timeup", "ansage_limit", "ansage_notimer",
        ])

    def _save(self, changes: dict[str, Any]) -> ConfigFlowResult:
        """Uebernimmt NUR die geaenderten Schluessel (Merge statt Vollersetzung)."""
        data = {**self._entry.data, **changes}
        self.hass.config_entries.async_update_entry(self._entry, data=data)
        # Options unveraendert lassen -> kein zweiter Reload.
        return self.async_create_entry(title="", data=dict(self._entry.options))

    # --- Basis-Einstellungen -------------------------------------------------
    async def async_step_basis(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        data = dict(self._entry.data)
        if user_input is not None:
            return self._save({
                CONF_NUM_CHILDREN: int(user_input[CONF_NUM_CHILDREN]),
                CONF_NUM_PROFILES: int(user_input[CONF_NUM_PROFILES]),
                CONF_KID_DASHBOARD: user_input[CONF_KID_DASHBOARD],
                # Leeres Feld = Auswahl entfernen (frueher liess sie sich nicht loeschen).
                CONF_TV_ENTITY: user_input.get(CONF_TV_ENTITY) or "",
                CONF_VIDEO_PLAYER: user_input.get(CONF_VIDEO_PLAYER) or "",
            })
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
        return self.async_show_form(step_id="basis", data_schema=schema)

    # --- Namen ---------------------------------------------------------------
    async def async_step_names(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        data = self._entry.data
        nc = int(data.get(CONF_NUM_CHILDREN, 2))
        npf = int(data.get(CONF_NUM_PROFILES, 1))
        old = data.get(CONF_NAMES, {})
        if user_input is not None:
            # Mergen: Namen von Kindern/Profilen, die aktuell nicht angezeigt werden
            # (weil die Anzahl kleiner ist), bleiben erhalten und kommen zurueck,
            # wenn die Anzahl wieder erhoeht wird.
            return self._save({CONF_NAMES: {**old, **_collect_names(user_input, nc, npf)}})
        return self.async_show_form(step_id="names", data_schema=_names_schema(nc, npf, old))

    # --- Sichtbarkeit --------------------------------------------------------
    async def async_step_visibility(self, user_input=None) -> ConfigFlowResult:
        data = self._entry.data
        nc = int(data.get(CONF_NUM_CHILDREN, 2))
        options = await _user_options(self.hass)
        if not options:
            return self.async_abort(reason="keine_benutzer")
        if user_input is not None:
            tab_users, admin = _collect_visibility(user_input, nc)
            return self._save({
                CONF_TAB_USERS: {**data.get(CONF_TAB_USERS, {}), **tab_users},
                CONF_ADMIN_USERS: admin,
            })
        return self.async_show_form(step_id="visibility",
                                    data_schema=_visibility_schema(nc, options, data))

    # --- Ansagen (je Grund einzeln) -----------------------------------------
    async def async_step_ansage_timeup(self, user_input=None) -> ConfigFlowResult:
        return await self._ansage("timeup", user_input)

    async def async_step_ansage_limit(self, user_input=None) -> ConfigFlowResult:
        return await self._ansage("limit", user_input)

    async def async_step_ansage_notimer(self, user_input=None) -> ConfigFlowResult:
        return await self._ansage("notimer", user_input)

    async def _ansage(self, key: str, user_input) -> ConfigFlowResult:
        """Eine einzelne Ansage bearbeiten - mit Probe-Abspielen VOR dem Speichern."""
        videos = dict(self._entry.data.get(CONF_VIDEOS, {}))
        cur = normalize_announce(videos.get(key))
        www_files = await self.hass.async_add_executor_job(_www_mp3_files, self.hass)
        step_id = f"ansage_{key}"

        if user_input is not None:
            cfg = _collect_announce(user_input, cur)
            if user_input.get("test"):
                # NICHT speichern: die eingegebenen Werte nur einmal abspielen und
                # das Formular mit denselben Eingaben erneut anzeigen.
                mgr = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
                if mgr is None:
                    ok, meldung = False, "Die Integration ist gerade nicht geladen."
                else:
                    ok, meldung = mgr.announce(key, cfg)
                schema = _announce_schema(key, cfg, www_files)
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=self.add_suggested_values_to_schema(schema, user_input),
                    errors=None if ok else {"base": "test_fehlgeschlagen"},
                    description_placeholders={"ergebnis": meldung},
                )
            videos[key] = cfg
            return self._save({CONF_VIDEOS: videos})

        return self.async_show_form(
            step_id=step_id,
            data_schema=_announce_schema(key, cur, www_files),
            description_placeholders={"ergebnis": ""},
        )
