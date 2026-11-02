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
from typing import (
    Any,
    List
)
from unittest.mock import MagicMock

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
from app.game.logic.relations import (
    MaterialIndex,
    ShorelineIndex,
)
from app.game.screen import Screen
from app.models.config import (
    ConfigurationSchema,
    MechanicsInstance,
)
from app.models.groups import EquipmentGroup
from app.models.properties import PropertiesSchema
from app.models.state import StateSchema
from app.models.state.devices import (
    DevicePayload, 
    WorldPayload, 
    MenuPayload
)

from app.services.factories import MechanicFactory
from app.services.generators.game import (
    Actuator,
    Cartographer,
    Cradle,
    Perimeter
)
from app.services.generators.menus import Provider
from app.static.semantics import (
    AssetInstances,
    Devices,
    PlayerGoals
)

# Cython Libraries
from libs.core.models import Dimensions
from libs.graphics.registry import (
    Registry,
    TTFFont,
)

# ---------------------------------------------------------------------------
# ----------------------------------------------- SUBSYSTEMS & ASSET REGISTRY
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_render(monkeypatch) -> MagicMock:
    """
    Patches Cython SDL rendering calls on app.game.screen.render and
    libs.graphics.registry.render so no textures are rendered during unit tests.
    """
    mock = MagicMock()
    mock.canvas.side_effect = lambda w, l, opaque=False: MagicMock(
        w=w, l=l, opaque=opaque
    )
    mock.compose.side_effect = lambda base, overlays: MagicMock(
        w=getattr(base, "w", 64),
        l=getattr(base, "l", 64),
    )
    monkeypatch.setattr("app.game.screen.render", mock)
    monkeypatch.setattr("libs.graphics.registry.render", mock)
    return mock


@pytest.fixture
def mock_registry(
    monkeypatch,
    mock_render: MagicMock,
    mock_material_index: MaterialIndex,
    mock_properties_schema: PropertiesSchema,
    mock_configurations_schema: ConfigurationSchema,
) -> Registry:
    monkeypatch.setattr(
        "libs.graphics.registry._sys_load_image",
        MagicMock(side_effect=lambda *args, **kwargs: MagicMock(w=64, l=64)),
    )
    monkeypatch.setattr(
        "libs.graphics.registry._sys_load_font",
        MagicMock(side_effect=lambda *args, **kwargs: TTFFont()),
    )
    registry = Registry(
        properties=mock_properties_schema,
        recipes=mock_configurations_schema.recipes,
    )
    yield registry
    registry._textures.clear()
    registry.clear()


# ---------------------------------------------------------------------------
# ------------------------------------------------------------------- DEVICES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_device(mock_configurations_schema: ConfigurationSchema):
    """
    Fixture factory instantiating an input Device via MechanicFactory.
    """
    def _device(kind: str = Devices.KEYBOARD.value) -> Device:
        mapping = getattr(mock_configurations_schema.mappings, kind)
        return MechanicFactory.device(kind, mapping)

    return _device


@pytest.fixture
def mock_keyboard(mock_device) -> Keyboard:
    return mock_device(Devices.KEYBOARD.value)


@pytest.fixture
def mock_payload():
    def _payload(goals: List[str] = [], intention: str = None):
        return DevicePayload(
                world=WorldPayload(
                    goals=goals,
                    intention=intention
                ),
                menu=MenuPayload()
            )

    return _payload
            
# ---------------------------------------------------------------------------
# ------------------------------------------------------------------- SCREEN
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_screen(
    mock_registry: Registry,
    mock_state_schema: StateSchema,
    mock_render: MagicMock,
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
    mock_actuator: Actuator,
    mock_shoreline_index: ShorelineIndex,
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

    for layer in board.layers():
        board.perimeters[layer] = Perimeter.generate(board, layer)

    fluids = board.instances(AssetInstances.FLUIDS.value)
    for layer in {f.state.layer for f in fluids}:
        for fluid in board.instances(AssetInstances.FLUIDS.value, layer):
            mock_actuator.propagate(fluid, board)
        board.update_fluid_cache(layer)
        board.set_moisture_field(
            layer,
            mock_actuator.compile_moisture_field(layer, board),
        )
        shores = Cartographer.generate(layer, board, mock_shoreline_index)
        if shores:
            board.add(shores)

    return board


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------- MECHANICS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mechanic(
    mock_configurations_schema: ConfigurationSchema,
    mock_executors,
    mock_relations: dict[str, Any],
):
    """
    Fixture factory instantiating a Mechanic by name and translator implementation.
    """
    configured = {
        m.key: m
        for m in (
            mock_configurations_schema.mechanics.core
            + mock_configurations_schema.mechanics.world
        )
    }

    def _mechanic(
        name: str,
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ) -> Mechanic:
        instance_cfg = configured.get(name, MechanicsInstance(name))
        return MechanicFactory.mechanics(
            instance_cfg,
            mock_executors(implementation),
            mock_relations,
        )

    return _mechanic


# ---------------------------------------------------------------------------
# -------------------------------------------------------------- ENGINE & BUS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bus() -> collections.deque:
    return collections.deque()


@pytest.fixture
def mock_engine(
    mock_board: Board,
    mock_screen: Screen,
    mock_configurations_schema: ConfigurationSchema,
    mock_relations: dict[str, Any],
    mock_provider: Provider,
    mock_registry: Registry,
    mock_executors,
):
    """
    Fixture factory constructing an Engine parameterized by translator implementation ('lambda' or 'compiler').
    """
    def _engine(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ) -> Engine:
        compiled_executors = mock_executors(implementation)
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

    return _engine()