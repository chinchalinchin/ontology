"""
# Ontology: tests.unit.conftest
"""
# Standard Libraries
from unittest.mock import (
    MagicMock, 
    patch
)

# External Libraries
import pytest

from app.game.devices import Keyboard
from app.game.board import Board
from app.game.logic.relations import ShorelineIndex
from app.services.orchestration import (
    Builder, 
    Orchestrator
)
from app.services.generators.menus import (
    Provider,
    Binder
)
from app.services.generators.game import (
    Decomposer,
    Cradle,
    Actuator
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Boundary
)
from libs.core.math.space import Space



# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK LIBRARIES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_registry() -> MagicMock:
    registry = MagicMock()
    registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 32, 32)
    return registry


@pytest.fixture
def mock_boundary() -> Boundary:
    """Boundary spatial constraint fixture."""
    return Boundary(Position(10, 20), Dimensions(30, 40))


@pytest.fixture
def mock_space_grid() -> Space:
    """
    Fixture providing an initialized Cython Space grid for testing 
    O(1) bucket lookups and broad-phase physics.
    """
    return Space(cell_size=64, max_entities=100)


# ---------------------------------------------------------------------------
# ------------------------------------------------------------- MOCK SERVICES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_decomposer(
    mock_composition_configuration, 
    mock_recipes_configuration,
    mock_properties,
) -> Decomposer:
    # 1. Setup mock properties with costs for aggregation
    return Decomposer(
        compositions=mock_composition_configuration, 
        properties=mock_properties,
        recipes=mock_recipes_configuration
    )


@pytest.fixture
def mock_binder(mock_registry) -> Binder:
    return Binder(
        registry=mock_registry, 
        library=MagicMock()
    )


@pytest.fixture
def mock_builder(
    mock_properties, 
    mock_configurations, 
    mock_state
):
    with patch('app.services.orchestration.builder.Loader') as mock_loader:
        mock_loader.load_properties.return_value = mock_properties
        mock_loader.load_configurations.return_value = mock_configurations
        mock_loader.load_state.return_value = mock_state
        
        yield Builder()


@pytest.fixture
def mock_orchestrator(mock_builder) -> Orchestrator:
    return Orchestrator(mock_builder)


@pytest.fixture
def mock_provider(
    mock_binder, 
    mock_recipes_configuration, 
    mock_widget_properties
) -> Provider:
    return Provider(
        recipes=mock_recipes_configuration.widgets, 
        properties=mock_widget_properties, 
        binder=mock_binder
    )


@pytest.fixture
def mock_cradle(
    mock_decomposer,
    mock_recipes_configuration,
    mock_spawnables
):
    return Cradle(mock_spawnables, mock_recipes_configuration, mock_decomposer)


@pytest.fixture
def mock_actuator(
    mock_shoreline_index
) -> Actuator:
    return Actuator(shorelines=mock_shoreline_index)


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK COMPONENTS
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_board(
    mock_assets, 
    mock_configurations, 
    mock_equipment,
    mock_cradle
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
        return board


@pytest.fixture
def mock_keyboard(
    mock_mapping_configuration
) -> Keyboard:
    return Keyboard(mock_mapping_configuration.keyboard)

@pytest.fixture
def mock_shoreline_index(mock_geography_properties):
    """ShorelineIndex fixture compiled from mock properties."""
    return ShorelineIndex.from_properties(mock_geography_properties.shorelines)

