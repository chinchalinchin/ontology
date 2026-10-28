"""
@domain.test
@test.fixtures
@app.core
@app.component
@app.devices
@app.mechanics
@workflow.injection

# Ontology: Test - tests.unit.fixtures.components

Concrete application component, device, registry, mechanic, and engine fixtures.
"""
# Standard Libraries
import collections
from typing import Any, Optional, Union

# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.game.board import Board
from app.game.devices import (
    Device,
    Keyboard,
)
from app.game.engine import Engine
from app.game.logic.mechanics import Mechanic
from app.game.logic.relations import MaterialIndex
from app.game.screen import Screen
from app.models.config import (
    ConfigurationSchema,
    MechanicsInstance,
)
from app.models.groups import EquipmentGroup
from app.models.properties import PropertiesSchema
from app.models.state import (
    CalendarState,
    StateSchema,
)
from app.services.factories import MechanicFactory
from app.services.generators.game import (
    Cradle,
    Decomposer,
)
from app.services.generators.menus import Provider
from app.services.orchestration import Migrator
from app.static.semantics import (
    AssetCategories,
    Devices,
    Mechanics,
)

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import Dimensions
from libs.graphics.registry import Registry

# ---------------------------------------------------------------------------
# --------------------------------------------- SUBSYSTEMS & ASSET REGISTRY
# ---------------------------------------------------------------------------


@pytest.fixture
def sdl_headless() -> Dimensions:
    """
    Initializes the Cython SDL2 subsystem in headless software-renderer mode.
    """
    viewport = Dimensions(320, 240)
    render.init(viewport.w, viewport.l, True)
    return viewport


@pytest.fixture
def mock_registry(
    sdl_headless: Dimensions,
    mock_properties_schema: PropertiesSchema,
    mock_configurations_schema: ConfigurationSchema,
) -> Registry:
    """
    Concrete Cython Registry initialized with application properties, recipes, and fonts.
    """
    registry = Registry(
        properties=mock_properties_schema,
        recipes=mock_configurations_schema.recipes,
        typography=mock_properties_schema.fonts,
    )
    yield registry
    registry.clear()


# ---------------------------------------------------------------------------
# ------------------------------------------------------------------ DEVICES
# ---------------------------------------------------------------------------


@pytest.fixture
def device(mock_configurations_schema: ConfigurationSchema):
    """
    Parameterized fixture factory instantiating an input Device via MechanicFactory.
    """
    def _device(kind: str = Devices.KEYBOARD.value) -> Device:
        mapping = getattr(mock_configurations_schema.mappings, kind, None)
        return MechanicFactory.device(kind, mapping)

    return _device


@pytest.fixture
def mock_keyboard(device) -> Keyboard:
    """
    Default Keyboard input device instance.
    """
    return device(Devices.KEYBOARD.value)


# ---------------------------------------------------------------------------
# ------------------------------------------------------------------- SCREEN
# ---------------------------------------------------------------------------


@pytest.fixture
def screen(
    sdl_headless: Dimensions,
    mock_registry: Registry,
):
    """
    Parameterized fixture factory instantiating a concrete Screen over headless SDL canvases.
    """
    allocated_screens: list[Screen] = []

    def _screen(
        screensize: Optional[Dimensions] = None,
        boardsize: Optional[Dimensions] = None,
        tiles: Optional[list[Asset]] = None,
        calendar: Optional[CalendarState] = None,
    ) -> Screen:
        instance = Screen(
            screensize=screensize or sdl_headless,
            boardsize=boardsize or Dimensions(640, 480),
            tiles=tiles if tiles is not None else [],
            registry=mock_registry,
            calendar=calendar or CalendarState(),
        )
        allocated_screens.append(instance)
        return instance

    yield _screen

    for inst in allocated_screens:
        inst.destroy()


@pytest.fixture
def mock_screen(screen) -> Screen:
    """
    Default concrete Screen instance.
    """
    return screen()


# ---------------------------------------------------------------------------
# -------------------------------------------------------------------- BOARD
# ---------------------------------------------------------------------------


