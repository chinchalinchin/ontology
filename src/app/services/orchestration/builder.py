"""
@domain.system
@app.services
@workflow.initialization
@workflow.injection

# Ontology: Source - app.services.orchestration.builder

Dependency Injection systems.
"""
from __future__ import annotations

# Standard Libraries
import logging
import dataclasses
from typing import (
    Dict, 
    List,
    Any
)

# Application Libraries
import app.static.settings as settings
from app.static.loader import Loader
from app.static.semantics import (
    Devices, 
    Mechanics,
    Executors,
    Lifespans,
    Relations
)
from app.game.board import Board
from app.game.devices import Device
from app.game.engine import Engine
from app.game.screen import Screen
from app.game.logic.mechanics import Mechanic
from app.game.logic.relations import (
    ShorelineIndex,
    MaterialIndex
)
from app.models.groups import (
    SpawnableGroup, 
    EquipmentGroup
)
from app.models.properties import PropertiesSchema
from app.models.config import (
    ConfigurationSchema, 
    MechanicsInstance
)
from app.services.markets import Materializer
from app.services.factories import MechanicFactory
from app.services.generators.game import (
    Cradle,
    Decomposer
)
from app.services.generators.menus import (
    Provider, 
    Library,
    Binder,
    Fabricator
)
from app.services.orchestration.migrator import Migrator

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import Dimensions
from libs.graphics.registry import Registry

logger = logging.getLogger(__name__)

# -------------------------------------------------

@dataclasses.dataclass
class ApplicationContext:
    """
    Isolates raw data configurations before they are hydrated into Engine components.
    """
    properties: PropertiesSchema = None
    configurations: ConfigurationSchema = None
    screensize: Dimensions = None
    headless: bool = False

# -------------------------------------------------


