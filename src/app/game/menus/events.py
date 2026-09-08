"""
# Ontology: app.game.menus.events
"""
import collections
from dataclasses import dataclass
from typing import Any, Union, List, Dict, TYPE_CHECKING

from app.game.menus.contexts import MenuContext

if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.screen import Screen
    from app.services.generators.provider import Provider

class Event:
    pass

@dataclass(slots=True)
class MenuEvent(Event):
    id: str
    context: MenuContext

@dataclass(slots=True)
class UpdateEvent(Event):
    widget: Any
    content: Union[str, List[str]]

@dataclass(slots=True)
class StateEvent(Event):
    id: str

class TerminalEvent(Event):
    pass

@dataclass(slots=True)
class EventContext:
    """
    State container passed to EventHandlers during routing.
    """
    board: 'Board'
    screens: Dict[str, 'Screen']
    provider: 'Provider'
    bus: collections.deque