@pytest.fixture
def board(
    mock_assets: list[Asset],
    mock_configurations_schema: ConfigurationSchema,
    mock_properties_schema: PropertiesSchema,
    mock_state_schema: StateSchema,
    mock_equipment: EquipmentGroup,
    mock_cradle: Cradle,
    mock_decomposer: Decomposer,
    mock_material_index: MaterialIndex,
    mock_keyboard: Keyboard,
):
    """
    Parameterized fixture factory assembling a concrete Board with injected dependencies.
    """
    def _board(
        assets: Optional[list[Asset]] = None,
        loaded: bool = True,
        paused: bool = False,
    ) -> Board:
        initial_assets = mock_assets if assets is None else assets
        instance = Board(
            assets=initial_assets,
            configurations=mock_configurations_schema,
            equipment=mock_equipment,
        )
        instance.loaded = loaded
        instance.paused = paused

        if getattr(mock_state_schema, "calendar", None) is not None:
            instance.calendar = mock_state_schema.calendar
        if getattr(mock_state_schema, "plots", None) is not None:
            instance.set_plot(mock_state_schema.plots)

        instance.set_device(mock_keyboard)
        instance.set_cradle(mock_cradle)
        instance.set_migrator(
            Migrator(
                board=instance,
                properties=mock_properties_schema,
                configurations=mock_configurations_schema,
                decomposer=mock_decomposer,
                materials=mock_material_index,
            )
        )
        return instance

    return _board


@pytest.fixture
def mock_board(board) -> Board:
    """
    Default concrete Board hydrated with testbed assets and services.
    """
    return board()


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------- MECHANICS
# ---------------------------------------------------------------------------


@pytest.fixture
def mechanic(
    executors,
    mock_relations: dict[str, Any],
):
    """
    Parameterized fixture factory instantiating a Mechanic via MechanicFactory.
    """
    def _mechanic(
        instance: Union[str, MechanicsInstance],
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ) -> Mechanic:
        cfg = (
            instance
            if isinstance(instance, MechanicsInstance)
            else MechanicsInstance(instance)
        )
        return MechanicFactory.mechanics(
            cfg,
            executors(implementation),
            mock_relations,
        )

    return _mechanic


# ---------------------------------------------------------------------------
# --------------------------------------------------------------- ENGINE & BUS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bus() -> collections.deque:
    """
    Clean asynchronous Engine event bus deque.
    """
    return collections.deque()


@pytest.fixture
def engine(
    mock_board: Board,
    mock_configurations_schema: ConfigurationSchema,
    mock_relations: dict[str, Any],
    mock_provider: Provider,
    mock_registry: Registry,
    screen,
    executors,
):
    """
    Parameterized fixture factory constructing an Engine with configurable
    translator implementation ('lambda' or 'compiler') and mechanic pipelines.
    """
    def _engine(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
        target_board: Optional[Board] = None,
        screens: Optional[dict[str, Screen]] = None,
        core: Optional[list[Mechanic]] = None,
        world: Optional[list[Mechanic]] = None,
    ) -> Engine:
        active_board = target_board or mock_board
        compiled_executors = executors(implementation)

        if core is None:
            core_cfg = mock_configurations_schema.mechanics.core or [
                MechanicsInstance(Mechanics.MENU.value),
                MechanicsInstance(Mechanics.ANIMATION.value),
                MechanicsInstance(Mechanics.REMOVE.value),
            ]
            core_pipeline = [
                MechanicFactory.mechanics(m, compiled_executors, mock_relations)
                for m in core_cfg
            ]
        else:
            core_pipeline = core

        if world is None:
            world_cfg = mock_configurations_schema.mechanics.world or [
                MechanicsInstance(Mechanics.PLAYER.value),
                MechanicsInstance(Mechanics.COGNITION.value),
                MechanicsInstance(Mechanics.TRANSITION.value),
                MechanicsInstance(Mechanics.MOTION.value),
            ]
            world_pipeline = [
                MechanicFactory.mechanics(m, compiled_executors, mock_relations)
                for m in world_cfg
            ]
        else:
            world_pipeline = world

        if screens is None:
            active_screens: dict[str, Screen] = {}
            layers = active_board.layers() or ["default"]
            layer_sizes = active_board.size()
            for idx, layer_key in enumerate(layers):
                board_dim = (
                    layer_sizes[idx]
                    if idx < len(layer_sizes)
                    and layer_sizes[idx].w > 0
                    and layer_sizes[idx].l > 0
                    else Dimensions(640, 480)
                )
                tiles = active_board.categories(
                    AssetCategories.TILES.value, layer=layer_key
                )
                active_screens[layer_key] = screen(
                    boardsize=board_dim,
                    tiles=tiles,
                    calendar=active_board.calendar,
                )
        else:
            active_screens = screens

        return Engine(
            board=active_board,
            screens=active_screens,
            core=core_pipeline,
            world=world_pipeline,
            provider=mock_provider,
            registry=mock_registry,
        )

    return _engine


@pytest.fixture
def mock_engine(engine) -> Engine:
    """
    Default concrete Engine instance assembled with default translator executors.
    """
    return engine()