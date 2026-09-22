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

class Lifecycles(str, Enum):
    CONTINUOUS      = "continuous"
    PERIODIC        = "periodic"
    TEMPORARY       = "temporary"

class Reactions(str, Enum):
    BOUNCE          = "bounce"
    HINDER          = "hinder"

# -------------------------------- ASSET RECIPE ENUMERATIONS

class FrameRecipe(str, Enum):
    NONE            = "none"
    SINGLE          = "single"
    ITERABLE        = "iterable"
    FLUID           = "fluid"
    STATE           = "state"
    SPRITE          = "sprite"
    SHORELINE       = "shoreline"
    # WIDGETS
    METER           = "meter"
    TRAVERSAL       = "traversal"
    INDEX           = "index"

class AnimationRecipe(str, Enum):
    NONE            = "none"
    BINARY          = "binary"
    STATE           = "state"
    SPRITE          = "sprite"
    METER           = "meter"
    TRAVERSAL       = "traversal"
    LIFECYCLE       = "lifecycle"

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
    SPEAK           = "speak"

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

class EffectsPalette(str, Enum):
    SPLASH          = "splash"

class Inventories(str, Enum):
    EQUIPMENT       = "equipment"
    POUCH           = "pouch"
    PACK            = "pack"
    WALLET          = "wallet"
    
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
    FLUID           = "fluid"
    INTERACTION     = "interaction"
    MOTION          = "motion"
    MENU            = "menu"
    NAVIGATION      = "navigation"
    PLAYER          = "player"
    PLOT            = "plot"
    PROJECTILE      = "projectile"
    REMOVE          = "remove"
    SOCIAL          = "social"
    SWITCH          = "switch"
    TRANSITION      = "transition"

class Configurations(str, Enum):
    ACTIONS         = "actions"
    COMPOSITIONS    = "compositions"
    INTENTIONS      = "intentions"
    LIBRARY         = "library"
    MAPPINGS        = "mappings"
    MECHANICS       = "mechanics"
    MENUS           = "menus"
    PLOTS           = "plots"
    RECIPES         = "recipes"

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

class Shortcuts(str, Enum):
    COMPOSITIONS    = "compositions"
    GIZMOS          = "gizmos"
    PLOTS           = "plots"

class ChannelTypes(int, Enum):
    TINT            = 0
    SUBMERGE        = 1

# -------------------------------- WIDGET ENUMERATIONS

class Controllers(str, Enum):
    DISPLAY         = "display"
    INVENTORY       = "inventory"
    LOAD            = "load"
    MAIN            = "main"
    OPTIONS         = "options"
    PAUSE           = "pause"
    SCROLL          = "scroll"
    
class Layouts(str, Enum):
    DOCK            = "dock"
    STACK           = "stack"
    OVERLAY         = "overlay"

class Alignments(str, Enum):
    START           = "start"
    END             = "end"
    CENTER          = "center"

class Bindings(str, Enum):
    APERTURE        = "aperture"
    COLLECTION      = "collection"
    ICON            = "icon"
    LIBRARY         = "library"
    METER           = "meter"
    SELECT          = "select"
    TEXT            = "text"

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
    LOAD            = "load"
    MAIN            = "main"
    OPTIONS         = "options"
    PAUSE           = "pause"
    TEXT            = "text"
    TRADE           = "trade"
    VIEW            = "view"

class Selections(str, Enum):
    LOAD            = "load"
    MENU            = "menu"
    NEW             = "new"
    SAVE            = "save"
    SCROLLUP        = "scrollup"
    SCROLLDOWN      = "scrolldown"
    SLOT            = "slot"
    QUIT            = "quit"

class Statuses(str, Enum):
    ACTIVE          = "active"
    IDLE            = "idle"
    SELECTED        = "selected"
    DISABLED        = "disabled"

class Fonts(str, Enum):
    DIALOGUE        = "dialogue"
    MENU            = "menu"
    TITLE           = "title"
