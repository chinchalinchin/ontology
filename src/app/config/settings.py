"""
# Ontology: app.config.settings

Package for global application constants.
"""
# Standard Libraries
from pathlib import Path
from typing import (
    Final,
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
    Enclosures,
    Inclines,
    Orientations,
    Directions,
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
    # ---------------------------------- INSTANCE LEVEL SUBSTRATES
    AssetInstances.ENVIRON.value: Substrates.ENVIRON.value,
    AssetInstances.FLUIDS.value: Substrates.FLUIDS.value,
    AssetInstances.SHORELINES.value: Substrates.SURFACES.value,
    AssetInstances.BRIDGES.value: Substrates.OVERLAYS.value,
    AssetInstances.STAIRS.value: Substrates.OVERLAYS.value,
    # ---------------------------------- BLUEPRINT LEVEL SUBTRACTS
    Buildings.FLOORS.value: Substrates.SURFACES.value, 
    Buildings.PATHS.value: Substrates.SURFACES.value,
    Buildings.FLATS.value: Substrates.SURFACES.value,
    Corridors.SOLIDS.value: Substrates.OVERLAYS.value,
    Corridors.STRIPES.value: Substrates.OVERLAYS.value,
    Corridors.DESIGNS.value: Substrates.OVERLAYS.value
}
"""Instance-keyed map of substrate elevations."""

MATERIAL_PARTITIONS: Final[dict[str, tuple[str, ...]]] = {
    Materials.ORGANICS.value: tuple(m.value for m in Organics),
    Materials.GEOLOGICS.value: tuple(m.value for m in Geologics),
    Materials.METALLICS.value: tuple(m.value for m in Metallics),
    Materials.CHROMATICS.value: tuple(m.value for m in Chromatics)
}
"""Materials partitioned by genus."""

BLUEPRINT_PARTITIONS: Final[dict[str, tuple[str, ...]]] = {
    Blueprints.BUILDINGS.value: tuple(b.value for b in Buildings),
    Blueprints.CORRIDORS.value: tuple(b.value for b in Corridors),
    Blueprints.COLUMNS.value: tuple(b.value for b in Columns),
    Blueprints.DIRECTIONS.value: tuple(b.vlaue for b in Directions),
    Blueprints.ENCLOSURES.value: tuple(b.value for b in Enclosures),
    Blueprints.INCLINES.value: tuple(b.value for b in Inclines),
    Blueprints.ORIENTATIONS.value: tuple(b.value for b in Orientations)

}
"""Blueprints partitioned by schema."""

BLUEPRINT_STRATEGIES: Final[dict[str, str]] = {
    Blueprints.BUILDINGS.value: MultiplicationStrategies.SIMPLE.value,
    Blueprints.CORRIDORS.value: MultiplicationStrategies.SIMPLE.value,
    Blueprints.COLUMNS.value: MultiplicationStrategies.EXPANSION.value,
    Blueprints.DIRECTIONS.value: None,
    Blueprints.ENCLOSURES.value: MultiplicationStrategies.PERIMETER.value,
    Blueprints.INCLINES.value: MultiplicationStrategies.SIMPLE.value,
    Blueprints.ORIENTATIONS.value: MultiplicationStrategies.ORIENTED.value
}
"""Multiplication strategy Blueprint mapping for deploying Asset states."""

OBSTACLE_BLUEPRINTS: Final[frozenset[str]] = frozenset({
    Buildings.WALLS.value,
    Buildings.HALLS.value,
    Columns.BASES.value,
    Enclosures.NORTH.value,
    Enclosures.EAST.value,
    Enclosures.SOUTH.value,
    Enclosures.WEST.value,
    Orientations.HORIZONTAL.value, 
    Orientations.VERTICAL.value,
    Inclines.UP.value,
    Inclines.LEFT.value,
    Inclines.RIGHT.value
})
"""Blueprints for constructing obstacles."""

SUBSTRATE_BLUEPRINTS: Final[frozenset[str]] = frozenset({
    Buildings.FLOORS.value,
    Buildings.PATHS.value,
    Corridors.SOLIDS.value,
    Corridors.STRIPES.value,
    Corridors.DESIGNS.value
})
"""Blueprints for rendering ground-level decals and decorations"""
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