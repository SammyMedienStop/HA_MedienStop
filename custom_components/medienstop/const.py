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


def child_id(index: int) -> str:
    return f"kind_{index}"


def child_name(index: int) -> str:
    return f"Kind {index}"


def profile_id(index: int) -> str:
    return f"profil_{index}"


def profile_name(index: int) -> str:
    return f"Profil {index}"
