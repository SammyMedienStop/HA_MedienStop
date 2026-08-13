# custom_components/medienstop/const.py
# -----------------------------------------------------------------------------
# Nur Konstanten + reine Hilfsfunktionen -> keine zyklischen Importe.
# Das ist die stabile Basis, von der ALLE Module importieren.
# -----------------------------------------------------------------------------

DOMAIN = "medienstop"

# Plattformen, die HA für diese Integration laedt.
PLATFORMS: list[str] = ["switch", "sensor", "binary_sensor", "number", "time", "select", "text", "button"]

# --- Config-/Options-Schlüssel ---------------------------------------------
CONF_NUM_CHILDREN = "num_children"     # Anzahl Kinder (1-9)
CONF_NUM_PROFILES = "num_profiles"     # Anzahl Zeit-Profile (1-5)
CONF_KID_DASHBOARD = "kid_dashboard"   # gewählte Kinder-Dashboard-Variante
CONF_TV_ENTITY = "tv_entity"           # bestehende Entity, die als Fernseher geschaltet wird
CONF_VIDEO_PLAYER = "video_player"     # media_player zum Streamen der Videos (z.B. Cast)
CONF_NAMES = "names"                   # {kind_1: Name, profil_1: Name, ...}
CONF_TAB_USERS = "tab_users"           # {kind_1: user_id, ...} fuer Tab-Sichtbarkeit
CONF_ADMIN_USERS = "admin_users"       # [user_id, ...] sehen Eltern-/Einstell-Tabs
CONF_VIDEOS = "videos"                 # {timeup:{id,type,delay}, limit:{...}, notimer:{...}}

# --- Grenzen / Standardwerte ------------------------------------------------
MIN_CHILDREN, MAX_CHILDREN = 1, 9
MIN_PROFILES, MAX_PROFILES = 1, 5
MAX_BUDGET = 600                        # Obergrenze Tagesbudget (Minuten)

# --- Tagtypen ----------------------------------------------------------------
DAY_WERKTAG = "werktag"
DAY_WOCHENENDE = "wochenende"
DAY_FERIEN = "ferien"
DAY_TYPES: list[str] = [DAY_WERKTAG, DAY_WOCHENENDE, DAY_FERIEN]

# Standard-Budget je Tagtyp (Minuten) - Startwerte für neue Profile.
DEFAULT_BUDGETS: dict[str, int] = {
    DAY_WERKTAG: 60,
    DAY_WOCHENENDE: 120,
    DAY_FERIEN: 180,
}

# Standard-Zeitfenster je Tagtyp (Stunde, Minute) als (start, ende).
# 00:00-23:59 bedeutet praktisch "ganztags erlaubt"; einfach enger stellen.
DEFAULT_WINDOWS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    DAY_WERKTAG: ((8, 0), (19, 0)),
    DAY_WOCHENENDE: ((8, 0), (21, 0)),
    DAY_FERIEN: ((8, 0), (21, 0)),
}

# --- Zustaende eines Kind-Timers (gespeichert) ------------------------------
STATE_IDLE = "idle"        # kein Timer aktiv
STATE_RUNNING = "running"  # läuft
STATE_PAUSED = "paused"    # pausiert

# --- abgeleitete Status-Texte (nur Anzeige im Sensor) -----------------------
STATUS_IDLE = "leer"          # Restzeit 0 -> kein Schauen mehr möglich
STATUS_READY = "bereit"       # Zeit vorhanden, Timer nicht gestartet
STATUS_RUNNING = "läuft"     # läuft und innerhalb Fenster
STATUS_PAUSED = "pausiert"    # vom Kind/Eltern pausiert
STATUS_BLOCKED = "gesperrt"   # läuft, aber außerhalb des erlaubten Fensters
STATUS_BUSY = "belegt"        # darf nicht starten: anderes Kind/Elternzeit aktiv

# --- Kinder-Dashboard-Varianten ---------------------------------------------
KID_DASH_SHARED = "shared_pin"     # Variante 1: ein Dashboard für alle, PIN je Kind
KID_DASH_PER_CHILD = "per_child"   # Variante 2: pro Kind ein Dashboard (Benutzerfreigabe)
KID_DASH_VARIANTS: list[str] = [KID_DASH_SHARED, KID_DASH_PER_CHILD]

