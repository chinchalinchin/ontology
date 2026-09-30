"""
# Ontology: app.config.enums.asset

Asset key enumerations.
"""
# Standard Libraries
from enum import Enum

# -------------------------------- HIERARCHY ENUMERATIONS

class AssetCategories(str, Enum):
    CRAFTS          = "crafts"
    CURSORS         = "cursors"
    EFFECTS         = "effects"
    GEOGRAPHY       = "geography"
    OBJECTS         = "objects"
    SHEETS          = "sheets"
    RESOURCES       = "resources"
    TILES           = "tiles"
    WIDGETS         = "widgets"

class AssetInstances(str, Enum):
    # TILES
    BACK            = "back"
    FORE            = "fore"
    GRID            = "grid"
    # CURSORS
    EXPRESSIONS     = "expressions"
    PROJECTILES     = "projectiles"
    # EFFECTS
    PASSIVE         = "passive"
    HAZARDS         = "hazards"
    COLLECTABLES    = "collectables"
    REACTABLES      = "reactables"
    FLUIDS          = "fluids"
    # GEOGRAPHY     
    SHORELINES      = "shorelines"
    # OBJECTS
    CHESTS          = "chests"
    CRATES          = "crates"
    DOORS           = "doors"
    GATES           = "gates"
    OBSTACLES       = "obstacles"
    PLATES          = "plates"
    SIGNS           = "signs"
    RAFTS           = "rafts"
    # CRAFTS
    STRUTS          = "struts"
    DECORS          = "decors"
    FORGES          = "forges"
    DEVICES         = "devices"
    # SHEETS
    PIXIES          = "pixies"
    SPRITES         = "sprites"
    PLAYERS         = "players"
    WEAPONS         = "weapons"
    ARMOR           = "armor"
    UTILITIES       = "utilities"
    TOOLS           = "tools"
    SHIELDS         = "shields"
    # RESOURCES
    CROPS           = "crops"
    ORE             = "ore"
    # WIDGETS
    PANES           = "panes"
    BUTTONS         = "buttons"
    PAGES           = "pages"
    METERS          = "meters"
    ICONS           = "icons"

# -------------------------------- GROUPING ENUMERATIONS

class Spawnables(str, Enum):
    COLLECTABLES    = "collectables"
    COMPOSITIONS    = "compositions"
    CROPS           = "crops"
    EXPRESSIONS     = "expressions"
    HAZARDS         = "hazards"
    ORE             = "ore"
    PROJECTILES     = "projectiles"
    STRUTS          = "struts"

class Equipment(str, Enum):
    WEAPONS         = "weapons"
    ARMOR           = "armor"
    UTILITIES       = "utilities"
    TOOLS           = "tools"
    SHIELDS         = "shields"

class Groups(str, Enum):
    EQUIPMENT       = "equipment"
    SPAWNABLES      = "spawnables"

# -------------------------------- FRAME SPACE PARTITIONS
#   NOTE: These denote different ways of dividing and 
#           partitioning Asset image files.

class Lifecycles(str, Enum):
    CONTINUOUS      = "continuous"
    PERIODIC        = "periodic"
    TEMPORARY       = "temporary"

class Directions(str, Enum):
    UP              = "up"
    LEFT            = "left"
    DOWN            = "down"
    RIGHT           = "right"

class Actions(str, Enum):
    CAST            = "cast"
    THRUST          = "thrust"
    WALK            = "walk"
    SLASH           = "slash"
    SHOOT           = "shoot"
    DIE             = "die"

class Expressions(str, Enum):
    AGREEMENT       = "agreement"
    ANGER           = "anger"
    CONFUSION       = "confusion"
    CURIOSITY       = "curiosity"
    DISAGREEMENT    = "disagreement"
    LOQUACITY       = "loquacity"
    SURPRISE        = "surprise"
    TIRED           = "tired"

# -------------------------------- ASSET ID ENUMERATIONS
#   NOTE: These are required Asset IDs.

class RequiredAssets(str, Enum):
    PLAYER          = "player"

class ExpressionsPalette(str, Enum):
    BUBBLES         = "bubbles"
    BUFFS           = "buffs"

class EffectsPalette(str, Enum):
    SPLASH          = "splash"
