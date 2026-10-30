"""
@domain.test
@domain.logic
@test.unit
@app.semantics

# Ontology: Tests - tests.unit.app.game.logic.modules.test_predicates

Predicate Unit tests.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Directions,
)
from app.game.logic import predicates

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_board,
    pytest.mark.app_core,
    pytest.mark.app_component,
]

# -----------------------------------------------------


@pytest.mark.workflow_collisions
def test_board_predicates_classification(mock_board):
    """
    Validates pure predicates for physical weights and navigational obstacles.
    """
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    sign = mock_board.instances(AssetInstances.SIGNS.value)[0]
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    player = mock_board.player()

    # Weight qualification
    assert predicates.is_weight(crate) is True
    assert predicates.is_weight(player) is True
    assert predicates.is_weight(sign) is False
    assert predicates.is_weight(fluid) is False

    # Obstacle qualification
    assert predicates.is_obstacle(crate) is True
    assert predicates.is_obstacle(sign) is True
    assert predicates.is_obstacle(player) is False
    assert predicates.is_obstacle(fluid) is False


@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_board_predicates_fluid_containment(mock_board):
    """
    Tests pure stream and pool containment predicates without referencing Board.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]

    # Stream is at (64, 64), 96x32 dimensions, DOWN, length=96
    fluid.state.position = Position(64, 64)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 96
    fluid.state.pool = None
    fluid.state.branches = []

    # Inside stream corridor (x in [64, 160], y in [64, 160])
    inside_pos = Position(70, 80)
    assert predicates.in_stream(inside_pos, fluid) is True
    assert predicates.in_fluid(inside_pos, fluid) is True

    # Outside stream corridor
    outside_pos = Position(200, 80)
    assert predicates.in_stream(outside_pos, fluid) is False
    assert predicates.in_fluid(outside_pos, fluid) is False