# --- Service-IDs -------------------------------------------------------------
SERVICE_START = "start_timer"          # Play (Kind)
SERVICE_PAUSE = "pause_timer"          # Pause
SERVICE_STOP = "stop_timer"            # Stop -> Restzeit auf 0
SERVICE_ADD_TIME = "add_time"          # Eltern: Minuten gutschreiben
SERVICE_SET_PIN = "set_pin"            # Eltern: PIN eines Kindes setzen/löschen
SERVICE_APPLY_BUDGETS = "apply_budgets_now"  # Budgets sofort als Restzeit anwenden
SERVICE_CREATE_DASHBOARD = "create_dashboard"  # Dashboard-Vorlage als Benachrichtigung
SERVICE_PLAY_MEDIA = "play_media"             # Video/Bild an den Fernseher streamen
SERVICE_TEST_VIDEO = "test_video"             # konfiguriertes Video sofort testen
SERVICE_RESET_STATS = "reset_statistics"      # geschaute Zeit (Statistik) zuruecksetzen

# --- Service-/Attribut-Felder ------------------------------------------------
ATTR_CHILD = "child"      # Kind-ID, z.B. kind_1
ATTR_PIN = "pin"          # Klartext-PIN (Kind)
ATTR_MINUTES = "minutes"  # Minuten
ATTR_SCOPE = "scope"      # Reset-Umfang: all/today/week/month/year

# --- Dispatcher-Signal (pro Config-Entry eindeutig) -------------------------
SIGNAL_UPDATE = "medienstop_update_{entry_id}"


# --- Ansagen vor dem Abschalten ---------------------------------------------
# Drei Gruende, je eine eigene Quelle + Verzoegerung.
ANNOUNCE_KEYS: list[str] = ["timeup", "limit", "notimer"]

# Quellen-Kennungen. Die sechs Vorlagen (siehe BUNDLED_MEDIA) sind eigene
# Quellen-Werte, damit im Konfigurations-Dialog EIN Auswahlfeld genuegt.
SRC_NONE = "none"       # keine Ansage -> sofort aus
SRC_MEDIA = "media"     # eigene Datei aus dem Media-Browser (media-source://)
SRC_WWW = "www"         # eigene Datei aus <config>/www/ (oeffentlich per HTTPS)
SRC_URL = "url"         # eigene, frei eingegebene URL
SRC_TTS = "tts"         # Text-Ansage (Alexa liest vor)
SRC_SOUND = "sound"     # eingebauter Alexa-Klang (Amazon-Soundbibliothek)

# Mitgelieferte Ansagen. Sie liegen oeffentlich im GitHub-Repo und werden von
# dort geladen -> der Nutzer muss NICHTS herunterladen oder kopieren.
# Bewusst auf Branch "main" (nicht auf einen Tag), damit spaetere Korrekturen an
# den Dateien auch bestehende Installationen erreichen.
# ACHTUNG: Dateinamen nie aendern - Amazons Server rufen genau diese URLs ab.
_RAW_MEDIA = "https://raw.githubusercontent.com/SammyMedienStop/HA_MedienStop/main/media"

# Quellen-Wert -> (URL, media_content_type)
# Die .mp3 sind Alexa-tauglich konvertiert (MPEG2 / 48 kbps / 24000 Hz / mono),
# die .mp4 sind fuer Fernseher und Chromecast gedacht.
BUNDLED_MEDIA: dict[str, tuple[str, str]] = {
    "video_timeup":  (f"{_RAW_MEDIA}/timeup_fernsehzeit-vorbei.mp4", "video"),
    "video_limit":   (f"{_RAW_MEDIA}/limit_schlaft-gut.mp4",         "video"),
    "video_notimer": (f"{_RAW_MEDIA}/notimer_keine-tv-zeit.mp4",     "video"),
    "audio_timeup":  (f"{_RAW_MEDIA}/timeup_fernsehzeit-vorbei.mp3", "music"),
    "audio_limit":   (f"{_RAW_MEDIA}/limit_schlaft-gut.mp3",         "music"),
    "audio_notimer": (f"{_RAW_MEDIA}/notimer_keine-tv-zeit.mp3",     "music"),
}

