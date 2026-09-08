"""
# Ontology: app.game.menus.handlers.state

State event handling implementation.
"""
# Standard Libraries
import logging

# Application Libraries
from app.config.enums import Menus
from app.game.menus.events import (
    MenuEvent, 
    StateEvent,
    EventContext
)
from app.game.menus.contexts import LoadContext
from app.game.menus.handlers.base import EventHandler

logger = logging.getLogger(__name__)


class StateEventHandler(EventHandler):
    def handle(self, event: StateEvent, context: EventContext) -> None:
        if not context.board.migrator:
            logger.warning("StateEvent received, but no Migrator defined on Board")
            return
        
        context.board.migrator.target = event.id    
        context.bus.append(MenuEvent(
            id=Menus.LOAD.value, 
            context=LoadContext(
                registry=next(iter(context.screens.values())).registry,
                screens=context.screens,
                screensize=next(iter(context.screens.values())).screensize
            )
        ))
