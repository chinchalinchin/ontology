"""
@domain.logic
@app.config
@app.semantics

# Ontology: Source - app.static.semantics.config

Configuration semantics enumerations.
"""
# Standard Libraries
from enum import StrEnum

class Configurations(StrEnum):
    """Enumeration of Configurations"""
    ACTIONS         = "actions"
    COMPOSITIONS    = "compositions"
    INTENTIONS      = "intentions"
    LIBRARY         = "library"
    MAPPINGS        = "mappings"
    MARKETS         = "markets"
    MECHANICS       = "mechanics"
    MENUS           = "menus"
    PLOTS           = "plots"
    RECIPES         = "recipes"

# ----------------------------------------------------------
# -------------------------------- ASSET RECIPE ENUMERATIONS
# ----------------------------------------------------------
#   NOTE: These are required Recipe configuration keys

class FrameRecipe(StrEnum):
    BINARY          = "binary"
    CARDINAL        = "cardinal"
    DIRECTED        = "directed"
    FLUID           = "fluid"
    ICON            = "icon"
    ITERABLE        = "iterable"
    MATERIAL        = "material"
    METER           = "meter"
    NONE            = "none"
    OBJECT          = "object"
    ORIENTED        = "oriented"
    PANE            = "pane"
    SINGLE          = "single"
    SEASONAL        = "seasonal"
    SPRITE          = "sprite"
    STAGE           = "stage"
    STATE           = "state"
    TRAVERSAL       = "traversal"
    
class AnimationRecipe(StrEnum):
    NONE            = "none"
    STATE           = "state"
    SPRITE          = "sprite"
    FREQUENCY       = "frequency"

class HitboxRecipe(StrEnum):
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
