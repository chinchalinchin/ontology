"""
@domain.concrete
@domain.system
@app.menu
@menu.handler
@workflow.hydration

# Ontology: Source - app.game.menus.handlers.state

State event handling implementation.
"""
# Standard Libraries
import logging

# Application Libraries
from app.static.semantics import Menus
from app.models.menus import (
    MenuEvent,
    StateEvent,
    LoadContext
)
from app.game.menus.core import EventData
from app.game.menus.handlers.base import EventHandler

logger = logging.getLogger(__name__)


class StateEventHandler(EventHandler):
    def handle(self, event: StateEvent, data: EventData) -> None:
        if not data.board.migrator:
            logger.warning("StateEvent received, but no Migrator defined on Board")
            return
        
        data.board.migrator.target = event.id    
        data.bus.append(MenuEvent(
            id=Menus.LOAD.value, 
            context=LoadContext(
                registry=next(iter(data.screens.values())).registry,
                screens=data.screens,
                screensize=next(iter(data.screens.values())).screensize
            )
        ))
