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
    ENVIRON         = "environ"
    CANOPY          = "canopy"
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
    DEVICES         = "devices"
    DOORS           = "doors"
    GATES           = "gates"
    OBSTACLES       = "obstacles"
    PLATES          = "plates"
    SIGNS           = "signs"
    RAFTS           = "rafts"
    # CRAFTS
    BRIDGES         = "bridges"
    CARPENTRY       = "carpentry"
    DECOR           = "decor"
    PLATFORMS       = "platforms"
    RAILINGS        = "railings"
    STRUTS          = "struts"
    STAIRS          = "stairs"
    FORGES          = "forges"
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
    TREES           = "trees"
    # WIDGETS
    PANES           = "panes"
    BUTTONS         = "buttons"
    PAGES           = "pages"
    METERS          = "meters"
    ICONS           = "icons"

# -------------------------------- GROUPING ENUMERATIONS
#   NOTE: Abstract groups of Assets.

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
#   NOTE: Different partitions of Asset image files.

class Frequencies(str, Enum):
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

class Switches(int, Enum):
    ON              = 1
    OFF             = 0

class Gauges(str, Enum):
    EMPTY           = "0"

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

class Materials(str, Enum):
    ORGANICS        = "organics"
    GEOLOGICS       = "geologics"
    METALLICS       = "metallics"

class Organics(str, Enum):
    THATCHES        = "thatches"
    WOOD            = "wood"

class Geologics(str, Enum):
    BRICK           = "brick"
    GRANITE         = "granite"
    MARBLE          = "marble"
    SANDSTONE       = "sandstone"
    SLATE           = "slate"
    STONE           = "stone"
    
class Metallics(str, Enum):
    COPPER          = "copper"
    IRON            = "iron"
    SILVER          = "silver"
    GOLD            = "gold"

class Chromatics(str, Enum):
    WHITE           = "white"
    BLUE            = "blue"
    RED             = "red"
    YELLOW          = "yellow"
    GREEN           = "green"

class Blueprints(str, Enum):
    BUILDINGS       = "buildings"

class Buildings(str, Enum):
    FLATS           = "flats"
    FLOORS          = "floors"
    HALLS           = "halls"
    PATHS           = "paths"
    ROOFS           = "roofs"
    WALLS           = "walls"

class Corridors(str, Enum):
    CARPETS         = "carpets"
    PAINTS          = "paints"
    PLANKS          = "planks"
    WALLPAPERS      = "wallpapers"

# -------------------------------- ASSET ENUMERATIONS
#   NOTE: These are required Assets.

class RequiredAssets(str, Enum):
    PLAYER          = "player"
    
class ExpressionsPalette(str, Enum):
    BUBBLES         = "bubbles"
    BUFFS           = "buffs"

class EffectsPalette(str, Enum):
    SPLASH          = "splash"
