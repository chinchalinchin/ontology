"""
# Ontology: app.game.menus.core
"""
from __future__ import annotations
# Standard Libraries
from typing import Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

# Application Libraries
from app.assets.base import Asset
from app.game.menus.bindings import Binding

if TYPE_CHECKING:
    from app.game.menus.controllers.base import MenuController

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
    context: Dict[str, Any]
    widgets: Dict[str, Widget]    
    controller: MenuController