# Reihenfolge im Auswahlfeld: erst die Vorlagen, dann eigene Quellen.
ANNOUNCE_SOURCES: list[str] = list(BUNDLED_MEDIA) + [
    SRC_MEDIA, SRC_WWW, SRC_URL, SRC_TTS, SRC_SOUND, SRC_NONE,
]

# Passende Vorlage je Grund - wird als Vorschlag angeboten, wenn fuer einen
# Grund noch nichts eingerichtet ist.
DEFAULT_BUNDLED: dict[str, str] = {
    "timeup": "video_timeup",
    "limit": "video_limit",
    "notimer": "video_notimer",
}

# Kleine Auswahl aus Amazons Klangbibliothek. Im Dialog ist freie Eingabe
# erlaubt, jede Kennung aus der ASK Sound Library funktioniert:
# https://developer.amazon.com/en-US/docs/alexa/custom-skills/ask-soundlibrary.html
ALEXA_SOUNDS: list[str] = [
    "bell_02",
    "amzn_sfx_doorbell_chime_01",
    "amzn_sfx_doorbell_chime_02",
    "amzn_sfx_scifi_alarm_01",
    "air_horn_03",
    "clock_01",
]

DEFAULT_DELAY = 10          # Sekunden bis zum Abschalten, nachdem die Ansage lief
MAX_DELAY = 600


def as_int(value, default: int) -> int:
    """Wie int(), aber None/'' -> default und eine echte 0 bleibt 0.

    Frueher stand hier `int(value or default)` - dadurch wurde aus einer
    eingestellten Verzoegerung von 0 Sekunden stillschweigend wieder 10.
    """
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_announce(cfg: dict | None) -> dict:
    """Bringt einen gespeicherten Ansage-Eintrag auf die aktuelle Form.

    Versteht weiterhin die alte Form aus Version <= 2.4.x
    (`{id, type, delay, tts}`) und bildet deren Vorrang-Verhalten exakt ab:
    eine gesetzte Text-Ansage schlug dort ein gesetztes Video.
    Es wird NICHTS migriert/geschrieben - die Umsetzung passiert beim Lesen.
    """
    cfg = dict(cfg or {})
    delay = as_int(cfg.get("delay"), DEFAULT_DELAY)

    src = cfg.get("src")
    if src:
        out = {"src": src, "delay": delay}
        for key in ("id", "type", "file", "tts", "sound"):
            if cfg.get(key):
                out[key] = cfg[key]
        return out

    # --- Altbestand ---------------------------------------------------------
    if cfg.get("tts"):
        return {"src": SRC_TTS, "tts": cfg["tts"], "delay": delay}
    old_id = cfg.get("id") or ""
    if old_id.startswith("media-source"):
        return {"src": SRC_MEDIA, "id": old_id,
                "type": cfg.get("type") or None, "delay": delay}
    if old_id:
        return {"src": SRC_URL, "id": old_id,
                "type": cfg.get("type") or None, "delay": delay}
    return {"src": SRC_NONE, "delay": delay}


def announce_media(cfg: dict) -> tuple[str, str | None]:
    """Liefert (URL/Medien-ID, content_type) fuer eine dateibasierte Quelle.

    Fuer `www` kann hier keine Adresse gebaut werden (dafuer wird die
    oeffentliche HTTPS-Basis von Home Assistant gebraucht) -> der Manager
    ergaenzt sie zur Laufzeit.
    """
    src = cfg.get("src")
    if src in BUNDLED_MEDIA:
        return BUNDLED_MEDIA[src]
    if src in (SRC_MEDIA, SRC_URL):
        return cfg.get("id", ""), cfg.get("type")
    return "", None


def child_id(index: int) -> str:
    return f"kind_{index}"


def child_name(index: int) -> str:
    return f"Kind {index}"


def profile_id(index: int) -> str:
    return f"profil_{index}"


def profile_name(index: int) -> str:
    return f"Profil {index}"
