
from pathlib import Path

# APPLICATION CONSTANTS

## ASSET KEY COMPONENT SEPARATOR
SEPARATOR = "-"

## STATE CONSTANTS
### BINARY OBJECT STATE KEYS
ON = "activated"
OFF = "idle"

# DIRECTORY CONSTANTS

SRC_DIR = Path(__file__).resolve().parent.parent
ASSET_DIR = SRC_DIR / "assets"
DATA_DIR = SRC_DIR / "data"
STATE_DIR = DATA_DIR / "state"

APP_EXT = "main.yaml"