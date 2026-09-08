"""
# Ontology: app.game.menus.handlers

Strategy implementations for Event resolution.
"""
# Standard Libraries
from abc import ABC, abstractmethod

# Application Libraries
from app.game.menus.events import (
    Event, 
    EventContext
)

class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: Event, context: EventContext) -> None:
        pass