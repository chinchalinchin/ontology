"""
# Ontology: app.game.menus.contexts

Package for Menu Context models.
"""
from __future__ import annotations

# Standard Libraries
from dataclasses import dataclass
from typing import (
    Any, 
    Dict, 
    Union, 
    List, 
    Optional, 
    TYPE_CHECKING
)

# Application Classes
from app.models.state.core import PlotState
from app.models.state.sprites import SpriteState
from app.models.state.objects import DialogueState

# Cython Libraries
from libs.graphics.registry import Registry
from libs.core.models import Dimensions

if TYPE_CHECKING:
    from app.game.board import Board


class MenuContext:
    pass


@dataclass(slots=True)
class ViewContext(MenuContext):
    sprite: SpriteState


@dataclass(slots=True)
class MainContext(MenuContext):
    registry: Registry


@dataclass(slots=True)
class TextContext(MenuContext):
    content: Union[str, List[str]]


@dataclass(slots=True)
class LoadContext(MenuContext):
    registry: Registry
    screens: Dict[str, Any]
    screensize: Dimensions


@dataclass(slots=True)
class DialogueContext(MenuContext):
    plot: PlotState 
    sprite: SpriteState = None
    object: DialogueState = None


@dataclass(slots=True)
class InventoryContext(MenuContext):
    inventory: Any


@dataclass(slots=True)
class PauseContext(MenuContext):
    board: Board