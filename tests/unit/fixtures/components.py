"""
# Ontology: tests.unit.fixtures.components

Mock application component fixtures
"""
# Standard Libraries
from unittest.mock import (
    MagicMock, 
    patch
)
import collections

# External Libraries
import pytest

# Application Libraries
from app.game.devices import Keyboard
from app.game.board import Board
from app.game.engine import Engine
from app.services.generators.game.factory import Factory
from app.services.translators import (
    LambdaTranslator,
    CompilerTranslator
)
from app.services.generators.menus.provider import Provider
from app.services.generators.menus.fabricator import Fabricator
from app.services.generators.menus.binder import Binder
from app.services.generators.menus.library import Library
from app.config.enums import Executors

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Boundary
)

class RenderStubScreen:
    """
    Screen double that stubs low-level SDL rendering passes without mocking engine logic.
    """
    def __init__(self, screensize, boardsize, tiles, registry):
        self.screensize = screensize
        self.boardsize = boardsize
        self.tiles = tiles
        self.registry = registry
        self.cleared = False
        self.drawn_assets = []
        self.presented = False

    def clear(self) -> None:
        self.cleared = True

    def draw(self, assets, position, dimensions) -> None:
        self.drawn_assets = list(assets)

    def interface(self, menus, overlays) -> None:
        pass

    def present(self) -> None:
        self.presented = True

    def destroy(self) -> None:
        pass

# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK COMPONENTS
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_screen(mock_registry) -> RenderStubScreen:
    return RenderStubScreen(
        screensize=Dimensions(320, 240),
        boardsize=Dimensions(640, 480),
        tiles=[],
        registry=mock_registry
    )

@pytest.fixture
def mock_registry() -> MagicMock:
    registry = MagicMock()
    registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 32, 32)
    return registry


@pytest.fixture
def mock_board(
    mock_assets, 
    mock_configurations, 
    mock_equipment,
    mock_cradle,
    mock_keyboard
) -> Board:    
    board = Board(
        assets=mock_assets, 
        configurations=mock_configurations, 
        equipment=mock_equipment
    )
    board.perimeters["0"] = [
        Boundary(Position(0, 0), Dimensions(320, 1)),
        Boundary(Position(0, 319), Dimensions(320, 1)),
        Boundary(Position(0, 0), Dimensions(1, 320)),
        Boundary(Position(319, 0), Dimensions(1, 320))
    ]
    board.set_cradle(mock_cradle)
    board.set_device(mock_keyboard)
    return board


@pytest.fixture
def mock_keyboard(
    mock_mapping_configuration
) -> Keyboard:
    return Keyboard(mock_mapping_configuration.keyboard)


@pytest.fixture
def mock_lambda_executors(
    mock_actuator,
    mock_configurations,
):
    translator = LambdaTranslator()
    intention_executor = translator.compile(mock_configurations.intentions)
    plot_executor = translator.compile(mock_configurations.plots)
    
    return {
        Executors.INTENTION.value: intention_executor,
        Executors.PLOT.value: plot_executor,
        Executors.ACTUATOR.value: mock_actuator
    }


@pytest.fixture
def mock_compiler_executors(
    mock_actuator,
    mock_configurations,
):
    translator = CompilerTranslator()
    intention_executor = translator.compile(mock_configurations.intentions)
    plot_executor = translator.compile(mock_configurations.plots)
    
    return {
        Executors.INTENTION.value: intention_executor,
        Executors.PLOT.value: plot_executor,
        Executors.ACTUATOR.value: mock_actuator
    }


@pytest.fixture
def mock_bus() -> collections.deque:
    return collections.deque()


@pytest.fixture
def mock_relations(mock_shoreline_index) -> dict:
    from app.config.enums import Relations
    return {
        Relations.SHORELINES.value: mock_shoreline_index
    }


@pytest.fixture
def mock_engine_with_lambda_transitions(
    mock_board, 
    mock_mechanics_configuration,
    mock_lambda_executors,
    mock_relations,
    mock_provider
) -> Engine:
    """
    Fully constructs the Engine with live Mechanics and Executors
    """
    world_mechanics = [
        Factory.mechanics(m, mock_lambda_executors, mock_relations) 
        for m in mock_mechanics_configuration.world
    ]

    return Engine(
        board=mock_board,
        screens={},
        core=[],
        world=world_mechanics,
        provider=mock_provider
    )


@pytest.fixture
def mock_engine_with_compiler_transitions(
    mock_board, 
    mock_mechanics_configuration,
    mock_compiler_executors,
    mock_relations,
    mock_provider
) -> Engine:
    """
    Fully constructs the Engine with live Mechanics and Executors
    """  
    world_mechanics = [
        Factory.mechanics(m, mock_compiler_executors, mock_relations) 
        for m in mock_mechanics_configuration.world
    ]

    return Engine(
        board=mock_board,
        screens={},
        core=[],
        world=world_mechanics,
        provider=mock_provider
    )

@pytest.fixture
def mock_engine_core(
    mock_board,
    mock_screen,
    mock_provider
) -> Engine:
    """
    Constructs an Engine with a live Board, live buses, concrete handlers, and stubbed rendering.
    """

    return Engine(
        board=mock_board,
        screens={"0": mock_screen},
        core=[],
        world=[],
        provider=mock_provider
    )