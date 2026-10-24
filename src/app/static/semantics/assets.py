"""
@app.semantics
@app.core

# Ontology: Source - app.config.enums.asset

Enumeration of Asset semantics.
"""
# Standard Libraries
from enum import Enum

# -------------------------------------------------------
# -------------------------------- HIERARCHY ENUMERATIONS
# -------------------------------------------------------

class AssetCategories(str, Enum):
    """Enumeration of Asset Categories."""
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
    """Enumeration of Asset Instances."""
    # TILES
    CANOPY          = "canopy"
    ENVIRON         = "environ"
    GRID            = "grid"
    # CURSORS
    EXPRESSIONS     = "expressions"
    PROJECTILES     = "projectiles"
    # EFFECTS
    COLLECTABLES    = "collectables"
    FLUIDS          = "fluids"
    HAZARDS         = "hazards"
    PASSIVE         = "passive"
    REACTABLES      = "reactables"
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
    DECOR           = "decor"
    PLATFORMS       = "platforms"
    STRUTS          = "struts"
    STAIRS          = "stairs"
    FORGES          = "forges"
    # SHEETS
    PIXIES          = "pixies"
    PLAYERS         = "players"
    SPRITES         = "sprites"
    ## SHEETS: EQUIPMENT
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
    BUTTONS         = "buttons"
    ICONS           = "icons"
    METERS          = "meters"
    PAGES           = "pages"
    PANES           = "panes"

# -------------------------------------------------------
# --------------------------------- GROUPING ENUMERATIONS
# -------------------------------------------------------
#   NOTE: Abstract groups of Assets.

class Spawnables(str, Enum):
    """Enumeration of Spawnable Assets."""
    COLLECTABLES    = "collectables"
    COMPOSITIONS    = "compositions"
    CROPS           = "crops"
    EXPRESSIONS     = "expressions"
    HAZARDS         = "hazards"
    ORE             = "ore"
    PROJECTILES     = "projectiles"
    STRUTS          = "struts"

class Equipment(str, Enum):
    """Enumeration of Equipment Sheets."""
    ARMOR           = "armor"
    SHIELDS         = "shields"
    TOOLS           = "tools"
    UTILITIES       = "utilities"
    WEAPONS         = "weapons"

class Groups(str, Enum):
    """Enumeration of Asset Groups."""
    EQUIPMENT       = "equipment"
    SPAWNABLES      = "spawnables"

# -------------------------------------------------------
# -------------------------------- FRAME SPACE PARTITIONS
# -------------------------------------------------------
#   NOTE: Different partitions of Asset image files.
#           Order matters.

class Frequencies(str, Enum):
    """Enumeration of Asset Frequencies."""
    CONTINUOUS      = "continuous"
    PERIODIC        = "periodic"
    TEMPORARY       = "temporary"

class Directions(str, Enum):
    """Enumeration of Asset Directions."""
    UP              = "up"
    LEFT            = "left"
    DOWN            = "down"
    RIGHT           = "right"

class Actions(str, Enum):
    """Enumeration of Asset Actions."""
    CAST            = "cast"
    THRUST          = "thrust"
    WALK            = "walk"
    SLASH           = "slash"
    SHOOT           = "shoot"
    DIE             = "die"

class Orientations(str, Enum):
    """Enumeration of Asset Orientations."""
    HORIZONTAL      = "horizontal"
    VERTICAL        = "vertical"

class Switches(int, Enum):
    """Enumeration of Asset Switch States."""
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
    CERAMICS        = "ceramics"
    CHROMATICS      = "chromatics"
    ORGANICS        = "organics"
    GEOLOGICS       = "geologics"
    METALLICS       = "metallics"

class Organics(str, Enum):
    COTTON          = "cotton"
    THATCHES        = "thatches"
    WOOD            = "wood"

class Ceramics(str, Enum):
    CLAY            = "clay"

class Geologics(str, Enum):
    LIMESTONE       = "limestone"
    FELDSPAR        = "feldspar"
    GRANITE         = "granite"
    MARBLE          = "marble"
    
class Metallics(str, Enum):
    COPPER          = "copper"
    IRON            = "iron"
    GOLD            = "gold"

class Chromatics(str, Enum):
    NEUTRAL         = "neutral"
    BLUE            = "blue"
    RED             = "red"
    YELLOW          = "yellow"
    GREEN           = "green"

class Blueprints(str, Enum):
    BUILDINGS       = "buildings"
    CORRIDORS       = "corridors"
    COLUMNS         = "columns"
    DIRECTIONS      = "directions"
    ENCLOSURES      = "enclosures"
    ORIENTATIONS    = "orientations"
    INCLINES        = "inclines"

class Buildings(str, Enum):
    FLOORS          = "floors"
    WALLS           = "walls"
    FLATS           = "flats"
    ROOFS           = "roofs"
    PATHS           = "paths"
    HALLS           = "halls"

class Corridors(str, Enum):
    SOLIDS          = "solids"
    STRIPES         = "stripes"
    DESIGNS         = "designs"

class Columns(str, Enum):
    CROWNS          = "crowns"
    SHAFTS          = "shafts"
    BASES           = "bases"

class Enclosures(str, Enum):
    NORTH           = "north"
    EAST            = "east"
    SOUTH           = "south"
    WEST            = "west"

class Inclines(str, Enum):
    UP              = "up"
    LEFT            = "left"
    RIGHT           = "right"
    
# -------------------------------------------------------
# ------------------------------------ ASSET ENUMERATIONS
# -------------------------------------------------------
#   NOTE: These are required Assets.

class RequiredAssets(str, Enum):
    PLAYER          = "player"
    
class ExpressionsPalette(str, Enum):
    BUBBLES         = "bubbles"
    BUFFS           = "buffs"

class EffectsPalette(str, Enum):
    SPLASH          = "splash"
