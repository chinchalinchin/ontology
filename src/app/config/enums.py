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
class RequiredAssets(str, Enum):
    PLAYER          = "player"

class AssetCategories(str, Enum):
    CRAFTS          = "crafts"
    CURSORS         = "cursors"
    EFFECTS         = "effects"
    OBJECTS         = "objects"
    SHEETS          = "sheets"
    RESOURCES       = "resources"
    TILES           = "tiles"
    WIDGETS         = "widgets"

class AssetInstances(str, Enum):
    # TILES
    BACK            = "back"
    FORE            = "fore"
    # CURSORS
    EXPRESSIONS     = "expressions"
    PROJECTILES     = "projectiles"
    # EFFECTS
    PERSISTENT      = "persistent"
    TEMPORARY       = "temporary"
    # OBJECTS
    CHESTS          = "chests"
    CRATES          = "crates"
    DOORS           = "doors"
    GATES           = "gates"
    PLATES          = "plates"
    SIGNS           = "signs"
    # CRAFTS
    STRUTS          = "struts"
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

class Spawnables(str, Enum):
    TEMPORARY       = "temporary"
    PROJECTILES     = "projectiles"
    STRUTS          = "struts"
    COMPOSITIONS    = "compositions"
    CROPS           = "crops"
    ORE             = "ore"

class Equipment(str, Enum):
    WEAPONS         = "weapons"
    ARMOR           = "armor"
    UTILITIES       = "utilities"
    TOOLS           = "tools"
    SHIELDS         = "shields"

class Groups(str, Enum):
    EQUIPMENT       = "equipment"
    SPAWNABLES      = "spawnables"

class Shortcuts(str, Enum):
    COMPOSITIONS    = "compositions"
    PLOTS           = "plots"

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
    DIALOGUE        = "dialogue"
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

class BlockingIntentions(str, Enum):
    # Intentions that must complete to release animation control
    ATTACK          = "attack"
    MINE            = "mine"

class AnimatedIntentions(str, Enum):
    # Intentions that are animated
    ATTACK          = "attack"
    MINE            = "mine"

class StaticIntentions(str, Enum):
    # Intentions that are not animated
    BARTER          = "barter"
    IDLE            = "idle"
    INTERACT        = "interact"
    MOCK            = "mock"
    SPEAK           = "speak"
    THREATEN        = "threaten"

class NavigationIntentions(str, Enum):
    # Intentions with Velocity
    FIND            = "find" 
    FOLLOW          = "follow" 
    HUNT            = "hunt" 
    ESCAPE          = "escape" 
    WANDER          = "wander"
    RETURN          = "return"

class StationaryIntentions(str, Enum):
    # Intentions with no Velocity
    BARTER          = "barter"
    BUILD           = "build"
    IDLE            = "idle"
    INTERACT        = "interact"
    MINE            = "mine"
    SPEAK           = "build"

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

class ExpressionsPalette(str, Enum):
    BUBBLES         = "bubbles"
    BUFFS           = "buffs"

# -------------------------------- GOAL ENUMERATIONS

class Goals(str, Enum):
    OBJECT          = "object"
    PROPERTY        = "property"
    POSITION        = "position"
    TARGET          = "target"
    SUBJECT         = "subject"

class PlayerGoals(str, Enum):
    UP              = "up"
    LEFT            = "left"
    DOWN            = "down"
    RIGHT           = "right"

# -------------------------------- ENGINE ENUMERATIONS

class Mechanics(str, Enum):
    ANIMATION       = "animation"
    COGNITION       = "cognition"
    COLLISION       = "collision"
    COMBAT          = "combat"
    INTERACTION     = "interaction"
    MOTION          = "motion"
    MENU            = "menu"
    PLAYER          = "player"
    PLOT            = "plot"
    PROJECTILE      = "projectile"
    REMOVE          = "remove"
    SOCIAL          = "social"
    SWITCH          = "switch"
    TRANSITION      = "transition"

class Configurations(str, Enum):
    ACTIONS         = "actions"
    INTENTIONS      = "intentions"
    MAPPINGS        = "mappings"
    MECHANICS       = "mechanics"
    MENUS           = "menus"
    RECIPES         = "recipes"
    COMPOSITIONS    = "compositions"

class MotiveAssets(str, Enum):
    PLAYERS         = "players"
    SPRITES         = "sprites"

class FrictiveAssets(str, Enum):
    CRATES          = "crates"

class InertAssets(str, Enum):
    PROJECTILES     = "projectiles"

class Translators(str, Enum):
    COMPILER        = "compiler"
    LAMBDA          = "lambda"
    
# -------------------------------- WIDGET ENUMERATIONS

class Controllers(str, Enum):
    SCROLL          = "scroll"
    DISPLAY         = "display"
    MAIN            = "main"
    LOAD            = "load"
    
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
    LOAD            = "load"

class Selections(str, Enum):
    SCROLLUP        = "scrollup"
    SCROLLDOWN      = "scrolldown"
    NEW             = "new"
    LOAD            = "load"
    MENU            = "menu"

class Statuses(str, Enum):
    ACTIVE          = "active"
    IDLE            = "idle"
    SELECTED        = "selected"
    DISABLED        = "disabled"