"""
@domain.system
@workflow.initialization

# Ontology: Source - app.services.orchestration.orchestrator

Application Dependency Pipeline
"""
# Application Libraries
from app.static.semantics import Menus
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

    def orchestrate(
        self,
        state_key: str = None,
        screensize: Dimensions = None,
        device: str = None,
        headless: bool = False
    ) -> Engine:
        # 1. Static Schemas & Compiled Domain Indices
        self.builder.load_data()
        self.builder.build_executors()
        self.builder.build_relations()

        # 2. Hardware/SDL Context & GPU Asset Registry
        self.builder.init_subsystems(screensize, headless)
        self.builder.build_registry()

        # 3. Services, Board Database, and Mechanics Pipeline
        self.builder.build_services(device)
        self.builder.build_board()
        self.builder.build_pipeline()

        engine = self.builder.get_engine()

        # Short-circuit to state hydration if state_key is given; otherwise boot to Main Menu
        if state_key is not None:
            engine.bus.append(StateEvent(id=state_key))
        else:
            engine.bus.append(
                MenuEvent(Menus.MAIN.value, MainContext(registry=self.builder.registry))
            )

        return engine