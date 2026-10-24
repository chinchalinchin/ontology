"""
# Ontology: app.config.enums.sprites

Sprite key enumerations.
"""
# Standard Libraries
from enum import Enum

# -------------------------------- SPRITE STATE ENUMERATIONS

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