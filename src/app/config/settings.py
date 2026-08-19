"""
# Ontology: app.config.settings

Package for global application constants.
"""
from pathlib import Path

## APPLICATION SETTINGS
SEPARATOR = "-"
## ENGINE CONSTANTS
TARGET_FPS = 60
TILE_HASH_SIZE = 32
## STATE SETTINGS
### BINARY OBJECT STATE KEYS
ON = 1
OFF = 0
## DIRECTORY SETTINGS
SRC_DIR = Path(__file__).resolve().parent.parent.parent
ASSET_DIR = SRC_DIR / "assets"
DATA_DIR = SRC_DIR / "data"
CONFIG_DIR = DATA_DIR / "config"
STATE_DIR = DATA_DIR / "state"
TEMPLATE_DIR = DATA_DIR / "templates"
### APPLICATION INDEX FILENAME
APP_EXT = "main.yaml"
## CLI SETTINGS
### DEBUG DUMP TEMPLATES
DUMP_TEMPLATES = {
    'state': ".state-dump.md.j2",
    'sdl': ".sdl-dump.md.j2"
}