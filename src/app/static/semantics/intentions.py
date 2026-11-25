"""
@domain.logic
@app.semantics
@category.sheets
@modality.intention

# Ontology: Source - app.static.semantics.intentions

Intention semantics enumerations.
"""
# Standard Libraries
from enum import StrEnum

# -------------------------------- SPRITE STATE ENUMERATIONS

class Intentions(StrEnum):
    ATTACK          = "attack"
    ATTRACT         = "attract"
    BARTER          = "barter"
    BLOCK           = "block"
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
    USE             = "use"
    WANDER          = "wander"

class BlockingIntentions(StrEnum):
    # Intentions that must complete to release animation control
    ATTACK          = "attack"
    MINE            = "mine"

class AnimatedIntentions(StrEnum):
    # Intentions that are animated
    ATTACK          = "attack"
    MINE            = "mine"

class StaticIntentions(StrEnum):
    # Intentions that are not animated
    BARTER          = "barter"
    IDLE            = "idle"
    INTERACT        = "interact"
    MOCK            = "mock"
    SPEAK           = "speak"
    THREATEN        = "threaten"

class NavigationIntentions(StrEnum):
    # Intentions with Velocity
    FIND            = "find" 
    FOLLOW          = "follow" 
    HUNT            = "hunt" 
    ESCAPE          = "escape" 
    WANDER          = "wander"
    RETURN          = "return"

class StationaryIntentions(StrEnum):
    # Intentions with no Velocity
    BARTER          = "barter"
    BUILD           = "build"
    IDLE            = "idle"
    INTERACT        = "interact"
    MINE            = "mine"
    SPEAK           = "speak"

class Motivations(StrEnum):
    CONQUEST        = "conquest"
    LOVE            = "love"
    PROFIT          = "profit"
    REBELLION       = "rebellion"
    REVENGE         = "revenge"
    SAFETY          = "safety"
    SURVIVAL        = "survival"

class Relationships(StrEnum):
    FAMILY          = "family"
    FOE             = "foe"
    FRIEND          = "friend"
    STRANGER        = "stranger"

class Inventories(StrEnum):
    EQUIPMENT       = "equipment"
    POUCH           = "pouch"
    PACK            = "pack"
    WALLET          = "wallet"
    
# -------------------------------- GOAL ENUMERATIONS

class Goals(StrEnum):
    DOOR            = "door"
    OBJECT          = "object"
    PROPERTY        = "property"
    POSITION        = "position"
    TARGET          = "target"
    RESOURCE        = "resource"
    SUBJECT         = "subject"

class Outcomes(StrEnum):
    COMPLETE        = "complete"
    LAYERED         = "layered"
    LOST            = "lost"

class Responses(StrEnum):
    FORGET          = "forget"
    STORE           = "store"
    PUSH            = "push"
    UNWIND          = "unwind"

class Reflexes(StrEnum):
    CONFUSION       = "confusion"

class PlayerGoals(StrEnum):
    UP              = "up"
    LEFT            = "left"
    DOWN            = "down"
    RIGHT           = "right"

# ---------------------------------

class Hands(StrEnum):
    LEFT            = "left"
    RIGHT           = "right"