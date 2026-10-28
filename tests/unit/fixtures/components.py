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
from typing import Any

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
from app.game.screen import Screen
from app.models.config import (
    ConfigurationSchema,
    MechanicsInstance,
)
from app.models.groups import EquipmentGroup
from app.models.properties import PropertiesSchema
from app.models.state import StateSchema
from app.services.factories import MechanicFactory
from app.services.generators.game import Cradle
from app.services.generators.menus import Provider
from app.static.semantics import Devices

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import Dimensions
from libs.graphics.registry import Registry

# ---------------------------------------------------------------------------
# --------------------------------------------- SUBSYSTEMS & ASSET REGISTRY
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_registry(
    mock_properties_schema: PropertiesSchema,
    mock_configurations_schema: ConfigurationSchema,
) -> Registry:
    render.init(320, 240, True)
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
    Fixture factory instantiating an input Device via MechanicFactory.
    """
    def _device(kind: str = Devices.KEYBOARD.value) -> Device:
        mapping = getattr(mock_configurations_schema.mappings, kind)
        return MechanicFactory.device(kind, mapping)

    return _device


@pytest.fixture
def mock_keyboard(device) -> Keyboard:
    return device(Devices.KEYBOARD.value)


# ---------------------------------------------------------------------------
# ------------------------------------------------------------------- SCREEN
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_screen(
    mock_registry: Registry,
    mock_state_schema: StateSchema,
) -> Screen:
    screen = Screen(
        screensize=Dimensions(320, 240),
        boardsize=Dimensions(640, 480),
        tiles=[],
        registry=mock_registry,
        calendar=mock_state_schema.calendar,
    )
    yield screen
    screen.destroy()


# ---------------------------------------------------------------------------
# -------------------------------------------------------------------- BOARD
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_board(
    mock_assets: list[Asset],
    mock_configurations_schema: ConfigurationSchema,
    mock_state_schema: StateSchema,
    mock_equipment: EquipmentGroup,
    mock_cradle: Cradle,
    mock_keyboard: Keyboard,
) -> Board:
    board = Board(
        assets=mock_assets,
        configurations=mock_configurations_schema,
        equipment=mock_equipment,
    )
    board.calendar = mock_state_schema.calendar
    board.set_plot(mock_state_schema.plots)
    board.set_cradle(mock_cradle)
    board.set_device(mock_keyboard)
    return board


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------- MECHANICS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mechanic(
    executors,
    mock_relations: dict[str, Any],
):
    """
    Fixture factory instantiating a Mechanic by name and translator implementation.
    """
    def _mechanic(
        name: str,
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ) -> Mechanic:
        return MechanicFactory.mechanics(
            MechanicsInstance(name),
            executors(implementation),
            mock_relations,
        )

    return _mechanic


# ---------------------------------------------------------------------------
# --------------------------------------------------------------- ENGINE & BUS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bus() -> collections.deque:
    return collections.deque()


@pytest.fixture
def engine(
    mock_board: Board,
    mock_screen: Screen,
    mock_configurations_schema: ConfigurationSchema,
    mock_relations: dict[str, Any],
    mock_provider: Provider,
    mock_registry: Registry,
    executors,
):
    """
    Fixture factory constructing an Engine parameterized by translator implementation ('lambda' or 'compiler').
    """
    def _engine(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ) -> Engine:
        compiled_executors = executors(implementation)
        core = [
            MechanicFactory.mechanics(m, compiled_executors, mock_relations)
            for m in mock_configurations_schema.mechanics.core
        ]
        world = [
            MechanicFactory.mechanics(m, compiled_executors, mock_relations)
            for m in mock_configurations_schema.mechanics.world
        ]
        return Engine(
            board=mock_board,
            screens={"0": mock_screen},
            core=core,
            world=world,
            provider=mock_provider,
            registry=mock_registry,
        )

    return _engine


@pytest.fixture
def mock_engine(engine) -> Engine:
    return engine()