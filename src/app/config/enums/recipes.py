"""
# Ontology: app.config.enums.recipes

Recipe key enumerations
"""
# Standard Libraries
from enum import Enum


# -------------------------------- ASSET RECIPE ENUMERATIONS
#   NOTE: These are required Recipe configuration keys

class FrameRecipe(str, Enum):
    BINARY          = "binary"
    CARDINAL        = "cardinal"
    DIRECTED        = "directed"
    FLUID           = "fluid"
    INDEX           = "index"
    ITERABLE        = "iterable"
    MATERIAL        = "material"
    METER           = "meter"
    NONE            = "none"
    OBJECT          = "object"
    ORIENTED        = "oriented"
    SINGLE          = "single"
    SEASONAL        = "seasonal"
    SPRITE          = "sprite"
    STAGE           = "stage"
    STATE           = "state"
    TRAVERSAL       = "traversal"
    
class AnimationRecipe(str, Enum):
    NONE            = "none"
    STATE           = "state"
    SPRITE          = "sprite"
    METER           = "meter"
    TRAVERSAL       = "traversal"
    FREQUENCY       = "frequency"

class HitboxRecipe(str, Enum):
    ATTACK          = "attack"
    DIRECTED        = "directed"
    DYNAMIC         = "dynamic"
    ELEVATED        = "elevated"
    LAYERED         = "layered"
    MATERIAL        = "material"
    NONE            = "none"
    ORIENTED        = "oriented"
    STAGE           = "stage"
    STATIC          = "static"
    SWITCH          = "switch"
