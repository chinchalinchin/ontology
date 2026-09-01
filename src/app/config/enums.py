"""
# Ontology: app.config.enums

"""
# Standard Libraries
from enum import Enum

class Devices(str, Enum):
    CONTROLLER      = "controller"
    KEYBOARD        = "keyboard"

class DeviceContexts(str, Enum):
    WORLD           = "world"
    MENU            = "menu"
    
# -------------------------------- ASSET ENUMERATIONS

class AssetCategories(str, Enum):
    CRAFTS          = "crafts"
    CURSORS         = "cursors"
    EFFECTS         = "effects"
    OBJECTS         = "objects"
    SHEETS          = "sheets"
    TILES           = "tiles"
    WIDGETS         = "widgets"

class AssetInstances(str, Enum):
    BACK            = "back"
    FORE            = "fore"
    EXPRESSIONS     = "expressions"
    PROJECTILES     = "projectiles"
    PERSISTENT      = "persistent"
    TEMPORARY       = "temporary"
    CHESTS          = "chests"
    CRATES          = "crates"
    DOORS           = "doors"
    GATES           = "gates"
    PLATES          = "plates"
    STRUTS          = "struts"
    PIXIES          = "pixies"
    SPRITES         = "sprites"
    PLAYERS         = "players"
    PANES           = "panes"
    BUTTONS         = "buttons"
    PAGES           = "pages"
    METERS          = "meters"
    ICONS           = "icons"
    WEAPONS         = "weapons"
    ARMOR           = "armor"
    UTILITIES       = "utilities"
    TOOLS           = "tools"
    SHIELDS         = "shields"

class Equipment(str, Enum):
    WEAPONS         = "weapons"
    ARMOR           = "armor"
    UTILITIES       = "utilities"
    TOOLS           = "tools"
    SHIELDS         = "shields"

class Shortcuts(str, Enum):
    COMPOSITIONS    = "compositions"
# -------------------------------- ASSET RECIPE ENUMERATIONS

class FrameRecipe(str, Enum):
    NONE            = "none"
    SINGLE          = "single"
    ITERABLE        = "iterable"
    STATE           = "state"
    SPRITE          = "sprite"
    METER           = "meter"
    TRAVERSAL       = "traversal"
    INDEX           = "index"

class AnimationRecipe(str, Enum):
    NONE            = "none"
    TEMPORARY       = "temporary"
    PERSISTENT      = "persistent"
    BINARY          = "binary"
    STATE           = "state"
    METER           = "meter"
    TRAVERSAL       = "traversal"

class StateRecipe(str, Enum):
    NONE            = "none"
    # ASSET STATES
    SPRITE          = "sprite"
    SWITCH          = "switch"
    DOOR            = "door"
    POSITIONAL      = "positional"
    PROPERTY        = "property"
    CONTAINER       = "container"
    ANIMATOR        = "animator"
    METRIC          = "metric"
    MULTIPLIER      = "multiplier"
    PLAYER          = "player"
    # WIDGET STATES
    TRAVERSAL       = "traversal"
    METER           = "meter"
    DISPLAY         = "display"
    PANE            = "pane"
    ICON            = "icon"

# -------------------------------- SPRITE STATE ENUMERATIONS

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

class Intentions(str, Enum):
    ATTACK          = "attack"
    ATTRACT         = "attract"
    BARTER          = "barter"
    BUILD           = "build"
    ESCAPE          = "escape"
    FIND            = "find"
    FOLLOW          = "follow"
    HUNT            = "hunt"
    IDLE            = "idle"
    INTERACT        = "interact"
    MINE            = "mine"
    MOCK            = "mock"
    RETURN          = "return"
    SCAVENGE        = "scavenge"
    SPEAK           = "speak"
    SPRINT          = "sprint"
    THREATEN        = "threaten"
    WANDER          = "wander"

class Motivations(str, Enum):
    CONQUEST        = "conquest"
    LOVE            = "love"
    PROFIT          = "profit"
    REBELLION       = "rebellion"
    REVENGE         = "revenge"
    SAFETY          = "safety"
    SURVIVAL        = "survival"

