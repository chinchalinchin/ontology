"""
@domain.user
@domain.abstract
@app.menu
@menu.handler

# Ontology: Source - app.game.menus.handlers.base

Strategy implementations for Event resolution.
"""
# Standard Libraries
from abc import (
    ABC, 
    abstractmethod
)

# Application Libraries
from app.models.menus import Event
from app.game.menus.core import EventData

class EventHandler(ABC):
    
    @abstractmethod
    def handle(self, event: Event, context: EventData) -> None:
        pass