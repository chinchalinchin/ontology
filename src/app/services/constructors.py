"""
# Ontology: app.services.constructors

Classes for constructing game objects.
"""
# Standard Libraries
import logging
import dataclasses
from typing import Dict, List
from enum import Enum

# Application Libraries
import app.config.settings as settings
from app.config.loader import Loader
from app.config.enums import (
    Devices, 
    Mechanics, 
)
from app.game.board import Board
from app.game.engine import Engine
from app.game.screen import Screen
from app.game.logic.mechanics.core import Mechanic
from app.game.logic.mechanics.intentional import TransitionMechanics
from app.models.groups import (
    SpawnableGroup, 
    EquipmentGroup
)
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema
from app.services.factory import Factory
from app.services.migrator import Migrator
from app.services.generators.decomposer import Decomposer
from app.services.generators.provider import Provider

# Cython Libraries
from libs.core.models import Dimensions
import libs.graphics.render as render
from libs.graphics.registry import Registry

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class Context:
    """
    Isolates raw data configurations before they are hydrated into Engine components.
    """
    properties: PropertiesSchema = None
    state: StateSchema = None
    configurations: ConfigurationSchema = None
    screensize: Dimensions = None
    headless: bool = False


class Builder:
    """
    Constructs the discrete subsystems of the Ontology engine.
    """
    def __init__(self):
        self.context = Context()
        self.registry: Registry = None
        self.board: Board = None
        self.provider: Provider = None
        self.screens: Dict[str, Screen] = {}
        self.core: List[Mechanic] = []
        self.world: List[Mechanic] = []


    @staticmethod
    def _unbox_enums(data):
        """
        Recursively resolves Enum instances to their primitive values.
        """
        if isinstance(data, dict):
            return {k: Builder._unbox_enums(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [Builder._unbox_enums(v) for v in data]
        elif isinstance(data, Enum):
            return data.value
        return data

    
    def _resolve_actions(self) -> None:
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
                    action_data = next((a.data for a in self.context.configurations.actions if a.id == e_props.actions), {})
                    resolved_dict[e_id] = dataclasses.replace(e_props, actions=action_data)
                else:
                    resolved_dict[e_id] = e_props
            resolved_sheets[sheet_type] = resolved_dict
            
        self.context.properties.sheets = dataclasses.replace(
            self.context.properties.sheets, 
            **resolved_sheets
        )


    def load_data(self, state_key: str) -> None:
        """
        """
        logger.info(f"Loading YAML data for target state: {state_key} ...")
        self.context.properties = Loader.load_properties()
        self.context.configurations = Loader.load_configurations()
        self.context.state = Loader.load_state(state_key)


    def init_subsystems(self, screensize: Dimensions, headless: bool = True) -> None:
        """
        """
        logger.info("Initializing SDL and Cython rendering subsystems...")
        self.context.screensize = screensize
        self.context.headless = headless
        render.init(screensize.w, screensize.l, headless)

        # IMPORTANT: This MUST be called before the Registry inits.
        if not headless:
            render.show()


    def build_board(self) -> None:
        logger.info("Constructing Empty Board and Migrator subsystem...")
        self._resolve_actions()

        # 1. Instantiate Decomposer ahead of standard Asset migrations
        self.decomposer = Decomposer(
            compositions=self.context.configurations.compositions,
            properties=self.context.properties,
            recipes=self.context.configurations.recipes
        )

        equipment = EquipmentGroup(
            armor=self.context.properties.sheets.armor,
            weapons=self.context.properties.sheets.weapons,
            tools=self.context.properties.sheets.tools,
            utilities=self.context.properties.sheets.utilities,
            shields=self.context.properties.sheets.shields
        )
        
        self.board = Board([], self.context.configurations, equipment)
        
        # Attach Migrator logic for deferred ECS evaluation
        self.board.migrator = Migrator(self.board, self.context.properties, self.context.configurations)

    def build_registry(self) -> None:
        """
        """
        logger.info("Initializing Registry...")
        # Unpack root dataclasses and resolve Enums to primitives
        properties_dict = self._unbox_enums(dataclasses.asdict(self.context.properties))
        recipes_dict = self._unbox_enums(dataclasses.asdict(self.context.configurations.recipes))
        fonts_dict = properties_dict.pop("fonts", {})
        self.registry = Registry(properties_dict, recipes_dict, fonts_dict)


    def build_services(self, device: Devices) -> None:
        """
        """
        logger.info("Injecting Generators and Devices into Board...")
        device_mapping = getattr(self.context.configurations.mappings, device, None)
        device_instance = Factory.device(device, device_mapping)
        self.board.set_device(device_instance)
        spawnable_groups = SpawnableGroup(
            projectiles=self.context.properties.cursors.projectiles,
            expressions=self.context.properties.cursors.expressions,
            temporary=self.context.properties.effects.temporary,
            struts=self.context.properties.crafts.struts
        )
        cradle = Factory.cradle(spawnable_groups, self.context.configurations.recipes, self.decomposer)
        self.board.set_cradle(cradle)


    def build_pipeline(self) -> None:
        logger.info("Building rendering pipelines, mechanics, and UI...")

        if not self.board.layers():
            # Initial Boot - No scene layers yet; provision a blank Master Screen
            self.screens = {
                'default': Screen(self.context.screensize, self.context.screensize, [], self.registry)
            }
        else:
            # Rehydrate logic fallback (if Migrator handles it differently in the future)
            self.screens = {}
            for layer in self.board.layers():
                max_width = max((self.board.size(layer)[0].w for layer in self.board.layers()), default=0)
                max_length = max((self.board.size(layer)[0].l for layer in self.board.layers()), default=0)
                self.screens[layer] = Screen(
                    self.context.screensize, 
                    Dimensions(max_width, max_length),
                    self.board.categories('tiles', layer),
                    self.registry
                )

        # Allocate Mechanics (Unchanged implementation)
        core_cfg = getattr(self.context.configurations.mechanics, 'core', None) or [
            Mechanics.MENU.value, Mechanics.ANIMATION.value, Mechanics.REMOVE.value
        ]
        world_cfg = getattr(self.context.configurations.mechanics, 'world', None) or [
            Mechanics.PLAYER.value, Mechanics.COGNITION.value, 
            Mechanics.TRANSITION.value, Mechanics.MOTION.value
        ]
        
        self.core = [Factory.mechanics(m) for m in core_cfg]
        self.world = [Factory.mechanics(m) for m in world_cfg]

        # Post-Process Core: Inject the compiled ISL Executor into TransitionMechanics (Unchanged implementation)
        translator = Factory.translator(settings.ISL_TRANSLATOR)
        executor = translator.compile(self.context.configurations.intentions)
            
        for m in self.world:
            if isinstance(m, TransitionMechanics):
                m.executor = executor

        # Allocate Menu Provider & Views (Unchanged implementation)
        self.provider = Provider(
            self.context.configurations.recipes.widgets, 
            self.context.properties.widgets, 
            self.registry
        )


    def get_engine(self) -> Engine:
        logger.info("Engine successfully assembled.")
        return Engine(
            board=self.board, 
            screens=self.screens, 
            core=self.core, 
            world=self.world, 
            provider=self.provider
        )


class Orchestrator:
    """
    Enforces the correct sequence of instantiation for the Engine lifecycle.
    """
    def __init__(self, builder: Builder = None):
        if builder is None:
            builder = Builder()
        self.builder = builder

    def orchestrate(self, 
        state_key: str, 
        screensize: Dimensions, 
        device: str, 
        headless: bool = False
    ) -> Engine:
        # Load state definitions (deferred evaluation by Migrator)
        self.builder.load_data(state_key) 
        self.builder.init_subsystems(screensize, headless)
        
        self.builder.build_board()
        self.builder.build_registry()
        
        self.builder.build_services(device)
        self.builder.build_pipeline()
        
        engine = self.builder.get_engine()
        registry = next(iter(engine.screens.values())).registry
        
        # Seed the Menu stack immediately for instantaneous launch
        from app.game.menus.events import MenuEvent
        engine.bus.append(MenuEvent('main', {'registry': registry}))
        
        return engine