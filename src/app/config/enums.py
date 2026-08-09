"""
# Ontology: Hierarchy

"""
# Standard Libraries
from enum import Enum


class Devices(str, Enum):
    CONTROLLER  = "controller"
    KEYBOARD    = "keyboard"

# -------------------------------- ASSET ENUMERATIONS

class AssetCategories(str, Enum):
    """
    """
    TILES           = "tiles"
    OBJECTS         = "objects"
    EFFECTS         = "effects"
    CURSORS         = "cursors"
    SHEETS          = "sheets"
    CRAFTS          = "crafts"

class AssetInstances(str, Enum):
    """
    """
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

# -------------------------------- ASSET RECIPE ENUMERATIONS

class FrameRecipe(str, Enum):
    """
    """
    SINGLE          = "single"
    ITERABLE        = "iterable"
    STATE           = "state"

class AnimationRecipe(str, Enum):
    """
    """
    TEMPORARY       = "temporary"
    PERSISTENT      = "persistent"
    BINARY          = "binary"
    STATE           = "state"

class StateRecipe(str, Enum):
    """
    """
    SPRITE          = "sprite"
    SWITCH          = "switch"
    DOOR            = "door"
    POSITIONAL      = "positional"
    PROPERTY        = "property"
    CONTAINER       = "container"
    ANIMATOR        = "animator"
    METRIC          = "metric"
    MULTIPLIER      = "multiplier"

# -------------------------------- SPRITE STATE ENUMERATIONS

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

class Extensions(str, Enum):
    INTERACT        = "interact"
    SPEAK           = "speak"
    SPRINT          = "sprint"
    TRADE           = "trade"

class Dispositions(str, Enum):
    ATTACK          = "attack"
    ATTRACT         = "attract"
    BARTER          = "barter"
    COMMUNICATE     = "communicate"
    ESCAPE          = "escape"
    ENGAGE          = "engage"
    FIND            = "find"
    FOLLOW          = "follow"
    IDLE            = "idle"
    INTERACT        = "interact"
    SCAVENGE        = "scavenge"
    MOCK            = "mock"
    RECOIL          = "recoil"
    RETURN          = "return"
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
