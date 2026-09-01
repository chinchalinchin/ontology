"""
# Ontology: app.models.config.menus

Models for typing the configuration attributes of Menus.
"""
# Standard Libraries
from typing import (
    List, 
    Optional, 
    Union
)
from dataclasses import dataclass

# Application Libraries
from app.config.enums import (
    Statuses,
    Layouts,
    Alignments,
)
from app.game.menus.core import Binding
from app.models.adapters import (
    PydanticScreenPosition as ScreenPosition
)
from app.models.config.core import Configuration

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- MENU CONFIGURATION

@dataclass(slots=True)
class MenuWidget:
    instance: str
    id: str
    name: str
    bind: Optional[Binding] = None
    status: Optional[Statuses] = Statuses.IDLE

@dataclass(slots=True)
class MenuPane:
    id: str 
    name: str
    layout: Layouts
    alignment: Alignments
    gap: int
    children: List[Union['MenuPane', MenuWidget]]
    margins: Optional[int] = 0
    position: Optional[ScreenPosition] = None # type: ignore

@dataclass(slots=True)
class MenuConfiguration(Configuration):
    controller: str
    roots: List[MenuPane]
