"""
# Ontology: app.config.enums.menus

Menu key enumerations
"""
# Standard Libraries
from enum import Enum

# -------------------------------- WIDGET ENUMERATIONS

class Controllers(str, Enum):
    DISPLAY         = "display"
    INVENTORY       = "inventory"
    LOAD            = "load"
    MAIN            = "main"
    OPTIONS         = "options"
    PAUSE           = "pause"
    SCROLL          = "scroll"
    
class Layouts(str, Enum):
    DOCK            = "dock"
    STACK           = "stack"
    OVERLAY         = "overlay"

class Alignments(str, Enum):
    START           = "start"
    END             = "end"
    CENTER          = "center"

class Bindings(str, Enum):
    APERTURE        = "aperture"
    COLLECTION      = "collection"
    ICON            = "icon"
    LIBRARY         = "library"
    METER           = "meter"
    SELECT          = "select"
    TEXT            = "text"

class Traversal(str, Enum):
    NORTH           = "north"
    SOUTH           = "south"
    EAST            = "east"
    WEST            = "west"

class Interactions(str, Enum):
    SELECT          = "select"
    CANCEL          = "cancel"
    PAUSE           = "pause"

class Menus(str, Enum):
    DIALOGUE        = "dialogue"
    INVENTORY       = "inventory"
    LOAD            = "load"
    MAIN            = "main"
    OPTIONS         = "options"
    PAUSE           = "pause"
    TEXT            = "text"
    TRADE           = "trade"
    VIEW            = "view"

class Selections(str, Enum):
    LOAD            = "load"
    MENU            = "menu"
    NEW             = "new"
    SAVE            = "save"
    SCROLLUP        = "scrollup"
    SCROLLDOWN      = "scrolldown"
    SLOT            = "slot"
    QUIT            = "quit"

class Statuses(str, Enum):
    ACTIVE          = "active"
    IDLE            = "idle"
    SELECTED        = "selected"
    DISABLED        = "disabled"
