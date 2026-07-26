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
from .const import (
    ATTR_CHILD,
    CONF_NAMES,
    ATTR_MINUTES,
    ATTR_SCOPE,
    ATTR_PIN,
    CONF_NUM_CHILDREN,
    CONF_ADMIN_USERS,
    CONF_NUM_PROFILES,
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
        # Videos vor dem Ausschalten (werden im Options-Flow per Media-Browser gesetzt)
        _vids = entry.data.get(CONF_VIDEOS, {})

        def _v(key):
            d = _vids.get(key, {}) or {}
            return d.get("id", ""), (d.get("type") or None), int(d.get("delay", 10) or 10)

        self.video_timeup, self.video_timeup_type, self.delay_timeup = _v("timeup")
        self.video_limit, self.video_limit_type, self.delay_limit = _v("limit")
        self.video_notimer, self.video_notimer_type, self.delay_notimer = _v("notimer")
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
        if child["state"] == STATE_PAUSED:
            return STATUS_PAUSED
        if child["state"] == STATE_RUNNING:
            return STATUS_RUNNING if self.within_window(cid) else STATUS_BLOCKED
        # hat Zeit, läuft aber nicht: belegt, wenn anderes Kind oder Elternzeit aktiv
        if self.parent_override or self.another_active(cid):
            return STATUS_BUSY
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
        """Ruft eine URL per HTTP GET auf (fire-and-forget)."""
        if not url:
            return
        _LOGGER.info("MedienStop.de Webhook: %s", url)

        async def _do() -> None:
            try:
                session = async_get_clientsession(self.hass)
                await session.get(url, timeout=aiohttp.ClientTimeout(total=10))
            except Exception as err:  # pragma: no cover
                _LOGGER.warning("Webhook fehlgeschlagen (%s): %s", url, err)

        self.hass.async_create_task(_do())

    def _sync_webhooks(self) -> None:
        """Feuert Aktiv/Inaktiv-Webhooks bei Zustandswechseln (Kinder + Eltern)."""
        for cid, c in self.children.items():
            active = (
                c["state"] == STATE_RUNNING and c["remaining"] > 0
                and self.within_window(cid) and not self.meal_pause
            )
            if active != c["_was_active"]:
                c["_was_active"] = active
                self._fire_webhook(c["url_active"] if active else c["url_inactive"])
        if self.parent_override != self._parent_was_active:
            self._parent_was_active = self.parent_override
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
            raise HomeAssistantError("MedienStop.de-System ist deaktiviert.")
        if self.meal_pause:
            raise HomeAssistantError("Essenspause aktiv - bitte warten.")
        if self.parent_override:
            raise HomeAssistantError("Elternzeit aktiv - Kinder pausiert.")
        if self.another_active(cid):
            raise HomeAssistantError("Ein anderes Kind schaut gerade - bitte warten.")
        if child["remaining"] <= 0:
            raise HomeAssistantError(f"{child['name']} hat keine Zeit mehr (Start nicht möglich).")
        if not self.within_window(cid):
            raise HomeAssistantError(f"Außerhalb der erlaubten Zeit für {child['name']}.")
        if child["pin"] and str(pin) != child["pin"]:
            raise HomeAssistantError("Falscher PIN.")
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
        """NUR bei echtem Ausschalten: laufende Timer pausieren + Elternmodus beenden."""
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
            self._notify()
            return
        if self.meal_pause:
            self._cancel_off()
            self._set_tv(False)
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
            return

        # Essenspause: hart aus, nichts zählt herunter.
        if self.meal_pause:
            self._set_tv(False)
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

    async def _async_play_media(self, url: str, content_type: str | None) -> None:
        # media-source:// und http(s) werden DIREKT an den media_player geschickt.
        # Home Assistant loest media-source fuer das Zielgeraet selbst auf.
        target = self.media_target()
        ctype = content_type or self._media_type(url)
        _LOGGER.info("MedienStop.de play_media -> Ziel=%s, id=%s, typ=%s", target, url, ctype)
        try:
            await self.hass.services.async_call(
                "media_player", "play_media",
                {"entity_id": target, "media_content_id": url,
                 "media_content_type": ctype}, blocking=True,
            )
        except Exception as err:  # pragma: no cover
            _LOGGER.error("play_media auf %s fehlgeschlagen: %s", target, err)
            await self.hass.services.async_call("persistent_notification", "create", {
                "title": "MedienStop.de – Video",
                "message": (f"Abspielen auf **{target}** fehlgeschlagen:\n{err}\n\n"
                            "Ist das die richtige (media_player-)Entitaet und das Geraet an?"),
                "notification_id": "medienstop_video_err"}, blocking=False)

    def _goodbye_then_off(self, reason: str) -> None:
        """Spielt das passende Video und schaltet den TV nach Verzoegerung aus."""
        if self._off_pending:
            return
        self._diag_log(f"ABSCHALTUNG geplant reason={reason}")
        url = {"timeup": self.video_timeup, "limit": self.video_limit,
               "notimer": self.video_notimer}.get(reason, "")
        ctype = {"timeup": self.video_timeup_type, "limit": self.video_limit_type,
                 "notimer": self.video_notimer_type}.get(reason)
        self._off_pending = True
        delays = {"timeup": self.delay_timeup, "limit": self.delay_limit,
                  "notimer": self.delay_notimer}
        if url:
            self._play_media(url, ctype)
            delay = max(0, int(delays.get(reason, 10)))
        else:
            delay = 0  # kein Video -> sofort aus (wie bisher)
        _LOGGER.warning("Abschalt-Sequenz (%s): Video=%s, aus in %ss", reason, bool(url), delay)
        self._unsub_off = async_call_later(self.hass, delay, self._do_off)

    def test_video(self, which: str = "timeup") -> bool:
        """Spielt das konfigurierte Video sofort ab (zum Testen). True = gespielt."""
        url = {"timeup": self.video_timeup, "limit": self.video_limit,
               "notimer": self.video_notimer}.get(which, "")
        ctype = {"timeup": self.video_timeup_type, "limit": self.video_limit_type,
                 "notimer": self.video_notimer_type}.get(which)
        if url:
            self._play_media(url, ctype)
            return True
        return False

    @callback
    def _do_off(self, _now) -> None:
        self._unsub_off = None
        self._off_pending = False
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
        lines = []
        lines.append(f"System aktiv:    {self.system_active}")
        lines.append(f"Elternzeit:      {self.parent_override}")
        lines.append(f"Essenspause:     {self.meal_pause}")
        lines.append(f"Ferien heute:    {self.holiday}")
        tv = self.tv_entity_id or "(KEINE TV-Entity gewählt!)"
        st = self.hass.states.get(self.tv_entity_id) if self.tv_entity_id else None
        roh = st.state if st else "(Entity nicht gefunden)"
        lines.append(f"TV-Entity:       {tv}")
        lines.append(f"Video-Player:    {self.media_target()}")
        lines.append(f"TV roher Zustand:{roh}")
        lines.append(f"TV gilt als an:  {self._tv_is_on()}")
        lines.append(f"Tagtyp heute:    {self.current_daytype()}")
        lines.append("Kinder:")
        authorized = self.parent_override
        for cid, c in self.children.items():
            inw = self.within_window(cid)
            auth = c["state"] == STATE_RUNNING and c["remaining"] > 0 and inw
            if auth:
                authorized = True
            lines.append(
                f"  - {c['name']}: status={self.status_text(cid)} "
                f"rest={c['remaining']}min state={c['state']} im_fenster={inw}"
            )
        lines.append(f"=> Jemand berechtigt: {authorized}")
        would_off = self.system_active and (self.meal_pause or (self._tv_is_on() and not authorized))
        lines.append(f"=> TV müsste AUS sein: {would_off}")
        if not self.system_active:
            lines.append("HINWEIS: 'System aktiv' ist AUS -> MedienStop schaltet nichts!")
        if not self.tv_entity_id:
            lines.append("HINWEIS: Keine TV-Entity gewählt -> es kann nichts geschaltet werden!")
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
        """(Neu) registriert den täglichen Auto-Aus-Zeitpunkt für die Elternzeit."""
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
        if not self.parent_autooff_enabled:
            return
        t = self.parent_autooff_time
        _LOGGER.info("Elternzeit Auto-Aus geplant für %02d:%02d Uhr", t.hour, t.minute)
        self._unsub_autooff = async_track_time_change(
            self.hass, self._autooff_fire, hour=t.hour, minute=t.minute, second=0
        )

    @callback
    def _autooff_fire(self, _now) -> None:
        """Wird täglich zur eingestellten Zeit (parent_autooff_time) aufgerufen."""
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
        raise HomeAssistantError(f"Unbekanntes Kind: {child}")

    async def _start(call: ServiceCall) -> None:
        _mgr_for(call.data[ATTR_CHILD]).start_timer(call.data[ATTR_CHILD], call.data.get(ATTR_PIN))

    async def _pause(call: ServiceCall) -> None:
        _mgr_for(call.data[ATTR_CHILD]).pause_timer(call.data[ATTR_CHILD])

    async def _stop(call: ServiceCall) -> None:
        _mgr_for(call.data[ATTR_CHILD]).stop_timer(call.data[ATTR_CHILD])

    async def _add(call: ServiceCall) -> None:
        child = call.data.get(ATTR_CHILD)
        minutes = call.data[ATTR_MINUTES]
        if child in (None, "", "all", "alle"):
            # ALLEN Kindern aller Manager Zeit geben
            for mgr in _managers(hass):
                mgr.add_time(None, minutes)
        else:
            _mgr_for(child).add_time(child, minutes)

    async def _setpin(call: ServiceCall) -> None:
        _mgr_for(call.data[ATTR_CHILD]).set_pin(call.data[ATTR_CHILD], call.data.get(ATTR_PIN, ""))

    async def _apply(call: ServiceCall) -> None:
        for mgr in _managers(hass):
            mgr.apply_budgets_now()

    async def _reset_stats(call: ServiceCall) -> None:
        child = call.data.get(ATTR_CHILD)
        scope = call.data.get(ATTR_SCOPE, "all")
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
        yaml_str = build_dashboard_yaml(children, profiles, child_names, profile_names, ids,
                                        tab_users, admin_users, lang)
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
            raise HomeAssistantError("Bitte eine Mediendatei auswaehlen oder eine URL angeben.")
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
            url = {"timeup": mgr.video_timeup, "limit": mgr.video_limit,
                   "notimer": mgr.video_notimer}.get(which, "")
            tgt = mgr.media_target()
            if not url:
                msg = (f"No video is set for '{which}'. Please pick one under "
                       "Configure -> Videos."
                       if en else
                       f"Fuer '{which}' ist kein Video gesetzt. Bitte unter "
                       "Konfigurieren -> Videos auswaehlen.")
            elif not (tgt or "").startswith("media_player."):
                msg = (f"The streaming target **{tgt}** is not a media_player. Please "
                       "choose a video player (media_player) under Configure."
                       if en else
                       f"Das Streaming-Ziel **{tgt}** ist kein media_player. "
                       "Bitte unter Konfigurieren einen Video-Player (media_player) waehlen.")
            else:
                mgr.test_video(which)
                msg = (f"Sending video to **{tgt}**:\n{url}\n\n"
                       "Does the **browser** open instead of the video picture? Then this "
                       "target is not a directly streamable player (e.g. Samsung/LG/Android "
                       "TV). In that case choose a **Cast/Chromecast player** as 'video "
                       "player' under Configure."
                       if en else
                       f"Sende Video an **{tgt}**:\n{url}\n\n"
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
