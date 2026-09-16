# custom_components/medienstop/__init__.py
# -----------------------------------------------------------------------------
# EINSTIEGSPUNKT + KERNLOGIK von MedienStop.
#
# Neu in dieser Version:
#   - TV: schaltet eine im Setup AUSGEWAEHLTE Entity (kein virtueller Schalter).
#   - Essenspause: globaler Hart-Aus-Schalter ("Jetzt wird gegessen"). Solange an,
#     ist alles aus und nicht startbar - erst wieder frei, wenn der Schalter aus ist.
#   - add_time: kann EINEM Kind oder ALLEN Kindern gleichzeitig Zeit geben.
# -----------------------------------------------------------------------------

from __future__ import annotations

import datetime
import logging

import aiohttp

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .dashboard import build_dashboard_yaml
from .texts import t as _text
from .const import (
    ANNOUNCE_KEYS,
    BUNDLED_MEDIA,
    SRC_AUTO,
    SRC_NONE,
    SRC_SOUND,
    SRC_TTS,
    SRC_WWW,
    announce_media,
    as_int,
    bundled_for,
    normalize_announce,
    ATTR_CHILD,
    CONF_NAMES,
    ATTR_MINUTES,
    ATTR_SCOPE,
    ATTR_PIN,
    CONF_NUM_CHILDREN,
    CONF_ADMIN_USERS,
    CONF_NUM_PROFILES,
    CONF_PARENT_KID_TAB,
    CONF_VIDEOS,
    CONF_TAB_USERS,
    CONF_TV_ENTITY,
    CONF_VIDEO_PLAYER,
    DAY_FERIEN,
    DAY_WERKTAG,
    DAY_WOCHENENDE,
    DEFAULT_BUDGETS,
    DEFAULT_WINDOWS,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_TIME,
    SERVICE_APPLY_BUDGETS,
    SERVICE_CREATE_DASHBOARD,
    SERVICE_PLAY_MEDIA,
    SERVICE_TEST_VIDEO,
    SERVICE_RESET_STATS,
    SERVICE_PAUSE,
    SERVICE_SET_PIN,
    SERVICE_START,
    SERVICE_STOP,
    SIGNAL_UPDATE,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RUNNING,
    child_id,
    child_name,
    profile_id,
    profile_name,
)

_LOGGER = logging.getLogger(__name__)
_SERVICES_REGISTERED = "_services_registered"

# Zustaende, die als "Fernseher AUS" gelten. Alles andere (on, playing, paused,
# ...) gilt als AN. Damit funktioniert auch ein media_player als TV-Entity.
_TV_OFF_STATES = {"off", "unavailable", "unknown", "none", "standby", "idle", ""}
# Nur DIESE Zustaende gelten als "Fernseher wurde wirklich ausgeschaltet".
# (idle/unavailable/unknown sind nur kurze Aussetzer und duerfen den Elternmodus
#  NICHT beenden.)
_TV_HARD_OFF_STATES = {"off", "standby"}


def _t(h: int, m: int) -> datetime.time:
    return datetime.time(hour=h, minute=m)


