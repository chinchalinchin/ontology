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
    BRIDGES         = "bridges"
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
    # TODO: rename to Frequencies. update properties accordingly.
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

class Orientations(str, Enum):
    HORIZONTAL      = "horizontal"
    VERTICAL        = "vertical"
    
class Expressions(str, Enum):
    AGREEMENT       = "agreement"
    ANGER           = "anger"
    CONFUSION       = "confusion"
    CURIOSITY       = "curiosity"
    DISAGREEMENT    = "disagreement"
    LOQUACITY       = "loquacity"
    SURPRISE        = "surprise"
    TIRED           = "tired"

class Seasons(str, Enum):
    SPRING          = "spring"
    SUMMER          = "summer"
    AUTUMN          = "autumn"
    WINTER          = "winter"

class Cycles(str, Enum):
    ONSET           = "onset"
    PEAK            = "peak"
    DECLINE         = "decline"

class Lifespans(str, Enum):
    ANNUAL          = "annual"
    PERENNIAL       = "perennial"
    CENTENNIAL      = "centennial"

class AnnualStages(str, Enum):
    SPROUT          = "sprout"
    GROWTH          = "growth"
    STALK           = "stalk"
    BLOOM           = "bloom"
    STUMP           = "stump"

class PerennialStages(str, Enum):
    SAPLING         = "sapling"
    BUSH            = "bush"
    BRANCH          = "branch"
    ADULT           = "adult"
    VIBRANT         = "vibrant"
    HEALTHY         = "healthy"
    ABSCISE         = "abscise"
    SNOWCAPT        = "snowcapt"
    DYING           = "dying"
    DEAD            = "dead"
    STUMP           = "stump"

class CentennialStages(str, Enum):
    TRACE           = "trace"
    DEPOSIT         = "deposit"
    NUGGET          = "nugget"
    VEIN            = "vein"
    CRYSTAL         = "crystal"
    ALLOY           = "alloy"
    
# -------------------------------- ASSET ID ENUMERATIONS
#   NOTE: These are required Asset IDs.

class RequiredAssets(str, Enum):
    PLAYER          = "player"

class ExpressionsPalette(str, Enum):
    BUBBLES         = "bubbles"
    BUFFS           = "buffs"

class EffectsPalette(str, Enum):
    SPLASH          = "splash"
