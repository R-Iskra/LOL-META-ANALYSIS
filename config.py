# config.py

# --------------------------------------------------------------------
# Database paths
# --------------------------------------------------------------------

RAW_DB_PATH = "raw.db"
CLEAN_DB_PATH = "clean.db"
DERIVED_DB_PATH = "derived.db"

# --------------------------------------------------------------------
# Riot API rate limits
# Format: {window_seconds: request_limit}
# --------------------------------------------------------------------

RIOT_RATE_LIMITS = {
    1: 20,
    120: 100
}

# --------------------------------------------------------------------
# API client settings
# --------------------------------------------------------------------

API_TIMEOUT = 30 # seconds
API_MAX_ATTEMPTS = 5

# --------------------------------------------------------------------
# Collection settings
# --------------------------------------------------------------------

COLLECT_TIERS = (
    "CHALLENGER",
    "GRANDMASTER",
    "MASTER"
)

# Max players to collect per tier; None collects all.
COLLECT_TOP = None

# Max matches 100.
MATCHES_PER_PLAYER = 100

# Minimum patch to collect. Matches from older patches are skipped
# and deleted from the raw DB. Set to None to collect all patches.
# Example "15.15"
COLECT_MIN_PATCH = "16.9"

# --------------------------------------------------------------------
# Queue / region settings
# --------------------------------------------------------------------

LADDER_QUEUE = "RANKED_SOLO_5x5"
LADDER_REGION = "na1" # Platform region for ladder endpoints
MATCH_REGION = "americas" # Routing region for match endpoints
MATCH_QUEUE = 420 # 420 = Ranked Solo/Duo 5v5
MATCH_TYPE = "ranked"

# --------------------------------------------------------------------
# Cleaning settings
# --------------------------------------------------------------------

# Minimum game duration in seconds to include
# Set to none to include all
CLEAN_MIN_DURATION = 900

# Minimum patch to include e.g. "15.15"
# Set to none to include all
CLEAN_MIN_PATCH = "16.9"