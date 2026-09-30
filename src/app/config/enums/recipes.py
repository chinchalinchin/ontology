"""
# Ontology: app.config.enums.recipes

Recipe key enumerations
"""
# Standard Libraries
from enum import Enum


# -------------------------------- ASSET RECIPE ENUMERATIONS
#   NOTE: These are required Recipe configuration keys

class FrameRecipe(str, Enum):
    NONE            = "none"
    SINGLE          = "single"
    ITERABLE        = "iterable"
    FLUID           = "fluid"
    STATE           = "state"
    SPRITE          = "sprite"
    CARDINAL        = "cardinal"
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