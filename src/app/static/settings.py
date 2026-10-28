"""
@domain.system
@app.config
@app.semantics

# Ontology: Source - app.static.settings

Package for global runtime environment settings.
"""
# Standard Libraries
import os
from pathlib import Path
from typing import Final

# Application Libraries
from app.static.semantics import Seasons

# ---------------------------------------------------
# ------------------------------ APPLICATION SETTINGS
# ---------------------------------------------------

TIME_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
"""Global time format."""

SEPARATOR: Final[str] = os.getenv("ONTOLOGY_SEPARATOR", "-")
"""Separator used by registry indexing to separate asset keys."""

NEW_BOARD: Final[str] = os.getenv("ONTOLOGY_NEW_BOARD", "world-01")
"""Key used to instantiate new game states."""

MIGRATOR_DELAY: Final[int] = int(os.getenv("ONTOLOGY_MIGRATOR_DELAY", "1"))
"""Delay interval in seconds for state migrations."""

EXPRESSION_TTL: Final[int] = int(os.getenv("ONTOLOGY_EXPRESSION_TTL", "120"))
"""Number of game ticks before Expressions are garbage collected."""

LOG_LEVEL: Final[str] = os.getenv("ONTOLOGY_LOG_LEVEL", "INFO")
"""Application logging verbosity level."""

SOCKET: Final[str] = os.getenv("ONTOLOGY_SOCKET", "/tmp/ontology.sock")
"""TCP Socket for application telemetry."""

# ---------------------------------------------------
# ----------------------------------- ENGINE SETTINGS
# ---------------------------------------------------

TARGET_FPS: Final[int] = int(os.getenv("ONTOLOGY_TARGET_FPS", "60"))
"""Engine target frame rate."""

TILE_HASH_SIZE: Final[int] = int(os.getenv("ONTOLOGY_TILE_HASH_SIZE", "32"))
"""Size of spatial cache hash on Board."""

PATH_RETRY_INTERVAL: Final[int] = int(os.getenv("ONTOLOGY_PATH_RETRY_INTERVAL", "60"))
"""Number of ticks between pathfinding retry attempts."""

TELEMETRY_TICKS: Final[int] = int(os.getenv("ONTOLOGY_TELEMETRY_TICKS", "600"))
"""Number of game ticks between telemetry log flushes."""

SPIN_RATE: Final[float] = float(os.getenv("ONTOLOGY_SPIN_RATE", "0.002"))
"""Rotational step rate per tick."""

BASE_FLOW_SPEED: Final[int] = int(os.getenv("ONTOLOGY_BASE_FLOW_SPEED", "20"))
"""Base Fluid vector field speed magnitude."""

FLUID_INVALIDATION_DEBOUNCE_TICKS: Final[int] = int(
    os.getenv("ONTOLOGY_FLUID_INVALIDATION_DEBOUNCE_TICKS", "2")
)
"""Number of ticks before Fluid invalidation retries."""

SEASON_DURATION_SECONDS: Final[int] = int(
    os.getenv("ONTOLOGY_SEASON_DURATION_SECONDS", "300")
)
"""Length of a Season in seconds."""

SEASON_EVAPORATION_MODIFIERS: Final[dict[str, float]] = {
    Seasons.SPRING.value: 1.0,
    Seasons.SUMMER.value: 1.5,
    Seasons.AUTUMN.value: 1.0,
    Seasons.WINTER.value: 0.5,
}
"""Multiplicative factors scaling moisture evaporation by Board Season."""

MAX_RETENTION: Final[int] = int(os.getenv("ONTOLOGY_MAX_RETENTION", "100"))
"""Maximum moisture retention percentage."""

DIFFUSION_RATE: Final[float] = float(os.getenv("ONTOLOGY_DIFFUSION_RATE", "10.0"))
"""Factor scaling moisture based on physical proximity to Fluid Assets."""

EVAPORATION_RATE: Final[float] = float(os.getenv("ONTOLOGY_EVAPORATION_RATE", "1.0"))
"""Multiplicative factor that scales the moisture evaporation rate."""

MOISTURE_DECAY_SIGMA: Final[float] = float(os.getenv("ONTOLOGY_MOISTURE_DECAY_SIGMA", "64.0"))
""""""

BASE_MOISTURE_POTENTIAL: Final[float] = float(os.getenv("ONTOLOGY_BASE_MOISTURE_POTENTIAL", "1.0"))
""""""
# ---------------------------------------------------
# -------------------------------- DIRECTORY SETTINGS
# ---------------------------------------------------

SRC_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent
ASSET_DIR: Final[Path] = SRC_DIR / "assets"
DATA_DIR: Final[Path] = SRC_DIR / "data"
DUMP_DIR: Final[Path] = DATA_DIR / "dumps"
LOG_DIR: Final[Path] = DATA_DIR / "logs"
CONFIG_DIR: Final[Path] = DATA_DIR / "config"
STATE_DIR: Final[Path] = DATA_DIR / "state"
TEMPLATE_DIR: Final[Path] = DATA_DIR / "templates"
SAVE_DIR: Final[Path] = DATA_DIR / "save"
FONT_DIR: Final[Path] = ASSET_DIR / "fonts"

APP_EXT: Final[str] = "main.yaml"
"""Standard application configuration filename extension."""

# ---------------------------------------------------
# -------------------------------------- CLI SETTINGS
# ---------------------------------------------------

DUMP_TEMPLATES: Final[dict[str, str]] = {
    "state": ".state-dump.md.j2",
    "sdl": ".sdl-dump.md.j2",
    "registry": ".registry-dump.md.j2",
    "menus": ".menu-dump.md.j2",
}
"""Jinja2 template filenames for CLI dump outputs."""

# ---------------------------------------------------
# -------------------------------- RENDERING SETTINGS
# ---------------------------------------------------

DIALOGUE_FONT: Final[Path] = FONT_DIR / "dialogue.tff"
"""Filesystem path to the dialogue font asset."""

TITLE_FONT: Final[Path] = FONT_DIR / "title.ttf"
"""Filesystem path to the title font asset."""

# ---------------------------------------------------
# ISL SETTINGS
# ---------------------------------------------------

TRANSLATOR_IMPLEMENTATION: Final[str] = os.getenv("ONTOLOGY_TRANSLATOR", "lambda")
"""Evaluation strategy for Transition conditions ('lambda' or 'compiler')."""

LAMBDA_SIGNATURE: Final[str] = "lambda sprite=None, sprites=None, plot=None, resource=None, calendar=None, **kwargs: {cond}"
"""Function signature for Lambda transitions."""
