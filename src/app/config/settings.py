"""
# Ontology: app.config.settings

Package for global application constants.
"""
from pathlib import Path
import os

# ---------------------------------------------------
## ----------------------------- APPLICATION SETTINGS
### SEPARATOR: Constant used by registry indexing to
###             separate asset keys.
SEPARATOR = "-" # os.environ.setdefault()
### NEW_BOARD: 
NEW_BOARD = "world-01"
### MIGRATOR_DELAY:
MIGRATOR_DELAY = 1
### EXPRESSION_TTL: Number of game ticks before Expressions
###                 are garbage collected.
EXPRESSION_TTL = 120
### LOG_LEVEL: Application log level.
LOG_LEVEL = "INFO"
# ---------------------------------------------------
## --------------------------------- ENGINE CONSTANTS
### TARGET_FPS: Engine's target FPS.
TARGET_FPS = 60
### TILE_HASH_SIZE: Size of spatial cache on Board.
TILE_HASH_SIZE = 32
### PATH_RETRY_INTERVAL
PATH_RETRY_INTERVAL = 60
### TELEMERY_TICKS: Number of game ticks between telemetry logs.
TELEMETRY_TICKS = 600
### SPIN_RATE:
SPIN_RATE = 0.002
# ---------------------------------------------------
## ----------------------------------- STATE SETTINGS
### ON/OFF: Binary Object Keys
ON, OFF = 1, 0
### EMPTY: 
EMPTY = 0
# ---------------------------------------------------
## ------------------------------- DIRECTORY SETTINGS
### *_DIR: Application directories
SRC_DIR = Path(__file__).resolve().parent.parent.parent
ASSET_DIR = SRC_DIR / "assets"
DATA_DIR = SRC_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
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
    'registry': '.registry-dump.md.j2',
    'menus': '.menu-dump.md.j2'
}
# ---------------------------------------------------
## ------------------------------- RENDERING SETTINGS
DIALOGUE_FONT = FONT_DIR / "dialogue.tff"
TITLE_FONT = FONT_DIR / "title.ttf"
# ---------------------------------------------------
## ------------------------------------- ISL SETTINGS
# ISL_TRANSLATOR: Options: "lambda", "compiler"
ISL_TRANSLATOR = "lambda"