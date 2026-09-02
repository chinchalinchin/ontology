"""
# Ontology: app.config.settings

Package for global application constants.
"""
from pathlib import Path

# ---------------------------------------------------
## ----------------------------- APPLICATION SETTINGS
### SEPARATOR: Constant used by registry indexing to
###             separate asset keys.
SEPARATOR = "-"
NEW_BOARD = "world-01"
# ---------------------------------------------------
## --------------------------------- ENGINE CONSTANTS
### TARGET_FPS: Engine's target FPS.
TARGET_FPS = 60
### TILE_HASH_SIZE: Size of spatial cache on Board.
TILE_HASH_SIZE = 32
# ---------------------------------------------------
## ----------------------------------- STATE SETTINGS
### ON/OFF: Binary Object Keys
ON = 1
OFF = 0
EMPTY = 0
# ---------------------------------------------------
## ------------------------------- DIRECTORY SETTINGS
### *_DIR: Application directories
SRC_DIR = Path(__file__).resolve().parent.parent.parent
ASSET_DIR = SRC_DIR / "assets"
DATA_DIR = SRC_DIR / "data"
CONFIG_DIR = DATA_DIR / "config"
STATE_DIR = DATA_DIR / "state"
TEMPLATE_DIR = DATA_DIR / "templates"
SAVE_DIR =  DATA_DIR / 'save'
FONT_DIR = ASSET_DIR / "fonts" 
### APP_EXT: Common Application filename extension
APP_EXT = "main.yaml"
# ---------------------------------------------------
## ------------------------------------- CLI SETTINGS
### DUMP_TEMPLATES: Templates for CLI dumps
DUMP_TEMPLATES = {
    'state': ".state-dump.md.j2",
    'sdl': ".sdl-dump.md.j2",
    'registry': '.registry-dump.md.j2'
}
# ---------------------------------------------------
## ------------------------------- RENDERING SETTINGS
DIALOGUE_FONT = FONT_DIR / "dialogue.tff"
TITLE_FONT = FONT_DIR / "title.ttf"
# ---------------------------------------------------
## ------------------------------------- ISL SETTINGS
# ISL_TRANSLATOR: Options: "lambda", "compiler"
ISL_TRANSLATOR: str = "lambda"