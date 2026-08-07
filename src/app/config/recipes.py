"""
# Ontology: Recipes

"""
# Standard Libraries
from enum import Enum

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