class Relationships(str, Enum):
    FAMILY          = "family"
    FOE             = "foe"
    FRIEND          = "friend"
    STRANGER        = "stranger"

# -------------------------------- GOAL ENUMERATIONS

class GoalCategories(str, Enum):
    ASSET           = "asset"
    LOOT            = "loot"
    WEALTH          = "wealth"
    PROPERTY        = "property"
    POSITION        = "position"
    SPRITE          = "sprite"
    
class PlayerGoals(str, Enum):
    UP              = "up"
    LEFT            = "left"
    DOWN            = "down"
    RIGHT           = "right"

class PlayerIntentions(str, Enum):
    INVENTORY       = "inventory"
    PAUSE           = "pause"

# -------------------------------- ENGINE ENUMERATIONS

class Mechanics(str, Enum):
    ANIMATION       = "animation"
    COGNITION       = "cognition"
    COLLISION       = "collision"
    COMBAT          = "combat"
    COMMERCE        = "commerce"
    INTERACTION     = "interaction"
    MOTION          = "motion"
    MENU            = "menu"
    PLAYER          = "player"
    PROJECTILE      = "projectile"
    REMOVE          = "remove"
    SPEECH          = "speech"
    SWITCH          = "switch"
    TRANSITION      = "transition"

class Configurations(str, Enum):
    ACTIONS         = "actions"
    INTENTIONS      = "intentions"
    MAPPINGS        = "mappings"
    MECHANICS       = "mechanics"
    MENUS           = "menus"
    RECIPES         = "recipes"
    SCRIPTS         = "scripts"
    COMPOSITIONS    = "compositions"

class Spawnables(str, Enum):
    TEMPORARY       = "temporary"
    PROJECTILES     = "projectiles"
    STRUTS          = "struts"
    COMPOSITIONS    = "compositions"

class Groups(str, Enum):
    CONFIGURATIONS  = "configurations"
    EQUIPMENT       = "equipment"
    SPAWNABLES      = "spawnables"

class MotiveAssets(str, Enum):
    PLAYERS         = "players"
    SPRITES         = "sprites"

class FrictiveAssets(str, Enum):
    CRATES          = "crates"

class InertAssets(str, Enum):
    PROJECTILES     = "projectiles"

class BlockingIntentions(str, Enum):
    ATTACK          = "attack"
    MINE            = "mine"

class AnimatedIntentions(str, Enum):
    # TODO: possibly redundant with respect to BlockingIntentions
    ATTACK          = "attack"
    MINE            = "mine"

# -------------------------------- ISL ENUMERATIONS

class MineableAssets(str, Enum):
    RESOURCES       = "resources"
# -------------------------------- WIDGET ENUMERATIONS

class Controllers(str, Enum):
    SCROLL          = "scroll"
    DISPLAY         = "display"
    
class Layouts(str, Enum):
    DOCK            = "dock"
    STACK           = "stack"
    OVERLAY         = "overlay"

class Alignments(str, Enum):
    START           = "start"
    END             = "end"
    CENTER          = "center"

class Traversal(str, Enum):
    NORTH           = "north"
    SOUTH           = "south"
    EAST            = "east"
    WEST            = "west"

class Interactions(str, Enum):
    SELECT          = "select"
    CANCEL          = "cancel"
    PAUSE           = "pause"

class Menus(str, Enum):
    DIALOGUE        = "dialogue"
    INVENTORY       = "inventory"
    MAIN            = "main"
    PAUSE           = "pause"
    TEXT            = "text"
    TRADE           = "trade"
    VIEW            = "view"

class Selections(str, Enum):
    SCROLLUP        = "scrollup"
    SCROLLDOWN      = "scrolldown"

class Selectors(str, Enum):
    SCROLL          = "scroll"
    SLOT            = "slot"

class Statuses(str, Enum):
    ACTIVE          = "active"
    IDLE            = "idle"
    SELECTED        = "selected"
    DISABLED        = "disabled"