"""
@domain.model
@app.menu

# Ontology: Source - app.models.menus.events
"""
# Standard Libraries
from dataclasses import dataclass
from typing import (
    Any, 
    Union, 
    List
)

from app.models.menus import MenuContext

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

class SeasonEvent(Event):
    pass

class TerminalEvent(Event):
    pass