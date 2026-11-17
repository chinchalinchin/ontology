"""
@domain.logic
@app.semantics
@modality.appearance
@workflow.rendering

# Ontology: Source - app.static.semantics.graphics

Graphics semantics enumerations.
"""
# Standard Libraries
from enum import (
    StrEnum,
    IntEnum
)

class ChannelTypes(IntEnum):
    """Enumeration of Frame Channels"""
    TINT            = 0
    SUBMERGE        = 1

class Fonts(StrEnum):
    """Enumeration of Font Assets."""
    DIALOGUE        = "dialogue"
    MENU            = "menu"
    TITLE           = "title"
