# /home/grant/Projects/ontology/src/app/game/menus/events.py

"""
# Ontology: app.game.menus.events
"""
from dataclasses import dataclass
from typing import Any, Union, List

class Event:
    pass

@dataclass(slots=True)
class MenuEvent(Event):
    id: str
    context: dict

@dataclass(slots=True)
class UpdateEvent(Event):
    widget: Any
    content: Union[str, List[str]]

@dataclass(slots=True)
class StateEvent(Event):
    id: str

class TerminalEvent(Event):
    pass