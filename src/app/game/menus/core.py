"""
@domain.user
@domain.model
@app.core
@app.menu

# Ontology: Source - app.game.menus.core
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING
)
from dataclasses import dataclass
import collections

# Application Libraries
from app.assets.base import Asset
from app.game.menus.bindings import Binding
from app.models.menus import MenuContext
from app.models.state import PaneState

# Cython Libraries
from libs.core.models import Dimensions

if TYPE_CHECKING:
    from app.game.menus.controllers.base import MenuController
    from app.game.board import Board
    from app.game.screen import Screen
    from app.services.generators.menus.provider import Provider

# ---------------------------------------------------------------------

class Widget(Asset):
    """
    Attach Binding to standard Asset base to allow state closure.
    """
    binding: Optional[Binding]

    def __init__(self, taxonomy, properties, state, frame, animation, binding: Optional[Binding] = None):
        super().__init__(taxonomy, properties, state, frame, animation)
        self.binding = binding

    @property
    def dimensions(self) -> Dimensions:
        if isinstance(self.state, PaneState):
            return self.state.span
        return self.properties.dimensions

# ---------------------------------------------------------------------

@dataclass(slots=True)
class Menu:
    """
    Structured envelope returned by the Provider containing runtime layout relationships.
    """
    id: str
    focus: str
    graph: Dict[str, Dict[str, str]]
    context: MenuContext
    widgets: Dict[str, Widget]
    controller: MenuController

# ---------------------------------------------------------------------

@dataclass(slots=True)
class EventData:
    """
    State container passed to EventHandlers during routing.
    """
    board: Board
    screens: Dict[str, Screen]
    provider: Provider
    bus: collections.deque