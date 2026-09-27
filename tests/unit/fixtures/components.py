"""
# Ontology: tests.unit.fixtures.components

Application component fixtures
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
