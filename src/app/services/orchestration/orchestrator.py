"""
# Ontology: app.services.orchestration.constructors

Classes for constructing game objects.
"""
# Application Libraries
from app.config.enums import Menus
from app.game.engine import Engine
from app.game.menus.events import (
    MenuEvent,
    StateEvent
)
from app.game.menus.contexts import MainContext
from app.services.orchestration.builder import Builder

# Cython Libraries
from libs.core.models import Dimensions

class Orchestrator:
    """
    Enforces the correct sequence of instantiation for the Engine lifecycle.
    """
    def __init__(self, builder: Builder = None):
        if builder is None:
            builder = Builder()
        self.builder = builder

    def orchestrate(self, 
        state_key: str = None, 
        screensize: Dimensions = None, 
        device: str = None, 
        headless: bool = False
    ) -> Engine:
        # Load state definitions (deferred evaluation by Migrator)
        self.builder.load_data(state_key)
        self.builder.build_executors()
        self.builder.init_subsystems(screensize, headless)
        
        self.builder.build_board()
        self.builder.build_registry()
        
        self.builder.build_services(device)
        self.builder.build_pipeline()
        
        engine = self.builder.get_engine()
        registry = next(iter(engine.screens.values())).registry
        
        # Short-circuit to state hydration if state_key is given; otherwise boot to Main Menu
        if state_key is not None:
            engine.bus.append(StateEvent(id=state_key))
        else:
            engine.bus.append(MenuEvent(Menus.MAIN.value, MainContext(registry=registry)))        

        return engine