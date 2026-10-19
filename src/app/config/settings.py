"""
# Ontology: app.config.settings

Package for global application constants.
"""
# Standard Libraries
from pathlib import Path
from typing import (
    Dict,
    Final,
    Tuple
)
# Application Libraries
from app.config.enums import (
    AssetInstances,
    # ----
    Chromatics,
    Geologics,
    Materials,
    Metallics,
    Organics,
    # -----
    Blueprints,
    Buildings,
    Columns,
    Corridors,
    # ----- 
    Seasons,
    # -----
    MultiplicationStrategies,
    Substrates,
)

# ---------------------------------------------------
# APPLICATION SETTINGS
# ---------------------------------------------------

SEPARATOR: Final[str] = "-"
"""Separator used by registry indexing to separate asset keys."""

NEW_BOARD: Final[str] = "world-01"
"""Key used to instantiate new game states."""

MIGRATOR_DELAY: Final[int] = 1
"""Delay interval in seconds for state migrations."""

EXPRESSION_TTL: Final[int] = 120
"""Number of game ticks before Expressions are garbage collected."""

LOG_LEVEL: Final[str] = "INFO"
"""Application logging verbosity level."""

SOCKET: Final[str] = "/tmp/ontology.sock"
"""TCP Socket for application telemetry."""

# ---------------------------------------------------
# ENGINE CONSTANTS
# ---------------------------------------------------

TARGET_FPS: Final[int] = 60
"""Engine target frame rate."""

TILE_HASH_SIZE: Final[int] = 32
"""Size of spatial cache hash on Board."""

PATH_RETRY_INTERVAL: Final[int] = 60
"""Number of ticks between pathfinding retry attempts."""

TELEMETRY_TICKS: Final[int] = 600
"""Number of game ticks between telemetry log flushes."""

SPIN_RATE: Final[float] = 0.002
"""Rotational step rate per tick."""

BASE_FLOW_SPEED: Final[int] = 20
"""Base Fluid vector field speed magnitude."""

FLUID_INVALIDATION_DEBOUNCE_TICKS: Final[int] = 2
"""Number of ticks before Fluid invalidation retries."""

SEASON_DURATION_SECONDS: Final[int] = 300
"""Length of a Season in seconds."""

SEASON_EVAPORATION_MODIFIERS: Final[dict[str, float]] = {
    Seasons.SPRING.value: 1.0,
    Seasons.SUMMER.value: 1.5,
    Seasons.AUTUMN.value: 1.0,
    Seasons.WINTER.value: 0.5,
}
"""Multiplicative factors scaling moisture evaporation by Board Season."""

MAX_RETENTION: Final[int] = 100
"""Maximum moisture retention percentage."""

DIFFUSION_RATE: Final[float] = 10.0
"""Factor scaling moisture based on physical proximity to Fluid Assets."""

EVAPORATION_RATE: Final[float] = 1.0
"""Multiplicative factor that scales the moisture evaporation rate"""

SUBSTRATES: Final[dict[str, int]] = {
    AssetInstances.ENVIRON.value: Substrates.ENVIRON.value,
    AssetInstances.FLUIDS.value: Substrates.FLUIDS.value,
    AssetInstances.SHORELINES.value: Substrates.SHORELINES.value,
    AssetInstances.BRIDGES.value: Substrates.BRIDGES.value
}
"""Instance-keyed map of substrate elevations."""

MATERIAL_PARTITIONS: Final[Dict[str, Tuple[str, ...]]] = {
    Materials.ORGANICS.value: tuple(m.value for m in Organics),
    Materials.GEOLOGICS.value: tuple(m.value for m in Geologics),
    Materials.METALLICS.value: tuple(m.value for m in Metallics),
    Materials.CHROMATICS.value: tuple(m.value for m in Chromatics)
}
"""Materials partitioned by genus."""

BLUEPRINT_PARTITIONS: Final[Dict[str, Tuple[str, ...]]] = {
    Blueprints.BUILDINGS.value: tuple(b.value for b in Buildings),
    Blueprints.CORRIDORS.value: tuple(b.value for b in Corridors),
    Blueprints.COLUMNS.value: tuple(b.value for b in Columns)
}
"""Blueprints partitioned by schema."""

BLUEPRINT_STRATEGIES: Final[Dict[str, str]] = {
    Blueprints.BUILDINGS.value: MultiplicationStrategies.SIMPLE.value,
    Blueprints.CORRIDORS.value: MultiplicationStrategies.SIMPLE.value,
    Blueprints.COLUMNS.value: MultiplicationStrategies.EXPANSION.value
}
"""Multiplication strategy Blueprint mapping for deploying Asset states."""
# ---------------------------------------------------
# DIRECTORY SETTINGS
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
# CLI SETTINGS
# ---------------------------------------------------

DUMP_TEMPLATES: Final[dict[str, str]] = {
    "state": ".state-dump.md.j2",
    "sdl": ".sdl-dump.md.j2",
    "registry": ".registry-dump.md.j2",
    "menus": ".menu-dump.md.j2",
}
"""Jinja2 template filenames for CLI dump outputs."""

# ---------------------------------------------------
# RENDERING SETTINGS
# ---------------------------------------------------

DIALOGUE_FONT: Final[Path] = FONT_DIR / "dialogue.tff"
"""Filesystem path to the dialogue font asset."""

TITLE_FONT: Final[Path] = FONT_DIR / "title.ttf"
"""Filesystem path to the title font asset."""

# ---------------------------------------------------
# ISL SETTINGS
# ---------------------------------------------------

ISL_TRANSLATOR: Final[str] = "lambda"
"""Evaluation strategy for ISL scripting conditions ('lambda' or 'compiler')."""