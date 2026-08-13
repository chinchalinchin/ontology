"""
# Ontology: app.config.enums

"""
# Standard Libraries
from enum import Enum

class Devices(str, Enum):
    CONTROLLER  = "controller"
    KEYBOARD    = "keyboard"

# -------------------------------- ASSET ENUMERATIONS

class AssetCategories(str, Enum):
    TILES           = "tiles"
    OBJECTS         = "objects"
    EFFECTS         = "effects"
    CURSORS         = "cursors"
    SHEETS          = "sheets"
    CRAFTS          = "crafts"

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

# -------------------------------- ASSET RECIPE ENUMERATIONS

class FrameRecipe(str, Enum):
    SINGLE          = "single"
    ITERABLE        = "iterable"
    STATE           = "state"

class AnimationRecipe(str, Enum):
    TEMPORARY       = "temporary"
    PERSISTENT      = "persistent"
    BINARY          = "binary"
    STATE           = "state"

class StateRecipe(str, Enum):
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

# -------------------------------- SPRITE STATE ENUMERATIONS

class Directions(str, Enum):
    UP              = "up"
    LEFT            = "left"
    DOWN            = "down"
    RIGHT           = "right"
    # QUANTIFIERS
    ALL             = "all"

class Actions(str, Enum):
    CAST            = "cast"
    THRUST          = "thrust"
    WALK            = "walk"
    SLASH           = "slash"
    SHOOT           = "shoot"
    DIE             = "die"
    # QUANTIFIERS
    ALL             = "all"

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

# -------------------------------- PLAYER STATE ENUMERATIONS

class PlayerGoals(str, Enum):
    UP              = "up"
    LEFT            = "left"
    DOWN            = "down"
    RIGHT           = "right"

# -------------------------------- ENGINE ENUMERATIONS

class Mechanics(str, Enum):
    ANIMATION       = "animation"
    COLLISION       = "collision"
    COMBAT          = "combat"
    COMMERCE        = "commerce"
    MOTION          = "motion"
    PLAYER          = "player"
    PROJECTILE      = "projectile"
    REMOVE          = "remove"
    SPEECH          = "speech"
    SWITCH          = "switch"
    TRANSITION      = "transition"
