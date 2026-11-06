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
    TYPE_CHECKING
)
from dataclasses import dataclass
import collections

# Application Libraries
from app.assets.base import Asset
from app.game.menus.bindings import Binding
from app.models.menus import MenuContext

if TYPE_CHECKING:
    from app.game.menus.controllers.base import MenuController
    from app.game.board import Board
    from app.game.screen import Screen
    from app.services.generators.menus.provider import Provider

class Widget(Asset):
    """
    Standard Asset overridden to require the Binding ECS component.
    """
    binding: Binding
    
    def __init__(self, taxonomy, properties, state, frame, animation, binding: Binding):
        super().__init__(taxonomy, properties, state, frame, animation)
        self.binding = binding

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


@dataclass(slots=True)
class EventContext:
    """
    State container passed to EventHandlers during routing.
    """
    board: Board
    screens: Dict[str, Screen]
    provider: Provider
    bus: collections.deque