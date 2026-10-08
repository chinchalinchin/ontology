"""
# Ontology: app.config.enums.recipes

Recipe key enumerations
"""
# Standard Libraries
from enum import Enum


# -------------------------------- ASSET RECIPE ENUMERATIONS
#   NOTE: These are required Recipe configuration keys

class FrameRecipe(str, Enum):
    CARDINAL        = "cardinal"
    FLUID           = "fluid"
    INDEX           = "index"
    ITERABLE        = "iterable"
    METER           = "meter"
    NONE            = "none"
    ORIENTED        = "oriented"
    SINGLE          = "single"
    SEASONAL        = "seasonal"
    SPRITE          = "sprite"
    STAGE           = "stage"
    STATE           = "state"
    TRAVERSAL       = "traversal"
    
class AnimationRecipe(str, Enum):
    NONE            = "none"
    BINARY          = "binary"
    STATE           = "state"
    SPRITE          = "sprite"
    METER           = "meter"
    TRAVERSAL       = "traversal"
    LIFECYCLE       = "lifecycle"

class HitboxRecipe(str, Enum):
    STATIC          = "static"
    DYNAMIC         = "dynamic"
    STAGE           = "stage"
    ATTACK          = "attack"
    NONE            = "none"