class Builder:
    """
    Constructs the discrete subsystems of the Ontology engine.
    """

    def __init__(self):
        self.context = ApplicationContext()
        self.registry: Registry = None
        self.board: Board = None
        self.device: Device = None
        self.decomposer: Decomposer = None
        self.cradle: Cradle = None
        self.library: Library = None
        self.binder: Binder = None
        self.fabricator: Fabricator = None
        self.provider: Provider = None
        self.materializer: Materializer = None
        self.screens: Dict[str, Screen] = {}
        self.core: List[Mechanic] = []
        self.world: List[Mechanic] = []
        self.executors: Dict[str, Any] = {}
        self.relations: Dict[str, Any] = {}


    def _actions(self) -> None:
        """
        Globally pre-hydrates Actions in Properties.
        """
        resolved_sheets = {}
        for sheet_field in dataclasses.fields(self.context.properties.sheets):
            sheet_type = sheet_field.name
            sheet_dict = getattr(self.context.properties.sheets, sheet_type, {})
            resolved_dict = {}
            for e_id, e_props in sheet_dict.items():
                if isinstance(e_props.actions, str):
                    action_data = next((
                        a.data 
                        for a in self.context.configurations.actions
                        if a.id == e_props.actions
                    ), {})
                    resolved_dict[e_id] = dataclasses.replace(e_props, actions=action_data)
                else:
                    resolved_dict[e_id] = e_props
            resolved_sheets[sheet_type] = resolved_dict
            
        self.context.properties.sheets = dataclasses.replace(
            self.context.properties.sheets, 
            **resolved_sheets
        )


    def load_data(self) -> None:
        """
        Loads YAML configuration data for properties and global configurations.
        State hydration is deferred to the Migrator.
        """
        self.context.properties = Loader.load_properties()
        self.context.configurations = Loader.load_configurations()
        self._actions()


    def build_executors(self) -> None:
        logger.info("Compiling master mechanic executors...")
        translator = MechanicFactory.translator(settings.TRANSLATOR_IMPLEMENTATION)
        intention_executor = translator.compile(self.context.configurations.intentions)
        plot_executor = translator.compile(self.context.configurations.plots)

        self.executors = {
            Executors.INTENTION.value: intention_executor,
            Executors.PLOT.value: plot_executor,
        }

        # Compile independent stage executors keyed by Lifespan enum values
        for lifespan in Lifespans:
            stage_rules = self.context.configurations.stages.get(lifespan.value)
            if stage_rules:
                self.executors[lifespan.value] = translator.compile(stage_rules)


    def build_relations(self) -> None:
        logger.info("Compiling relational indices...")
        self.relations = {
            Relations.SHORELINES.value: ShorelineIndex.from_properties(
                self.context.properties.geography.shorelines
            ),
            Relations.MATERIALS.value: MaterialIndex.from_configuration(
                self.context.configurations.materials
            )
        }


    def init_subsystems(self, screensize: Dimensions, headless: bool = True) -> None:
        logger.info("Initializing SDL and Cython rendering subsystems...")
        self.context.screensize = screensize
        self.context.headless = headless
        render.init(screensize.w, screensize.l, headless)

        # IMPORTANT: This MUST be called before the Registry inits.
        if not headless:
            render.show()


    def build_registry(self) -> None:
        """
        Initializes Registry directly using native application models.
        """
        logger.info("Initializing Registry with native models...")
        self.registry = Registry(
            properties=self.context.properties,
            recipes=self.context.configurations.recipes,
            typography=self.context.properties.fonts
        )


    def build_services(self, device: Devices) -> None:
        logger.info("Instantiating Generators, Devices, and UI Providers...")
        device_mapping = getattr(self.context.configurations.mappings, device, None)
        self.device = MechanicFactory.device(device, device_mapping)

        materials = self.relations[Relations.MATERIALS.value]

        self.materializer = Materializer(
            materials=materials
        )
        
        self.decomposer = Decomposer(
            compositions=self.context.configurations.compositions,
            properties=self.context.properties,
            recipes=self.context.configurations.recipes,
            materials=materials
        )

        spawnable_groups = SpawnableGroup(
            projectiles=self.context.properties.cursors.projectiles,
            expressions=self.context.properties.cursors.expressions,
            collectables=self.context.properties.effects.collectables,
            hazards=self.context.properties.effects.hazards,
            passive=self.context.properties.effects.passive,
            struts=self.context.properties.crafts.struts,
            shorelines=self.context.properties.geography.shorelines
        )
        self.cradle = Cradle(
            spawnables=spawnable_groups,
            recipes=self.context.configurations.recipes,
            materials=materials,
            decomposer=self.decomposer
        )

        self.library = Library(self.context.configurations.library)
        self.binder = Binder(self.registry, self.library)
        self.fabricator = Fabricator()
        self.provider = Provider(
            self.context.configurations.recipes.widgets,
            self.context.properties.widgets,
            self.binder,
            self.fabricator
        )


    def build_board(self) -> None:
        logger.info("Constructing Empty Board and Migrator subsystem...")
        equipment = EquipmentGroup(
            armor=self.context.properties.sheets.armor,
            weapons=self.context.properties.sheets.weapons,
            tools=self.context.properties.sheets.tools,
            utilities=self.context.properties.sheets.utilities,
            shields=self.context.properties.sheets.shields
        )

        self.board = Board([], self.context.configurations, equipment)
        self.board.set_device(self.device)
        self.board.set_cradle(self.cradle)

        migrator = Migrator(
            board=self.board,
            properties=self.context.properties,
            configurations=self.context.configurations,
            decomposer=self.decomposer,
            materials=self.relations[Relations.MATERIALS.value]
        )
        self.board.set_migrator(migrator)


    def build_pipeline(self) -> None:
        logger.info("Building rendering pipelines and mechanics...")
        self.screens = {
            'default': Screen(
                self.context.screensize, 
                self.context.screensize,
                [], 
                self.registry,
                self.board.calendar
            )
        }

        core_cfg = self.context.configurations.mechanics.core or [
            MechanicsInstance(Mechanics.MENU.value), 
            MechanicsInstance(Mechanics.ANIMATION.value), 
            MechanicsInstance(Mechanics.REMOVE.value)
        ]
        world_cfg = self.context.configurations.mechanics.world or [
            MechanicsInstance(Mechanics.PLAYER.value), 
            MechanicsInstance(Mechanics.COGNITION.value), 
            MechanicsInstance(Mechanics.TRANSITION.value), 
            MechanicsInstance(Mechanics.MOTION.value)
        ]
        
        self.core = [
            MechanicFactory.mechanics(m, self.executors, self.relations) 
            for m in core_cfg
        ]
        self.world = [
            MechanicFactory.mechanics(m, self.executors, self.relations) 
            for m in world_cfg
        ]


    def get_engine(self) -> Engine:
        logger.info("Engine successfully assembled.")
        return Engine(
            board=self.board, 
            screens=self.screens, 
            core=self.core, 
            world=self.world, 
            provider=self.provider,
            registry=self.registry
        )