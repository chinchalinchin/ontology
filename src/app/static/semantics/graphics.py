"""
@app.semantics
@workflow.rendering

# Ontology: app.config.enums.graphics

Enumeration of Graphics semantics.
"""
# Standard Libraries
from enum import Enum

class ChannelTypes(int, Enum):
    """Enumeration of Frame Channels"""
    TINT            = 0
    SUBMERGE        = 1

class Fonts(str, Enum):
    """Enumeration of Font Assets."""
    DIALOGUE        = "dialogue"
    MENU            = "menu"
    TITLE           = "title"
