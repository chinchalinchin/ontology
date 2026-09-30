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
    SOCIAL          = "social"
    SWITCH          = "switch"
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

class MotiveAssets(str, Enum):
    PLAYERS         = "players"
    SPRITES         = "sprites"

class FrictiveAssets(str, Enum):
    CRATES          = "crates"

class InertAssets(str, Enum):
    PROJECTILES     = "projectiles"

class Shortcuts(str, Enum):
    COMPOSITIONS    = "compositions"
    GIZMOS          = "gizmos"
    PLOTS           = "plots"

# -------------------------------- MECHANIC ENUMERATIONS

class Reactions(str, Enum):
    BOUNCE          = "bounce"
    HINDER          = "hinder"
    
class Relations(str, Enum):
    SHORELINES      = "shorelines"

class Executors(str, Enum):
    PLOT            = "plot"
    INTENTION       = "intention"
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