class MedienStopManager:
    """Haelt den kompletten Laufzeit-Zustand einer MedienStop-Konfiguration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self.num_children: int = int(entry.data.get(CONF_NUM_CHILDREN, 1))
        self.num_profiles: int = int(entry.data.get(CONF_NUM_PROFILES, 1))
        # Ausgewählte Fernseh-Entity (z.B. switch.wohnzimmer_tv). Leer = keine.
        self.tv_entity_id: str | None = entry.data.get(CONF_TV_ENTITY) or None
        # Eigener Player zum Streamen (Cast); faellt auf die TV-Entity zurueck.
        self.video_player_id: str | None = entry.data.get(CONF_VIDEO_PLAYER) or None
        self.tab_users: dict = entry.data.get(CONF_TAB_USERS, {})
        self.admin_users: list = entry.data.get(CONF_ADMIN_USERS, [])

        # --- globale Schalterzustaende --------------------------------------
        self.system_active: bool = True    # Gesamtsystem aktiv? (Loop läuft nur dann)
        self.holiday: bool = False         # "Heute ist Ferienzeit"
        self.parent_override: bool = False # Elternzeit: TV trotz allem erlaubt
        # Elternzeit-Statistik: Minuten, in denen Elternzeit aktiv war UND der TV lief.
        self.parent_watched = 0        # heute
        self.parent_watched_week = 0   # diese Woche
        self.parent_watched_month = 0  # dieser Monat
        self.parent_watched_year = 0   # dieses Jahr
        self.meal_pause: bool = False      # "Jetzt wird gegessen": Hart-Aus
        self.last_check = None             # Zeitstempel der letzten Hintergrund-Prüfung
        # Elternzeit-Auto-Aus: schaltet die Elternzeit täglich zur Uhrzeit ab.
        self.parent_autooff_enabled: bool = True
        self.parent_autooff_time: datetime.time = datetime.time(22, 0)
        # Webhook-URLs (Aktiv/Inaktiv) für spätere Automatisierungen
        self.parent_url_active: str = ""
        self.parent_url_inactive: str = ""
        self._parent_was_active = False
        # Beim ersten _sync_webhooks()-Lauf werden die Flanken-Merker nur
        # abgeglichen, nicht gefeuert (siehe _sync_webhooks).
        self._webhooks_primed = False
        # Ansagen vor dem Ausschalten (im Options-Flow je Grund einzeln einstellbar).
        # normalize_announce versteht auch die alte Form aus <= 2.4.x weiter.
        _vids = entry.data.get(CONF_VIDEOS, {})
        self.media_cfg: dict[str, dict] = {
            key: normalize_announce(_vids.get(key)) for key in ANNOUNCE_KEYS
        }

        # Flache Attribute bleiben aus Bestandsschutz erhalten (Diagnose, Service,
        # evtl. eigene Templates von Nutzern). Sie werden aus media_cfg abgeleitet.
        def _flat(key):
            cfg = self.media_cfg[key]
            url, ctype = announce_media(cfg)
            return url, ctype, cfg["delay"], (cfg.get("tts") or "")

        self.video_timeup, self.video_timeup_type, self.delay_timeup, self.tts_timeup = _flat("timeup")
        self.video_limit, self.video_limit_type, self.delay_limit, self.tts_limit = _flat("limit")
        self.video_notimer, self.video_notimer_type, self.delay_notimer, self.tts_notimer = _flat("notimer")
        self._off_pending = False
        self._unsub_off = None

        # --- Profile ---------------------------------------------------------
        names = entry.data.get(CONF_NAMES, {})
        self.profiles: dict[str, dict] = {}
        for i in range(1, self.num_profiles + 1):
            pid = profile_id(i)
            self.profiles[pid] = {
                "name": names.get(pid) or profile_name(i),
                "budgets": dict(DEFAULT_BUDGETS),
                "windows": {dt: [_t(*w[0]), _t(*w[1])] for dt, w in DEFAULT_WINDOWS.items()},
            }

        # --- Kinder ----------------------------------------------------------
        self.children: dict[str, dict] = {}
        first_pid = profile_id(1)
        for i in range(1, self.num_children + 1):
            cid = child_id(i)
            self.children[cid] = {
                "name": names.get(cid) or child_name(i),
                "profile": first_pid,
                "pin": "",
                "remaining": 0,
                "state": STATE_IDLE,
                "watched": 0,         # heute geschaute Minuten
                "watched_week": 0,    # diese Woche
                "watched_month": 0,   # dieser Monat
                "watched_year": 0,    # dieses Jahr
                "url_active": "",     # Webhook bei Start (aktiv)
                "url_inactive": "",   # Webhook bei Stop/Pause (inaktiv)
                "_was_active": False, # interner Merker für Flankenwechsel
            }

        self._unsub_loop = None
        self._unsub_midnight = None
        self._unsub_autooff = None
        self._unsub_enforce = None
        self._unsub_tvstate = None
        self.last_reset = dt_util.now().date()
        # WICHTIG: apply_budgets_now() NICHT hier aufrufen - zu diesem Zeitpunkt sind
        # die gespeicherten Budgets/Restzeiten noch nicht wiederhergestellt. Das
        # Anwenden passiert in async_setup_entry NACH dem Restore (nur fuer Kinder
        # ohne wiederhergestellte Restzeit).

    # ========================================================================
    # ABLEITUNGEN / HELFER
    # ========================================================================
    def current_daytype(self) -> str:
        if self.holiday:
            return DAY_FERIEN
        # "Schulnacht"-Logik: Wochenende = Freitag + Samstag (am nächsten Morgen
        # muss niemand frueh raus). Sonntag zählt schon als Werktag, weil Montag
        # wieder Schule/Arbeit ist.  weekday(): Mo=0 .. Fr=4, Sa=5, So=6
        return DAY_WOCHENENDE if dt_util.now().weekday() in (4, 5) else DAY_WERKTAG

    def _profile_of(self, cid: str) -> dict:
        pid = self.children[cid]["profile"]
        return self.profiles.get(pid) or next(iter(self.profiles.values()))

    def child_budget(self, cid: str, daytype: str | None = None) -> int:
        daytype = daytype or self.current_daytype()
        return int(self._profile_of(cid)["budgets"].get(daytype, 0))

    def within_window(self, cid: str, daytype: str | None = None) -> bool:
        daytype = daytype or self.current_daytype()
        start, end = self._profile_of(cid)["windows"][daytype]
        if start == end:
            return True
        return start <= dt_util.now().time() <= end

    def status_text(self, cid: str) -> str:
        from .const import (
            STATUS_BLOCKED, STATUS_BUSY, STATUS_IDLE, STATUS_PAUSED,
            STATUS_READY, STATUS_RUNNING,
        )
        child = self.children[cid]
        if self.meal_pause:
            return STATUS_BLOCKED  # während Essenspause alles gesperrt
        if child["remaining"] <= 0:
            return STATUS_IDLE
        if child["state"] == STATE_RUNNING:
            return STATUS_RUNNING if self.within_window(cid) else STATUS_BLOCKED
        # TV ist von einem ANDEREN Kind oder von der Elternzeit belegt -> dieses
        # Kind kann jetzt NICHT schauen (auch nicht fortsetzen), daher "belegt".
        # Dadurch blendet das Kind-Dashboard den Play-/Fortsetzen-Knopf aus, solange
        # ein anderes Kind läuft (nur EIN Kind gleichzeitig am gemeinsamen Fernseher).
        if self.parent_override or self.another_active(cid):
            return STATUS_BUSY
        if child["state"] == STATE_PAUSED:
            return STATUS_PAUSED
        return STATUS_READY

    def another_active(self, cid: str) -> bool:
        """Laeuft GERADE der Timer eines ANDEREN Kindes?"""
        return any(
            c != cid and ch["state"] == STATE_RUNNING
            for c, ch in self.children.items()
        )

    def pause_all_running(self) -> None:
        """Pausiert alle aktuell laufenden Kind-Timer (z.B. bei Elternzeit)."""
        changed = False
        for ch in self.children.values():
            if ch["state"] == STATE_RUNNING:
                ch["state"] = STATE_PAUSED
                changed = True
        if changed:
            self._sync_webhooks()
            self._notify()

    def can_start(self, cid: str) -> bool:
        child = self.children[cid]
        return (
            self.system_active
            and not self.meal_pause
            and not self.parent_override          # Elternzeit blockt Kinderstart
            and not self.another_active(cid)      # nur EIN Kind gleichzeitig
            and child["remaining"] > 0
            and child["state"] != STATE_RUNNING
            and self.within_window(cid)
        )

    # ========================================================================
    # BERECHTIGUNG: Wer darf was bedienen?
    # ========================================================================
    def child_ids_for_user(self, user_id: str | None) -> list[str]:
        """Kinder, denen dieser HA-Benutzer unter "Sichtbarkeit" zugeordnet ist."""
        if not user_id:
            return []
        return [cid for cid, uid in self.tab_users.items() if uid == user_id]

    async def async_check_user(self, user_id: str | None, cid: str | None = None,
                               action: str = "") -> None:
        """Sperrt Kind-Benutzer für alles, was nicht ihr eigener Timer ist.

        Hintergrund: Die Tab-Sichtbarkeit im Dashboard ist nur Kosmetik - ein
        Kind kann einen versteckten Tab per Adresse aufrufen oder eine Entity
        über die Suche finden und so den Elternmodus einschalten oder den
        Timer eines Geschwisterkinds stoppen. Deshalb wird hier serverseitig
        geprüft, wer den Aufruf ausgelöst hat.

        Regeln:
        * Kein Benutzer im Kontext (Automation, Skript, Zeitplan) -> erlaubt.
        * HA-Administratoren und die unter "Sichtbarkeit" gewählten Eltern
          -> erlaubt.
        * Ein Benutzer, der dort einem Kind zugeordnet ist, darf NUR den Timer
          dieses Kindes bedienen (`cid`). Elternzeit, andere Kinder, Zeit
          gutschreiben usw. sind für ihn gesperrt.
        * Benutzer ohne jede Zuordnung bleiben wie bisher unbeschränkt.
        """
        if not user_id or user_id in self.admin_users:
            return
        own = self.child_ids_for_user(user_id)
        if not own:
            return
        if cid is not None and cid in own:
            return
        try:
            user = await self.hass.auth.async_get_user(user_id)
        except Exception:  # pragma: no cover - Auth nicht erreichbar
            user = None
        if user is not None and getattr(user, "is_admin", False):
            return
        wer = user.name if (user is not None and getattr(user, "name", None)) else user_id
        # `action` ist ein Schlüssel aus texts.py (act_*) oder schon fertiger Text.
        was = self.t(action) if action.startswith("act_") else (action or self.t("act_default"))
        if cid is not None and cid in self.children:
            was = self.t("act_for", action=was, name=self.children[cid]["name"])
        _LOGGER.warning("MedienStop.de: '%s' durch Kind-Benutzer %s (%s) abgelehnt",
                        was, wer, own)
        raise HomeAssistantError(self.t("err_not_allowed", who=wer, what=was))

    def t(self, key: str, **kw) -> str:
        """Laufzeittext in der HA-Sprache (siehe texts.py)."""
        return _text(self.hass, key, **kw)

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(entry_id=self.entry.entry_id))

    def _diag_log(self, tag: str) -> None:
        """Schreibt einen kompletten Zustands-Schnappschuss ins Protokoll (Diagnose)."""
        st = self.hass.states.get(self.tv_entity_id) if self.tv_entity_id else None
        kids = "; ".join(
            f"{c['name']}={c['state']}/{c['remaining']}min/fenster={self.within_window(cid)}"
            for cid, c in self.children.items()
        )
        _LOGGER.warning(
            "MedienStop.de [%s] system=%s elternmodus=%s essenspause=%s ferien=%s "
            "tv_entity=%s(zustand=%s an=%s) video_player=%s off_pending=%s | %s",
            tag, self.system_active, self.parent_override, self.meal_pause, self.holiday,
            self.tv_entity_id, (st.state if st else "?"), self._tv_is_on(),
            self.media_target(), self._off_pending, kids,
        )

    # --- Webhooks -----------------------------------------------------------
    def _fire_webhook(self, url: str) -> None:
        """Ruft eine Hook-URL auf (fire-and-forget).

        Home-Assistant-Webhooks akzeptieren standardmaessig NUR POST und PUT und
        antworten auf GET mit 405. Frueher wurde hier ausschliesslich GET benutzt
        und der Antwort-Status nie geprueft -> HA-Webhooks feuerten nie, ohne dass
        irgendwo ein Fehler sichtbar wurde. Daher: POST zuerst, GET nur als
        Rueckfall (fuer Dienste wie IFTTT, die GET erwarten). Protokolliert wird
        auf WARNING, weil INFO in manchen Installationen nicht geschrieben wird.
        """
        if not url:
            return

        async def _do() -> None:
            session = async_get_clientsession(self.hass)
            timeout = aiohttp.ClientTimeout(total=10)
            try:
                async with session.post(url, timeout=timeout) as resp:
                    status = resp.status
                if status not in (405, 501):
                    self._log_webhook("POST", status, url)
                    return
                # Ziel mag kein POST -> mit GET erneut versuchen.
                async with session.get(url, timeout=timeout) as resp:
                    self._log_webhook("GET", resp.status, url)
            except Exception as err:  # pragma: no cover
                _LOGGER.warning("MedienStop.de Hook FEHLGESCHLAGEN (%s): %s", url, err)

        self.hass.async_create_task(_do())

    @staticmethod
    def _log_webhook(method: str, status: int, url: str) -> None:
        if status < 400:
            _LOGGER.warning("MedienStop.de Hook OK (%s %s): %s", method, status, url)
        else:
            _LOGGER.warning("MedienStop.de Hook FEHLGESCHLAGEN (%s %s): %s", method, status, url)

    def _sync_webhooks(self) -> None:
        """Feuert Aktiv/Inaktiv-Webhooks bei Zustandswechseln (Kinder + Eltern)."""
        primed = self._webhooks_primed
        if not primed:
            # Erster Lauf nach dem Start: die Flanken-Merker EINMALIG auf den
            # Ist-Zustand setzen, ohne zu feuern. Sonst meldet z.B. ein per
            # RestoreEntity wiederhergestellter Elternmodus nach jedem Neustart
            # faelschlich eine frische "aktiv"-Flanke.
            self._webhooks_primed = True
        for cid, c in self.children.items():
            active = (
                c["state"] == STATE_RUNNING and c["remaining"] > 0
                and self.within_window(cid) and not self.meal_pause
            )
            if active != c["_was_active"]:
                c["_was_active"] = active
                if primed:
                    self._fire_webhook(c["url_active"] if active else c["url_inactive"])
        if self.parent_override != self._parent_was_active:
            self._parent_was_active = self.parent_override
            if primed:
                self._fire_webhook(
                    self.parent_url_active if self.parent_override else self.parent_url_inactive
                )

    # ========================================================================
    # TV-STEUERUNG (ausgewählte Entity)
    # ========================================================================
    def _tv_is_on(self) -> bool:
        if not self.tv_entity_id:
            return False
        st = self.hass.states.get(self.tv_entity_id)
        if not st:
            return False
        # AN = alles außer den bekannten Aus-Zustaenden (deckt media_player ab).
        return str(st.state).lower() not in _TV_OFF_STATES

    def _set_tv(self, turn_on: bool) -> None:
        """Schaltet die ausgewählte TV-Entity (generisch via homeassistant.turn_*)."""
        if not self.tv_entity_id:
            return
        # NOT-AUS: Ist "System aktiv" ausgeschaltet, greift MedienStop.de GAR NICHT
        # mehr in den Fernseher ein - weder ein- noch ausschalten. Zentrales
        # Sicherheitsnetz fuer alle Aufrufer (auch verzoegerte, siehe _do_off).
        if not self.system_active:
            _LOGGER.warning(
                "MedienStop.de: TV-Schaltung (%s) unterdrueckt - 'System aktiv' ist AUS",
                "an" if turn_on else "aus",
            )
            return
        service = "turn_on" if turn_on else "turn_off"
        _LOGGER.warning("MedienStop.de schaltet Fernseher %s: %s", service, self.media_target())
        self.hass.async_create_task(
            self.hass.services.async_call(
                "homeassistant", service, {"entity_id": self.tv_entity_id}, blocking=False
            )
        )

    # ========================================================================
    # AKTIONEN
    # ========================================================================
    def start_timer(self, cid: str, pin: str | None = None) -> None:
        child = self.children[cid]
        if not self.system_active:
            raise HomeAssistantError(self.t("err_system_off"))
        if self.meal_pause:
            raise HomeAssistantError(self.t("err_meal_pause"))
        if self.parent_override:
            raise HomeAssistantError(self.t("err_parent_time"))
        if self.another_active(cid):
            raise HomeAssistantError(self.t("err_other_child"))
        if child["remaining"] <= 0:
            raise HomeAssistantError(self.t("err_no_time", name=child["name"]))
        if not self.within_window(cid):
            raise HomeAssistantError(self.t("err_outside_window", name=child["name"]))
        if child["pin"] and str(pin) != child["pin"]:
            raise HomeAssistantError(self.t("err_wrong_pin"))
        child["state"] = STATE_RUNNING
        self._cancel_off()   # evtl. geplante Abschaltung abbrechen
        self._set_tv(True)
        _LOGGER.info("Timer gestartet: %s (%s Min übrig)", cid, child["remaining"])
        self._sync_webhooks()
        self._notify()

    def pause_timer(self, cid: str) -> None:
        child = self.children[cid]
        if child["state"] == STATE_RUNNING:
            child["state"] = STATE_PAUSED
        self._enforce_tv()
        self._sync_webhooks()
        self._notify()

    def stop_timer(self, cid: str) -> None:
        child = self.children[cid]
        child["remaining"] = 0
        child["state"] = STATE_IDLE
        self._enforce_tv()
        self._sync_webhooks()
        self._notify()

    def add_time(self, cid: str | None, minutes: int) -> None:
        """Schreibt Minuten gut. cid=None -> ALLEN Kindern."""
        targets = self.children.keys() if cid in (None, "", "all", "alle") else [cid]
        for c in targets:
            self.children[c]["remaining"] = max(0, self.children[c]["remaining"] + int(minutes))
        _LOGGER.info("%s Min gutgeschrieben für: %s", minutes, list(targets))
        self._notify()

    def reset_statistics(self, cid: str | None = None, scope: str = "all") -> None:
        """Setzt die geschaute Zeit (Statistik) zurück.

        cid=None/""/"alle" -> ALLE Kinder, sonst nur das genannte Kind.
        scope: "all" (Heute+Woche+Monat+Jahr), "today", "week", "month" oder "year".
        """
        targets = list(self.children.keys()) if cid in (None, "", "all", "alle") else [cid]
        # Welche Zähler zurückgesetzt werden (Standard: alle Zeiträume).
        keys = {
            "today": ["watched"],
            "week": ["watched_week"],
            "month": ["watched_month"],
            "year": ["watched_year"],
        }.get(scope, ["watched", "watched_week", "watched_month", "watched_year"])
        for c in targets:
            for k in keys:
                self.children[c][k] = 0
        # "Alle" schließt die Elternzeit-Statistik mit ein.
        if cid in (None, "", "all", "alle"):
            pkeys = {
                "today": ["parent_watched"],
                "week": ["parent_watched_week"],
                "month": ["parent_watched_month"],
                "year": ["parent_watched_year"],
            }.get(scope, ["parent_watched", "parent_watched_week",
                          "parent_watched_month", "parent_watched_year"])
            for k in pkeys:
                setattr(self, k, 0)
        _LOGGER.info("Statistik zurückgesetzt (%s) für: %s", scope, targets)
        self._notify()

    def set_pin(self, cid: str, pin: str) -> None:
        self.children[cid]["pin"] = str(pin or "")
        self._notify()

    def apply_budgets_now(self) -> None:
        daytype = self.current_daytype()
        for cid, child in self.children.items():
            child["remaining"] = self.child_budget(cid, daytype)
            child["state"] = STATE_IDLE
        _LOGGER.info("Budgets angewendet (Tagtyp: %s)", daytype)
        self._notify()

    # ========================================================================
    # ZEITSCHLEIFE + RESET
    # ========================================================================
    def start_clock(self) -> None:
        self._unsub_loop = async_track_time_interval(
            self.hass, self._loop, datetime.timedelta(minutes=1)
        )
        self._unsub_midnight = async_track_time_change(
            self.hass, self._midnight, hour=0, minute=0, second=5
        )
        self._schedule_autooff()
        # Schnelle Abschalt-Prüfung alle 15s (NUR prüfen, NICHT herunterzählen).
        # So geht der TV zuegig aus, wenn jemand ohne Timer/Zeit schaut.
        self._unsub_enforce = async_track_time_interval(
            self.hass, self._enforce_tick, datetime.timedelta(seconds=15)
        )
        # Auf Zustand der Fernseh-Entity reagieren (z.B. manuell ausgeschaltet).
        if self.tv_entity_id:
            self._unsub_tvstate = async_track_state_change_event(
                self.hass, [self.tv_entity_id], self._on_tv_state
            )

    @callback
    def _on_tv_state(self, event) -> None:
        """NUR bei echtem Ausschalten: laufende Timer pausieren + Elternmodus beenden.

        Bewusst OHNE `system_active`-Guard: hier wird nur interner Zustand
        nachgefuehrt (Timer pausieren, Elternmodus beenden), es wird nichts am
        Fernseher geschaltet. Der Not-Aus sitzt zentral in `_set_tv()`.
        """
        new = event.data.get("new_state")
        old = event.data.get("old_state")
        new_state = (new.state if new else "").lower()
        old_state = (old.state if old else "").lower()
        # Nur reagieren, wenn der TV WIRKLICH aus geht (off/standby) und vorher an war.
        # Kurze idle/unavailable/unknown-Aussetzer werden ignoriert, damit der
        # Elternmodus nicht faelschlich beendet wird (und danach das Video kommt).
        self._diag_log(f"tv_state {old_state}->{new_state}")
        if new_state not in _TV_HARD_OFF_STATES:
            return
        if old_state in _TV_HARD_OFF_STATES or old_state in ("", "unavailable", "unknown", "none"):
            _LOGGER.warning("MedienStop.de: TV-Wechsel %s->%s ignoriert (kein echtes Aus)",
                            old_state, new_state)
            return
        _LOGGER.warning("MedienStop.de: TV WIRKLICH aus (%s->%s) -> pausieren + Elternmodus beenden",
                        old_state, new_state)
        changed = False
        for c in self.children.values():
            if c["state"] == STATE_RUNNING:
                c["state"] = STATE_PAUSED
                changed = True
        if self.parent_override:
            self.parent_override = False
            changed = True
        self._cancel_off()
        if changed:
            _LOGGER.info("Fernseher aus -> Timer pausiert, Elternmodus beendet")
            self._sync_webhooks()
            self._notify()

    @callback
    def _enforce_tick(self, _now) -> None:
        # Heartbeat: zeigt, dass die Hintergrund-Prüfung läuft.
        self.last_check = dt_util.now()
        if not self.system_active:
            # NOT-AUS: schwebende Abschaltung verwerfen und Hook-Flanken weiterhin
            # melden - aber NICHTS zaehlen (das passiert ohnehin nur in _loop).
            self._cancel_off()
            self._sync_webhooks()
            self._notify()
            return
        if self.meal_pause:
            self._cancel_off()
            self._set_tv(False)
            self._sync_webhooks()
            self._notify()
            return
        daytype = self.current_daytype()
        authorized, reason = self._scan(daytype, decrement=False)
        if self._tv_is_on() and not authorized:
            if not self._off_pending:
                self._goodbye_then_off(reason or "notimer")
        else:
            self._cancel_off()
        self._sync_webhooks()
        self._notify()

    @callback
    def _loop(self, _now) -> None:
        if not self.system_active:
            # NOT-AUS: schwebende Abschaltung verwerfen. Der Early-Return liegt
            # bewusst VOR _scan(decrement=True) und der Elternzeit-Zaehlung weiter
            # unten -> bei "System aktiv = aus" laeuft KEINE Statistik mit.
            self._cancel_off()
            return

        # Essenspause: hart aus, nichts zählt herunter.
        if self.meal_pause:
            self._set_tv(False)
            self._sync_webhooks()
            self._notify()
            return

        daytype = self.current_daytype()
        authorized, reason = self._scan(daytype, decrement=True)

        # Elternzeit-Statistik: pro Minute zählen, solange Elternzeit aktiv ist und der TV läuft.
        if self.parent_override and self._tv_is_on():
            self.parent_watched += 1
            self.parent_watched_week += 1
            self.parent_watched_month += 1
            self.parent_watched_year += 1

        if self._tv_is_on() and not authorized:
            self._goodbye_then_off(reason or "notimer")
        else:
            self._cancel_off()
        self._sync_webhooks()
        self._notify()

    @staticmethod
    def _media_type(url: str) -> str:
        u = url.lower().split("?")[0]
        if u.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")):
            return "image"
        if u.endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg")):
            return "music"
        return "video"

    def media_target(self) -> str | None:
        """Ziel zum Streamen: eigener Video-Player (Cast) oder sonst die TV-Entity."""
        return self.video_player_id or self.tv_entity_id

    def _play_media(self, url: str, content_type: str | None = None) -> None:
        """Spielt ein Video/Bild auf dem Streaming-Ziel ab (nur media_player)."""
        target = self.media_target()
        if not url or not target:
            return
        if not target.startswith("media_player."):
            _LOGGER.warning("Video/Streaming benoetigt eine media_player-Entity (aktuell %s)", target)
            return
        self.hass.async_create_task(self._async_play_media(url, content_type))

    async def _vorlage_aus_dem_heimnetz(self, url: str) -> str:
        """Liefert eine mitgelieferte Vorlage ueber das Heimnetz statt ueber GitHub.

        Hintergrund: Viele Fernseher und DLNA-Renderer koennen **kein HTTPS**
        (verifiziert mit einem Panasonic Viera: dieselbe Datei per http:// aus
        dem Heimnetz laeuft, per https:// von GitHub bleibt das Geraet stumm -
        ohne Fehlermeldung, weil der Renderer den Auftrag trotzdem annimmt).
        Deshalb wird die Datei einmalig nach <config>/www/medienstop/ geholt und
        von dort per http:// ausgeliefert.

        Alexa geht diesen Weg NICHT: Amazons Server laedt die Datei selbst aus
        dem Internet und braucht dafuer gerade die oeffentliche HTTPS-Adresse.

        Klappt etwas nicht, wird die Original-URL zurueckgegeben - dann ist das
        Verhalten wie bisher, statt gar keiner Ansage.
        """
        import os

        if url not in {u for u, _ in BUNDLED_MEDIA.values()}:
            return url
        name = url.rsplit("/", 1)[-1]
        ordner = self.hass.config.path("www", "medienstop")
        ziel = os.path.join(ordner, name)

        def _vorhanden() -> bool:
            return os.path.isfile(ziel) and os.path.getsize(ziel) > 0

        try:
            if not await self.hass.async_add_executor_job(_vorhanden):
                _LOGGER.warning("MedienStop.de holt die Vorlage %s einmalig ins Heimnetz", name)
                session = async_get_clientsession(self.hass)
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as antwort:
                    antwort.raise_for_status()
                    daten = await antwort.read()

                def _schreiben() -> None:
                    os.makedirs(ordner, exist_ok=True)
                    # Erst daneben schreiben, dann umbenennen: ein Abbruch
                    # hinterlaesst so keine halbe Datei, die spaeter als
                    # "schon vorhanden" durchgeht.
                    vorlaeufig = ziel + ".teil"
                    with open(vorlaeufig, "wb") as fh:
                        fh.write(daten)
                    os.replace(vorlaeufig, ziel)

                await self.hass.async_add_executor_job(_schreiben)

            from homeassistant.helpers.network import NoURLAvailableError, get_url
            try:
                basis = get_url(self.hass, prefer_external=False, allow_internal=True)
            except NoURLAvailableError:
                return url
            return f"{basis.rstrip('/')}/local/medienstop/{name}"
        except Exception as err:  # pragma: no cover - Netz/Dateisystem
            _LOGGER.warning("Vorlage %s konnte nicht lokal bereitgestellt werden (%s) - "
                            "nutze die Adresse von GitHub", name, err)
            return url

    async def async_vorlagen_vorladen(self) -> None:
        """Holt die gebrauchten Vorlagen beim Start einmalig ins Heimnetz.

        Ohne diesen Schritt faende der Download erst statt, wenn die Ansage
        WIRKLICH gebraucht wird - also mitten in einer Abschaltung. Bei einer
        langsamen Leitung liefe die Abschalt-Verzoegerung dann ab, bevor das
        Video ueberhaupt zu sehen war.

        Geladen wird nur, was zum eingestellten Ziel passt:
        * Alexa braucht die oeffentliche HTTPS-Adresse -> gar kein Download.
        * Fernseher/Cast bekommen die Datei aus dem Heimnetz -> vorladen.
        Fehler sind unkritisch: `_vorlage_aus_dem_heimnetz` faellt auf die
        Adresse von GitHub zurueck, es wird dann eben spaeter geladen.
        """
        if not self.media_target() or self._target_is_alexa():
            return
        gebraucht: set[str] = set()
        for reason in ANNOUNCE_KEYS:
            src = normalize_announce(self.media_cfg.get(reason)).get("src")
            if src == SRC_AUTO:
                src = bundled_for(reason, audio=False)
            if src in BUNDLED_MEDIA:
                gebraucht.add(BUNDLED_MEDIA[src][0])
        if not gebraucht:
            return
        fertig = 0
        for url in sorted(gebraucht):
            if (await self._vorlage_aus_dem_heimnetz(url)) != url:
                fertig += 1
        _LOGGER.warning("MedienStop.de: %s von %s Vorlagen liegen im Heimnetz bereit",
                        fertig, len(gebraucht))

    async def _async_play_media(self, url: str, content_type: str | None,
                                notify_on_error: bool = True) -> tuple[bool, str, str]:
        """-> (geklappt, Fehlertext, tatsaechlich genutzte Adresse).

        Die genutzte Adresse kann von der uebergebenen abweichen, weil Vorlagen
        fuer Fernseher aus dem Heimnetz ausgeliefert werden - der Test-Knopf soll
        zeigen, was wirklich abgespielt wurde.
        `notify_on_error=False`, wenn der Aufrufer den Fehler selbst anzeigt.
        """
        # media-source:// und http(s) werden DIREKT an den media_player geschickt.
        # Home Assistant loest media-source fuer das Zielgeraet selbst auf.
        target = self.media_target()
        ctype = content_type or self._media_type(url)
        # Vorlagen ueber das Heimnetz ausliefern - viele TVs koennen kein HTTPS.
        if url.startswith("https://"):
            url = await self._vorlage_aus_dem_heimnetz(url)
        _LOGGER.warning("MedienStop.de play_media -> Ziel=%s, id=%s, typ=%s", target, url, ctype)
        try:
            await self.hass.services.async_call(
                "media_player", "play_media",
                {"entity_id": target, "media_content_id": url,
                 "media_content_type": ctype}, blocking=True,
            )
        except Exception as err:  # pragma: no cover
            _LOGGER.error("play_media auf %s fehlgeschlagen: %s", target, err)
            text = self.t("play_failed", target=target, err=err)
            if notify_on_error:
                await self.hass.services.async_call("persistent_notification", "create", {
                    "title": self.t("title_video"),
                    "message": self.t("play_failed_md", target=target, err=err),
                    "notification_id": "medienstop_video_err"}, blocking=False)
            return False, text, url
        return True, "", url

    @staticmethod
    def _ssml_audio(url: str) -> str:
        """Baut die SSML-Nachricht fuer eine Audiodatei auf Alexa.

        WICHTIG: Der <speak>-Rahmen ist Pflicht. Ohne ihn erkennt der Alexa
        Media Player die Nachricht nicht als SSML, verwirft den <audio>-Tag und
        der Echo bleibt STUMM - ohne jede Fehlermeldung (Bug bis 2.5.0).
        Ausserdem muss die URL in doppelten Anfuehrungszeichen stehen und
        &-Zeichen (Query-Parameter!) muessen maskiert sein, sonst ist das SSML
        ungueltig und Amazon lehnt es ebenfalls stillschweigend ab.
        """
        safe = (url.replace("&", "&amp;").replace("<", "&lt;")
                   .replace(">", "&gt;").replace('"', "&quot;"))
        return f'<speak><audio src="{safe}"/></speak>'

    def _speak_audio_url(self, url: str) -> None:
        """Spielt eine MP3 auf einem Alexa/Echo ab (Umweg ueber SSML).

        Alexa kann per `media_player.play_media` KEINE beliebigen Dateien
        abspielen. Der einzige Weg ist ein SSML-<audio>-Tag in einer Ansage -
        Amazons Server laedt die Datei dann selbst. Voraussetzungen (sonst bleibt
        der Lautsprecher stumm, ohne Fehlermeldung):
          * oeffentlich per HTTPS erreichbar, gueltiges Zertifikat
          * MP3, MPEG Version 2, 48 kbps, 16000/22050/24000 Hz, max. 240 s
        Die mitgelieferten Ansagen erfuellen das (siehe media/README.md).
        """
        self._speak(self._ssml_audio(url), ssml=True)

    def _speak(self, text: str, ssml: bool = False) -> None:
        """Liest einen Text auf dem Streaming-Ziel vor (Alternative zu Video/Audio-Datei,
        v.a. fuer Alexa/Echo-Lautsprecher, die keine eigene Mediendatei abspielen koennen)."""
        target = self.media_target()
        if not text or not target:
            return
        if not target.startswith("media_player."):
            _LOGGER.warning("Ansage benoetigt eine media_player-Entity (aktuell %s)", target)
            return
        self.hass.async_create_task(self._async_speak(text, ssml))

    async def _async_speak(self, text: str, ssml: bool = False,
                           notify_on_error: bool = True) -> tuple[bool, str]:
        """-> (geklappt, Fehlertext). `notify_on_error=False`, wenn der Aufrufer
        den Fehler selbst anzeigt (Test-Knopf im Dialog)."""
        # Nutzt den notify-Service der "Alexa Media Player"-Integration (HACS), der
        # Text direkt ueber Amazons eigene Sprachausgabe vorliest - dafuer wird KEIN
        # gehostetes Audio/Video benoetigt (im Gegensatz zu _play_media). Funktioniert
        # NUR, wenn diese fremde Integration installiert ist und den Service anbietet.
        target = self.media_target()
        if not self.hass.services.has_service("notify", "alexa_media"):
            _LOGGER.warning("Ansage auf %s fehlgeschlagen: notify.alexa_media nicht verfuegbar", target)
            text_err = self.t("speak_no_service", target=target)
            if notify_on_error:
                await self.hass.services.async_call("persistent_notification", "create", {
                    "title": self.t("title_announce"),
                    "message": self.t("speak_no_service_md", target=target),
                    "notification_id": "medienstop_tts_err"}, blocking=False)
            return False, text_err
        # Reiner Text -> "announce" (mit Aufmerksamkeitston). Ein SSML-<audio>-Tag
        # muss dagegen als "tts" gesendet werden, sonst spielt Amazon die Datei nicht.
        msg_type = "tts" if ssml else "announce"
        _LOGGER.warning("MedienStop.de Ansage -> Ziel=%s, typ=%s, text=%s", target, msg_type, text)
        try:
            await self.hass.services.async_call(
                "notify", "alexa_media",
                {"message": text, "target": [target], "data": {"type": msg_type}},
                blocking=True,
            )
        except Exception as err:  # pragma: no cover
            _LOGGER.error("Ansage auf %s fehlgeschlagen: %s", target, err)
            text_err = self.t("speak_failed", target=target, err=err)
            if notify_on_error:
                await self.hass.services.async_call("persistent_notification", "create", {
                    "title": self.t("title_announce"),
                    "message": self.t("speak_failed_md", target=target, err=err),
                    "notification_id": "medienstop_tts_err"}, blocking=False)
            return False, text_err
        return True, ""

    # --- Ansage-Weiche (Vorlage / eigene Datei / URL / Text / Alexa-Klang) ----
    def _target_is_alexa(self) -> bool:
        """True, wenn das Streaming-Ziel ein Alexa/Echo-Geraet ist.

        Alexa-Geraete koennen KEINE beliebigen Mediendateien abspielen; sie
        brauchen den Umweg ueber einen SSML-<audio>-Tag. Erkannt wird das an der
        Integration hinter der Entity ("alexa_media"), damit der Nutzer davon
        nichts wissen muss.
        """
        target = self.media_target()
        if not target:
            return False
        try:
            from homeassistant.helpers import entity_registry as er
            entry = er.async_get(self.hass).async_get(target)
            return bool(entry and entry.platform == "alexa_media")
        except Exception:  # pragma: no cover - Registry nicht verfuegbar
            return False

    def _public_local_url(self, filename: str) -> str:
        """Baut die oeffentliche HTTPS-Adresse einer Datei aus <config>/www/.

        Amazons Server laedt die Datei SELBST - sie muss also von aussen per
        HTTPS erreichbar sein. Dateien unter <config>/www/ werden als /local/...
        ohne Zugangs-Token ausgeliefert; media_source-URLs funktionieren dafuer
        NICHT. Gespeichert wird nur der Dateiname, damit ein Wechsel der
        externen Adresse (Nabu Casa, eigene Domain) nichts kaputt macht.
        """
        from homeassistant.helpers.network import NoURLAvailableError, get_url
        try:
            base = get_url(self.hass, prefer_external=True,
                           allow_internal=False, require_ssl=True)
        except NoURLAvailableError:
            return ""
        return f"{base.rstrip('/')}/local/{filename.lstrip('/')}"

    def _announce_plan(self, reason: str, cfg: dict | None = None) -> tuple[str, str, str | None, str]:
        """Entscheidet OHNE Seiteneffekt, was abgespielt werden soll.

        -> (art, nutzlast, content_type, meldung) mit art aus
        {"nein", "play", "speak", "speak_ssml"}. "nein" heisst: nichts zu tun,
        `meldung` ist dann der Grund im Klartext. Getrennt von der Ausfuehrung,
        damit derselbe Weg einmal beilaeufig (Abschaltung) und einmal mit echtem
        Abwarten (Test-Knopf) benutzt werden kann.
        """
        cfg = normalize_announce(cfg if cfg is not None else self.media_cfg.get(reason))
        src = cfg.get("src", SRC_NONE)
        target = self.media_target()

        if src == SRC_NONE:
            return "nein", "", None, self.t("ann_none")
        if not target:
            return "nein", "", None, self.t("ann_no_target")
        if not target.startswith("media_player."):
            return "nein", "", None, self.t("ann_not_player", target=target)

        # Ein abgemeldetes/entferntes Geraet nimmt Befehle stumm entgegen: nichts
        # passiert, kein Fehler. Genau daran scheiterten Ansagen bisher unbemerkt,
        # wenn als Video-Player noch ein altes Geraet eingetragen war.
        zustand = self.hass.states.get(target)
        if zustand is None:
            return "nein", "", None, self.t("ann_target_missing", target=target)
        if zustand.state in ("unavailable", "unknown"):
            return "nein", "", None, self.t("ann_target_unavailable", target=target,
                                            state=zustand.state)

        is_alexa = self._target_is_alexa()

        # --- "Automatisch passend": jetzt erst die Vorlage bestimmen ---------
        # Erst hier ist bekannt, ob das Ziel ein Echo ist. Dadurch kann der
        # Nutzer die Kombination Geraet/Dateityp gar nicht falsch waehlen, und
        # ein spaeterer Geraetewechsel zieht automatisch nach.
        if src == SRC_AUTO:
            src = bundled_for(reason, audio=is_alexa)
            cfg = {**cfg, "src": src}

        # --- Text-Ansage: laeuft ueber Alexas Sprachausgabe ------------------
        if src == SRC_TTS:
            text = cfg.get("tts") or ""
            if not text:
                return "nein", "", None, self.t("ann_no_tts_text")
            if not is_alexa:
                return "nein", "", None, self.t("ann_tts_needs_alexa", target=target)
            return "speak", text, None, self.t("ann_tts_ok", target=target, text=text)

        # --- Eingebauter Alexa-Klang -----------------------------------------
        if src == SRC_SOUND:
            sound = cfg.get("sound") or ""
            if not sound:
                return "nein", "", None, self.t("ann_no_sound")
            if not is_alexa:
                return "nein", "", None, self.t("ann_sound_needs_alexa", target=target)
            return "play", sound, "sound", self.t("ann_sound_ok", sound=sound, target=target)

        # --- Dateibasierte Quellen -------------------------------------------
        if src == SRC_WWW:
            filename = cfg.get("file") or ""
            if not filename:
                return "nein", "", None, self.t("ann_no_file")
            url = self._public_local_url(filename)
            if not url:
                return "nein", "", None, self.t("ann_no_https")
            ctype = self._media_type(url)
        else:
            url, ctype = announce_media(cfg)
            if not url:
                return "nein", "", None, self.t("ann_no_template")
            ctype = ctype or self._media_type(url)

        if is_alexa:
            # Alexa kann weder media-source-Dateien noch Videos abspielen.
            if url.startswith("media-source"):
                return "nein", "", None, self.t("ann_alexa_no_media_source")
            if ctype == "video" or url.lower().split("?")[0].endswith((".mp4", ".mkv", ".avi")):
                return "nein", "", None, self.t("ann_alexa_no_video")
            if not url.lower().startswith("https://"):
                return "nein", "", None, self.t("ann_alexa_needs_https", url=url)
            return "speak_ssml", self._ssml_audio(url), None, self.t("ann_audio_ok", target=target, url=url)

        return "play", url, ctype, self.t("ann_play_ok", target=target, url=url)

    def announce(self, reason: str, cfg: dict | None = None) -> tuple[bool, str]:
        """Startet die Ansage beilaeufig. -> (gestartet, Klartext-Meldung)

        ACHTUNG: "gestartet" heisst NICHT "hat geklappt" - der eigentliche
        Aufruf laeuft als Hintergrund-Task. Wer wissen muss, ob wirklich Ton
        kam, nimmt `async_announce` (siehe dort).
        """
        art, payload, ctype, meldung = self._announce_plan(reason, cfg)
        if art == "nein":
            return False, meldung
        if art == "play":
            self._play_media(payload, ctype)
        else:
            self._speak(payload, ssml=(art == "speak_ssml"))
        return True, meldung

    async def async_announce(self, reason: str, cfg: dict | None = None) -> tuple[bool, str]:
        """Wie `announce`, wartet aber den Dienst-Aufruf ab. -> (geklappt, Meldung)

        Der Test-Knopf im Dialog braucht das: `announce` meldete frueher immer
        Erfolg, weil es den Aufruf nur als Task startete - ein fehlender
        `notify.alexa_media`-Dienst oder ein stummer Echo blieb dadurch
        unsichtbar (Bug bis 2.5.0).
        """
        art, payload, ctype, meldung = self._announce_plan(reason, cfg)
        if art == "nein":
            return False, meldung
        if art == "play":
            ok, fehler, genutzt = await self._async_play_media(payload, ctype,
                                                               notify_on_error=False)
            if ok and genutzt != payload:
                # Vorlage kam aus dem Heimnetz statt von GitHub -> das soll in der
                # Rueckmeldung stehen, sonst zeigt der Test eine Adresse an, die
                # gar nicht abgespielt wurde.
                meldung = (f"{meldung.split(chr(10))[0]}\n{genutzt}\n"
                           + self.t("ann_local_hint"))
        else:
            ok, fehler = await self._async_speak(payload, ssml=(art == "speak_ssml"),
                                                 notify_on_error=False)
        return (True, meldung) if ok else (False, fehler)

    def _goodbye_then_off(self, reason: str) -> None:
        """Spielt die passende Ansage und schaltet den TV nach Verzoegerung aus."""
        if self._off_pending:
            return
        self._diag_log(f"ABSCHALTUNG geplant reason={reason}")
        self._off_pending = True
        cfg = self.media_cfg.get(reason) or {}
        gespielt, meldung = self.announce(reason)
        # Ohne Ansage sofort aus (wie bisher), sonst die eingestellte Verzoegerung.
        delay = max(0, as_int(cfg.get("delay"), 10)) if gespielt else 0
        _LOGGER.warning("Abschalt-Sequenz (%s): %s | aus in %ss", reason, meldung, delay)
        self._unsub_off = async_call_later(self.hass, delay, self._do_off)

    def test_video(self, which: str = "timeup") -> bool:
        """Spielt die konfigurierte Ansage sofort ab (zum Testen). True = gespielt."""
        gespielt, _meldung = self.announce(which)
        return gespielt

    @callback
    def _do_off(self, _now) -> None:
        self._unsub_off = None
        self._off_pending = False
        # NOT-AUS: Eine Abschaltung wird bis zu 600 s im Voraus geplant. Wird in
        # dieser Zeit "System aktiv" ausgeschaltet, muss der bereits laufende
        # Zeitgeber wirkungslos verfallen (frueher schaltete er den TV trotzdem ab).
        if not self.system_active:
            _LOGGER.warning("MedienStop.de: geplante Abschaltung verworfen - 'System aktiv' ist AUS")
            self._notify()
            return
        self._set_tv(False)
        self._notify()

    def _cancel_off(self) -> None:
        """Bricht eine geplante Abschaltung ab (z.B. wenn wieder berechtigt)."""
        if self._unsub_off:
            self._unsub_off()
            self._unsub_off = None
        self._off_pending = False

    def _scan(self, daytype: str, decrement: bool):
        """Prueft alle laufenden Timer und liefert (berechtigt, grund).

        grund kann sein: "limit" (Fenster vorbei = Schlafenszeit), "timeup"
        (Budget aufgebraucht) oder None. decrement=True zaehlt die Restzeit
        herunter (nur im Minuten-Loop). Ein laufendes Kind, dessen Fenster vorbei
        ist, wird pausiert (damit danach nicht immer wieder "limit" kommt und
        spaetere TV-Starts korrekt als "notimer" gelten).
        """
        authorized = self.parent_override
        reason = None
        for cid, child in self.children.items():
            if child["state"] != STATE_RUNNING:
                continue
            if self.parent_override:
                # Elternzeit: Kinder werden beim Einschalten pausiert (Schalter).
                # Sicherheitsnetz für alle anderen Wege, damit während der
                # Elternzeit NIE Kinderzeit weiterläuft oder Statistik zählt.
                child["state"] = STATE_PAUSED
                continue
            if not self.within_window(cid, daytype):
                reason = reason or "limit"        # Schlafenszeit / Tagesende
                child["state"] = STATE_PAUSED
                continue
            if decrement:
                child["remaining"] = max(0, child["remaining"] - 1)
                child["watched"] += 1
                child["watched_week"] += 1
                child["watched_month"] += 1
                child["watched_year"] += 1
            if child["remaining"] <= 0:
                child["state"] = STATE_IDLE
                reason = reason or "timeup"       # Budget aufgebraucht
            else:
                authorized = True
        return authorized, reason

    def _enforce_tv(self, any_authorized: bool | None = None) -> None:
        if not self.system_active:
            return
        if self.meal_pause:
            if self._tv_is_on():
                self._diag_log("enforce_tv: Essenspause -> TV aus")
            self._set_tv(False)
            return
        if any_authorized is None:
            any_authorized = self.parent_override or any(
                c["state"] == STATE_RUNNING and c["remaining"] > 0 and self.within_window(cid)
                for cid, c in self.children.items()
            )
        if self._tv_is_on() and not any_authorized:
            self._diag_log("enforce_tv: niemand berechtigt -> TV aus")
            self._set_tv(False)

    # --- Diagnose ------------------------------------------------------------
    def diagnostics_text(self) -> str:
        """Menschlich lesbarer Statusbericht: warum (nicht) abgeschaltet wird."""
        T = self.t
        lines = []
        if not self.system_active:
            lines.append(T("diag_emergency_1"))
            lines.append(T("diag_emergency_2"))
            lines.append(T("diag_emergency_3"))
            lines.append("")
        lines.append(T("diag_system", v=self.system_active))
        lines.append(T("diag_parent", v=self.parent_override))
        lines.append(T("diag_meal", v=self.meal_pause))
        lines.append(T("diag_holiday", v=self.holiday))
        tv = self.tv_entity_id or T("diag_no_tv")
        st = self.hass.states.get(self.tv_entity_id) if self.tv_entity_id else None
        roh = st.state if st else T("diag_entity_missing")
        lines.append(T("diag_tv_entity", v=tv))
        lines.append(T("diag_video_player", v=self.media_target()))
        lines.append(T("diag_tv_raw", v=roh))
        lines.append(T("diag_tv_on", v=self._tv_is_on()))
        lines.append(T("diag_daytype", v=self.current_daytype()))
        lines.append(T("diag_children"))
        authorized = self.parent_override
        for cid, c in self.children.items():
            inw = self.within_window(cid)
            auth = c["state"] == STATE_RUNNING and c["remaining"] > 0 and inw
            if auth:
                authorized = True
            lines.append(T("diag_child", name=c["name"], status=self.status_text(cid),
                           remaining=c["remaining"], state=c["state"], inw=inw))
        lines.append(T("diag_authorized", v=authorized))
        would_off = self.system_active and (self.meal_pause or (self._tv_is_on() and not authorized))
        lines.append(T("diag_would_off", v=would_off))
        if not self.system_active:
            lines.append(T("diag_hint_system_off"))
        if not self.tv_entity_id:
            lines.append(T("diag_hint_no_tv"))
        return "\n".join(lines)

    # --- Elternzeit Auto-Aus -------------------------------------------------
    def set_autooff_time(self, value: datetime.time) -> None:
        self.parent_autooff_time = value
        self._schedule_autooff()
        self._notify()

    def set_autooff_enabled(self, enabled: bool) -> None:
        self.parent_autooff_enabled = bool(enabled)
        self._schedule_autooff()
        self._notify()

    def _schedule_autooff(self) -> None:
        """(Neu) registriert den täglichen Auto-Aus-Zeitpunkt für die Elternzeit.

        WICHTIG: Hier NUR den Auto-Aus-Zeitgeber an-/abmelden! Frueher wurden hier
        (aus `shutdown()` kopiert) auch `_unsub_enforce`, `_unsub_tvstate` und
        `_unsub_off` abgemeldet - aber nie wieder registriert. Jedes Verstellen der
        Auto-Aus-Zeit oder des Auto-Aus-Schalters legte damit die 15-Sekunden-
        Pruefung und die TV-Zustandsueberwachung dauerhaft lahm.
        """
        if self._unsub_autooff:
            self._unsub_autooff()
            self._unsub_autooff = None
        if not self.parent_autooff_enabled:
            return
        t = self.parent_autooff_time
        _LOGGER.info("Elternzeit Auto-Aus geplant für %02d:%02d Uhr", t.hour, t.minute)
        self._unsub_autooff = async_track_time_change(
            self.hass, self._autooff_fire, hour=t.hour, minute=t.minute, second=0
        )

    @callback
    def _autooff_fire(self, _now) -> None:
        """Wird täglich zur eingestellten Zeit (parent_autooff_time) aufgerufen.

        Bewusst OHNE `system_active`-Guard: beendet nur die Elternzeit (interner
        Zustand). Der anschliessende `_enforce_tv()` ist bereits geguardet, und
        `_set_tv()` faengt den Not-Aus in jedem Fall ab.
        """
        _LOGGER.info(
            "Auto-Aus ausgelöst um %s (Elternzeit war %s)",
            self.parent_autooff_time, "an" if self.parent_override else "aus",
        )
        if self.parent_override:
            self._diag_log("Elternzeit AUTO-AUS loest aus")
            self.parent_override = False
            self._enforce_tv()
            self._sync_webhooks()
            self._notify()

    @callback
    def _midnight(self, _now) -> None:
        _LOGGER.info("Mitternachts-Reset von MedienStop.de")
        today = dt_util.now().date()
        last = self.last_reset
        new_week = today.isocalendar()[:2] != last.isocalendar()[:2]
        new_month = (today.year, today.month) != (last.year, last.month)
        new_year = today.year != last.year
        for child in self.children.values():
            child["watched"] = 0
            if new_week:
                child["watched_week"] = 0
            if new_month:
                child["watched_month"] = 0
            if new_year:
                child["watched_year"] = 0
        # Elternzeit-Statistik analog zurücksetzen.
        self.parent_watched = 0
        if new_week:
            self.parent_watched_week = 0
        if new_month:
            self.parent_watched_month = 0
        if new_year:
            self.parent_watched_year = 0
        self.last_reset = today
        self.apply_budgets_now()

    def shutdown(self) -> None:
        if self._unsub_loop:
            self._unsub_loop()
            self._unsub_loop = None
        if self._unsub_midnight:
            self._unsub_midnight()
            self._unsub_midnight = None
        if self._unsub_autooff:
            self._unsub_autooff()
            self._unsub_autooff = None
        if self._unsub_enforce:
            self._unsub_enforce()
            self._unsub_enforce = None
        if self._unsub_tvstate:
            self._unsub_tvstate()
            self._unsub_tvstate = None
        if self._unsub_off:
            self._unsub_off()
            self._unsub_off = None
        self._unsub_tvstate = None
        self.last_reset = dt_util.now().date()


# =============================================================================
# SETUP / UNLOAD
# =============================================================================
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    manager = MedienStopManager(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Nach dem Wiederherstellen (Budgets/Restzeit sind jetzt geladen): fuer Kinder
    # OHNE wiederhergestellte Restzeit (Neuinstallation) das Budget anwenden.
    # Bestehende Restzeiten bleiben ueber Neustarts erhalten.
    for cid, child in manager.children.items():
        if not child.get("_remaining_restored"):
            child["remaining"] = manager.child_budget(cid)
            child["state"] = STATE_IDLE
    manager._notify()
    manager.start_clock()
    _async_register_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    # Vorlagen im Hintergrund ins Heimnetz holen - NACH start_clock und als
    # eigener Task, damit der Start von Home Assistant nicht auf den Download
    # wartet. Laeuft auch nach jeder Konfigurationsaenderung erneut (die loest
    # einen Reload aus), sodass ein Wechsel des Zielgeraets nachzieht.
    entry.async_create_background_task(
        hass, manager.async_vorlagen_vorladen(), "medienstop_vorlagen_vorladen")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        manager: MedienStopManager = hass.data[DOMAIN].pop(entry.entry_id)
        manager.shutdown()
        if not _managers(hass):
            for svc in (
                SERVICE_START, SERVICE_PAUSE, SERVICE_STOP,
                SERVICE_ADD_TIME, SERVICE_SET_PIN, SERVICE_APPLY_BUDGETS,
                SERVICE_CREATE_DASHBOARD,
                SERVICE_PLAY_MEDIA,
                SERVICE_TEST_VIDEO,
            ):
                hass.services.async_remove(DOMAIN, svc)
            hass.data[DOMAIN].pop(_SERVICES_REGISTERED, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


# =============================================================================
# SERVICES
# =============================================================================
def _managers(hass: HomeAssistant) -> list[MedienStopManager]:
    return [v for v in hass.data.get(DOMAIN, {}).values() if isinstance(v, MedienStopManager)]


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.data[DOMAIN].get(_SERVICES_REGISTERED):
        return

    child_only = vol.Schema({vol.Required(ATTR_CHILD): cv.string})
    start_schema = vol.Schema({
        vol.Required(ATTR_CHILD): cv.string,
        vol.Optional(ATTR_PIN): cv.string,
    })
    # add_time: child OPTIONAL -> leer/all = alle Kinder
    add_schema = vol.Schema({
        vol.Optional(ATTR_CHILD): cv.string,
        vol.Required(ATTR_MINUTES): vol.Coerce(int),
    })
    pin_schema = vol.Schema({
        vol.Required(ATTR_CHILD): cv.string,
        vol.Optional(ATTR_PIN, default=""): cv.string,
    })
    # reset_statistics: child OPTIONAL -> leer/alle = alle Kinder
    reset_schema = vol.Schema({
        vol.Optional(ATTR_CHILD): cv.string,
        vol.Optional(ATTR_SCOPE, default="all"): vol.In(
            ["all", "today", "week", "month", "year"]
        ),
    })

    def _mgr_for(child: str) -> MedienStopManager:
        for mgr in _managers(hass):
            if child in mgr.children:
                return mgr
        raise HomeAssistantError(_text(hass, "err_unknown_child", child=child))

    def _user(call: ServiceCall) -> str | None:
        """HA-Benutzer, der den Service ausgelöst hat (None bei Automationen)."""
        ctx = getattr(call, "context", None)
        return getattr(ctx, "user_id", None) if ctx else None

    async def _check_parent_action(call: ServiceCall, action: str) -> None:
        """Eltern-Aktion (alle Kinder / Hub): für Kind-Benutzer gesperrt."""
        for mgr in _managers(hass):
            await mgr.async_check_user(_user(call), None, action)

    async def _start(call: ServiceCall) -> None:
        cid = call.data[ATTR_CHILD]
        mgr = _mgr_for(cid)
        await mgr.async_check_user(_user(call), cid, "act_start")
        mgr.start_timer(cid, call.data.get(ATTR_PIN))

    async def _pause(call: ServiceCall) -> None:
        cid = call.data[ATTR_CHILD]
        mgr = _mgr_for(cid)
        await mgr.async_check_user(_user(call), cid, "act_pause")
        mgr.pause_timer(cid)

    async def _stop(call: ServiceCall) -> None:
        cid = call.data[ATTR_CHILD]
        mgr = _mgr_for(cid)
        await mgr.async_check_user(_user(call), cid, "act_stop")
        mgr.stop_timer(cid)

    async def _add(call: ServiceCall) -> None:
        child = call.data.get(ATTR_CHILD)
        minutes = call.data[ATTR_MINUTES]
        # Zeit gutschreiben ist Elternsache - auch für das eigene Kind gesperrt.
        await _check_parent_action(call, "act_add_time")
        if child in (None, "", "all", "alle"):
            # ALLEN Kindern aller Manager Zeit geben
            for mgr in _managers(hass):
                mgr.add_time(None, minutes)
        else:
            _mgr_for(child).add_time(child, minutes)

    async def _setpin(call: ServiceCall) -> None:
        await _check_parent_action(call, "act_set_pin")
        _mgr_for(call.data[ATTR_CHILD]).set_pin(call.data[ATTR_CHILD], call.data.get(ATTR_PIN, ""))

    async def _apply(call: ServiceCall) -> None:
        await _check_parent_action(call, "act_apply_budgets")
        for mgr in _managers(hass):
            mgr.apply_budgets_now()

    async def _reset_stats(call: ServiceCall) -> None:
        child = call.data.get(ATTR_CHILD)
        scope = call.data.get(ATTR_SCOPE, "all")
        await _check_parent_action(call, "act_reset_stats")
        if child in (None, "", "all", "alle"):
            for mgr in _managers(hass):
                mgr.reset_statistics(None, scope)
        else:
            _mgr_for(child).reset_statistics(child, scope)

    async def _create_dashboard(call: ServiceCall) -> None:
        # Standard: Anzahl aus der ersten Konfiguration; optional überschreibbar.
        mgrs = _managers(hass)
        default_children = mgrs[0].num_children if mgrs else 2
        default_profiles = mgrs[0].num_profiles if mgrs else 1
        children = int(call.data.get("children", default_children))
        profiles = int(call.data.get("profiles", default_profiles))
        # Echte (ggf. umbenannte) Namen aus der ersten Konfiguration verwenden.
        from .entity import device_display_name, resolve_entity_ids
        child_names, profile_names = {}, {}
        if mgrs:
            eid = mgrs[0].entry.entry_id
            child_names = {cid: device_display_name(hass, eid, cid, mgrs[0].children[cid]["name"])
                           for cid in mgrs[0].children}
            profile_names = {pid: device_display_name(hass, eid, pid, mgrs[0].profiles[pid]["name"])
                             for pid in mgrs[0].profiles}
        ids = resolve_entity_ids(hass, mgrs[0].entry.entry_id) if mgrs else {}
        tab_users = mgrs[0].tab_users if mgrs else {}
        admin_users = mgrs[0].admin_users if mgrs else []
        lang = "en" if (hass.config.language or "de")[:2].lower() == "en" else "de"
        # Sammel-Tab "Kinder" fuer die Eltern (Standard: an) - Einstellung unter
        # Konfigurieren -> Sichtbarkeit.
        kid_tab = bool(mgrs[0].entry.data.get(CONF_PARENT_KID_TAB, True)) if mgrs else True
        yaml_str = build_dashboard_yaml(children, profiles, child_names, profile_names, ids,
                                        tab_users, admin_users, lang, kid_tab)
        if lang == "en":
            title = "MedienStop.de – Dashboard template"
            message = (
                f"Template for {children} child(ren) and {profiles} profile(s). "
                "Copy it and paste into Settings -> Dashboards -> new dashboard -> "
                "Raw configuration editor.\n\n"
                "```yaml\n" + yaml_str + "```\n"
            )
        else:
            title = "MedienStop.de – Dashboard-Vorlage"
            message = (
                f"Vorlage für {children} Kind(er) und {profiles} Profil(e). "
                "Kopieren und in Einstellungen -> Dashboards -> neues Dashboard -> "
                "Raw-Konfigurationseditor einfuegen.\n\n"
                "```yaml\n" + yaml_str + "```\n"
            )
        await hass.services.async_call(
            "persistent_notification", "create",
            {"title": title, "message": message,
             "notification_id": "medienstop_dashboard"}, blocking=False,
        )

    hass.services.async_register(DOMAIN, SERVICE_START, _start, schema=start_schema)
    hass.services.async_register(DOMAIN, SERVICE_PAUSE, _pause, schema=child_only)
    hass.services.async_register(DOMAIN, SERVICE_STOP, _stop, schema=child_only)
    hass.services.async_register(DOMAIN, SERVICE_ADD_TIME, _add, schema=add_schema)
    hass.services.async_register(DOMAIN, SERVICE_SET_PIN, _setpin, schema=pin_schema)
    hass.services.async_register(DOMAIN, SERVICE_APPLY_BUDGETS, _apply, schema=vol.Schema({}))
    hass.services.async_register(DOMAIN, SERVICE_RESET_STATS, _reset_stats, schema=reset_schema)
    async def _play_media(call: ServiceCall) -> None:
        media = call.data.get("media")
        if media:
            url = media.get("media_content_id")
            ctype = media.get("media_content_type")
        else:
            url = call.data.get("url")
            ctype = call.data.get("content_type")
        if not url:
            raise HomeAssistantError(_text(hass, "err_no_media"))
        for mgr in _managers(hass):
            mgr._play_media(url, ctype)

    hass.services.async_register(DOMAIN, SERVICE_PLAY_MEDIA, _play_media, schema=vol.Schema({
        vol.Optional("media"): dict,
        vol.Optional("url"): cv.string,
        vol.Optional("content_type"): cv.string,
    }))

    async def _test_video(call: ServiceCall) -> None:
        which = call.data.get("which", "timeup")
        # Sprache nach HA-Einstellung (en -> Englisch, sonst Deutsch).
        en = (hass.config.language or "de")[:2].lower() == "en"
        title = "MedienStop.de – Video test" if en else "MedienStop.de – Video-Test"
        for mgr in _managers(hass):
            gespielt, meldung = await mgr.async_announce(which)
            if not gespielt:
                msg = meldung
            elif mgr._target_is_alexa():
                msg = (meldung + "\n\n"
                       "Nothing audible? The Echo needs the (HACS) **Alexa Media Player** "
                       "integration, and audio files must meet Amazon's format rules "
                       "(see media/README.md)."
                       if en else
                       meldung + "\n\n"
                       "Nichts zu hoeren? Der Echo benoetigt die (HACS-)Integration "
                       "**Alexa Media Player**, und Audiodateien muessen Amazons "
                       "Formatvorgaben erfuellen (siehe media/README.md).")
            else:
                msg = (meldung + "\n\n"
                       "Does the **browser** open instead of the video picture? Then this "
                       "target is not a directly streamable player (e.g. Samsung/LG/Android "
                       "TV). In that case choose a **Cast/Chromecast player** as 'video "
                       "player' under Configure."
                       if en else
                       meldung + "\n\n"
                       "Oeffnet sich der **Browser** statt des Videobilds? Dann ist dieses Ziel "
                       "kein direkt streamfaehiger Player (z.B. Samsung/LG/Android-TV). Waehle dann "
                       "unter Konfigurieren einen **Cast-/Chromecast-Player** als 'Video-Player'.")
            await hass.services.async_call("persistent_notification", "create", {
                "title": title, "message": msg,
                "notification_id": "medienstop_videotest"}, blocking=False)

    hass.services.async_register(DOMAIN, SERVICE_TEST_VIDEO, _test_video, schema=vol.Schema({
        vol.Optional("which", default="timeup"): vol.In(["timeup", "limit", "notimer"]),
    }))
    hass.services.async_register(DOMAIN, SERVICE_CREATE_DASHBOARD, _create_dashboard, schema=vol.Schema({
        vol.Optional("children"): vol.Coerce(int),
        vol.Optional("profiles"): vol.Coerce(int),
    }))

    hass.data[DOMAIN][_SERVICES_REGISTERED] = True
