"""
@domain.logic
@domain.user
@app.semantics
@category.widgets
@workflow.menus

# Ontology: Source - app.static.semantics.menus

Menu semantics enumerations
"""
# Standard Libraries
from enum import StrEnum

# -------------------------------- WIDGET ENUMERATIONS

class Controllers(StrEnum):
    DISPLAY         = "display"
    INVENTORY       = "inventory"
    LOAD            = "load"
    MAIN            = "main"
    OPTIONS         = "options"
    PAUSE           = "pause"
    SCROLL          = "scroll"
    
class Layouts(StrEnum):
    DOCK            = "dock"
    STACK           = "stack"
    OVERLAY         = "overlay"

class Alignments(StrEnum):
    START           = "start"
    CENTER          = "center"
    END             = "end"

class Bindings(StrEnum):
    APERTURE        = "aperture"
    COLLECTION      = "collection"
    ICON            = "icon"
    LIBRARY         = "library"
    METER           = "meter"
    SELECT          = "select"
    TEXT            = "text"

class Traversal(StrEnum):
    NORTH           = "north"
    SOUTH           = "south"
    EAST            = "east"
    WEST            = "west"

class Interactions(StrEnum):
    SELECT          = "select"
    CANCEL          = "cancel"
    PAUSE           = "pause"

class Menus(StrEnum):
    DIALOGUE        = "dialogue"
    EQUIPMENT       = "equipment"
    LOAD            = "load"
    MAIN            = "main"
    OPTIONS         = "options"
    PACK            = "pack"
    PAUSE           = "pause"
    POUCH           = "pouch"
    TEXT            = "text"
    TRADE           = "trade"
    VIEW            = "view"

class Selections(StrEnum):
    LOAD            = "load"
    MENU            = "menu"
    GRIP            = "grip"
    NEW             = "new"
    SAVE            = "save"
    SCROLLUP        = "scrollup"
    SCROLLDOWN      = "scrolldown"
    SLOT            = "slot"
    QUIT            = "quit"

class Statuses(StrEnum):
    ACTIVE          = "active"
    IDLE            = "idle"
    SELECTED        = "selected"
    DISABLED        = "disabled"

# -------------------------------- REQUIRED WIDGETS

class SystemPanes(StrEnum):
    TRANSPARENT     = "transparent"