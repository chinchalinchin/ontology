"""
# Ontology: app.config.enums

"""
# Standard Libraries
from enum import Enum

# -------------------------------- ENGINE ENUMERATIONS

class Mechanics(str, Enum):
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

class Configurations(str, Enum):
    ACTIONS         = "actions"
    COMPOSITIONS    = "compositions"
    INTENTIONS      = "intentions"
    LIBRARY         = "library"
    MAPPINGS        = "mappings"
    MECHANICS       = "mechanics"
    MENUS           = "menus"
    PLOTS           = "plots"
    RECIPES         = "recipes"

class Shortcuts(str, Enum):
    ASSETS          = "assets"
    CALENDAR        = "calendar"
    COMPOSITIONS    = "compositions"
    BRIDGES         = "bridges"
    GIZMOS          = "gizmos"
    PLOTS           = "plots"

class Substrates(int, Enum):
    ENVIRON         = -4 
    FLUIDS          = -3
    GEOGRAPHY       = -2
    BRIDGES         = -1

# -------------------------------- ENGINE ASSET ENUMERATIONS

class MotiveAssets(str, Enum):
    PLAYERS         = "players"
    SPRITES         = "sprites"

class FrictiveAssets(str, Enum):
    CRATES          = "crates"

class InertAssets(str, Enum):
    PROJECTILES     = "projectiles"

class OrientedAssets(str, Enum):
    RAILINGS        = "railings"
    BRIDGES         = "bridges"
    
# -------------------------------- MECHANIC ENUMERATIONS

class Reactions(str, Enum):
    BOUNCE          = "bounce"
    HINDER          = "hinder"
    
class Relations(str, Enum):
    SHORELINES      = "shorelines"

class Executors(str, Enum):
    # TRANSITION EXECUTORS
    PLOT            = "plot"
    INTENTION       = "intention"
    ANNUAL          = "annual"
    PERENNIAL       = "perennial"
    CENTENNIAL      = "centennial"
    # GENERATORS
    ACTUATOR        = "actuator"

class Translators(str, Enum):
    COMPILER        = "compiler"
    LAMBDA          = "lambda"

# -------------------------------- RENDERING ENUMERATIONS

class ChannelTypes(int, Enum):
    TINT            = 0
    SUBMERGE        = 1


class Fonts(str, Enum):
    DIALOGUE        = "dialogue"
    MENU            = "menu"
    TITLE           = "title"
