"""
# Ontology: app.config.settings

Package for global application constants.
"""
from pathlib import Path

# APPLICATION SETTINGS

## ASSET KEY COMPONENT SEPARATOR
SEPARATOR = "-"

## STATE CONSTANTS
### BINARY OBJECT STATE KEYS
ON = 1
OFF = 0

# DIRECTORY CONSTANTS

SRC_DIR = Path(__file__).resolve().parent.parent.parent
ASSET_DIR = SRC_DIR / "assets"
DATA_DIR = SRC_DIR / "data"
CONFIG_DIR = DATA_DIR / "config"
STATE_DIR = DATA_DIR / "state"
TEMPLATE_DIR = DATA_DIR / "templates"

APP_EXT = "main.yaml"

DUMP_TEMPLATES = {
    'state': ".state-dump.md.j2",
    'sdl': ".sdl-dump.md.j2"
}