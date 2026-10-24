"""
# Ontology: app.models.properties.fonts

Module for typing Font property attributes.
"""
# Standard Libraries
from typing import Optional
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.static.semantics import (
    Alignments,
)

# --------------------------------------------------------------

@dataclass(slots=True)
class RGBA:
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255

@dataclass(slots=True)
class Outline:
    color: RGBA = field(default_factory=lambda: RGBA(r=255, g=255, b=255, a=255))    
    width: int = 0

# --------------------------------------------------------------

@dataclass(slots=True)
class FontProperties:
    alignment: Alignments = Alignments.START.value
    color: RGBA = field(default_factory=lambda: RGBA(r=255, g=255, b=255, a=255))    
    outline: Optional[Outline] = None
    bold: bool = False
    italics: bool = False
    strikethrough: bool = False
    underline: bool = False
    margins: float = 0
    size: int = 24