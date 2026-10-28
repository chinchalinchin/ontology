"""
@app.core
@app.semantics
@app.mechanics

# Ontology: Source - app.static.semantics.enums

Enumeration of Engine semantics.
"""
# Standard Libraries
from enum import Enum

# -------------------------------- ENGINE ENUMERATIONS

class Mechanics(str, Enum):
    """Enumeration of Mechanics."""
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
    SEASON          = "season"
    SOCIAL          = "social"
    SWITCH          = "switch"
    TELEMETRY       = "telemetry"
    TRANSITION      = "transition"

class Shortcuts(str, Enum):
    """Enumeration of Asset hydration shortcuts."""
    ASSETS          = "assets"
    CALENDAR        = "calendar"
    COMPOSITIONS    = "compositions"
    BRIDGES         = "bridges"
    GIZMOS          = "gizmos"
    PLOTS           = "plots"

class Substrates(int, Enum):
    """Enumeration of Asset rendering substrates"""
    ENVIRON         = -4 
    FLUIDS          = -3
    SURFACES        = -2
    OVERLAYS        = -1
    STANDARD        = 0

class LayerProjections(str, Enum):
    """Enumeration of Door Projections"""
    IN              = "in"
    OUT             = "out"
    
# -------------------------------- ENGINE ASSET ENUMERATIONS

class MotiveAssets(str, Enum):
    """Enumeration of Assets registered for Motive Motion updates."""
    PLAYERS         = "players"
    SPRITES         = "sprites"

class FrictiveAssets(str, Enum):
    """Enumeration of Assets registered for Frictive Motion updates."""
    CRATES          = "crates"

class InertAssets(str, Enum):
    """Enumeration of Assets registered for Inert Motion updates."""
    PROJECTILES     = "projectiles"

class MultipliedAssets(str, Enum):
    """Enumeration of Assets registered for Multiplication Strategies"""
    BRIDGES         = "bridges"
    ENCLOSURES      = "enclosures"
    RAILINGS        = "railings"
    STAIRS          = "stairs"
    STRUTS          = "struts"

# -------------------------------- MECHANIC ENUMERATIONS

class Reactions(str, Enum):
    """Enumeration of Hazard Reactions"""
    BOUNCE          = "bounce"
    HINDER          = "hinder"
    
class Relations(str, Enum):
    """Enumeration of Relations"""
    SHORELINES      = "shorelines"
    MATERIALS       = "materials"

class Executors(str, Enum):
    """Enumeration of Mechanic Executors"""
    # TRANSITION EXECUTORS
    PLOT            = "plot"
    INTENTION       = "intention"
    ANNUAL          = "annual"
    PERENNIAL       = "perennial"
    CENTENNIAL      = "centennial"
    # GENERATORS
    ACTUATOR        = "actuator"

class Translators(str, Enum):
    """Enumeration of Transition compilation techniques."""
    COMPILER        = "compiler"
    LAMBDA          = "lambda"

class MultiplicationStrategies(str, Enum):
    """Enumeration of strategies for Asset multiplication"""
    SIMPLE          = "simple"
    EXPANSION       = "expansion"
    ORIENTED        = "oriented"
    PERIMETER       = "perimeter"