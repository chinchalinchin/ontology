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
from app.config.enums import Executors

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Boundary
)

# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK COMPONENTS
# ---------------------------------------------------------------------------

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
    with patch('app.game.board.settings.TILE_HASH_SIZE', 32):
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
    mock_relations
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
        provider=MagicMock()
    )


@pytest.fixture
def mock_engine_with_compiler_transitions(
    mock_board, 
    mock_mechanics_configuration,
    mock_compiler_executors,
    mock_relations
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
        provider=MagicMock()
    )