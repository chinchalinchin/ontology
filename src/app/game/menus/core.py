"""
# Ontology: app.game.menus
"""
from __future__ import annotations

# Standard Libraries
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

# Application Libraries
from app.assets.base import Asset

if TYPE_CHECKING:
    from app.game.menus.controllers.base import MenuController
    
@dataclass(slots=True)
class Binding:
    selection: Optional[str] = None
    selector: Optional[str] = None
    state: Optional[str] = None

@dataclass(slots=True)
class Widget(Asset):
    binding: Binding

@dataclass(slots=True)
class Menu:
    id: str
    focus: str
    graph: Dict[str, Dict[str, str]]
    context: Dict[str, Any]
    widgets: Dict[str, Widget]    
    controller: MenuController