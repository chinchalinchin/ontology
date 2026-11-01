"""
@domain.test
@test.unit
@physics.motion
@workflow.player

# Ontology: Tests - tests.unit.app.game.logic.modules.motion.test_kinematic

Unit tests for the kinematic motion module.
"""
# Standard Libraries
import math

# External Libraries
import pytest

# Application Libraries
from app.game.logic.modules.motion import kinematic
from app.static.semantics import (
    PlayerGoals
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.physics_motion,
    pytest.mark.workflow_player
]

# -----------------------------------------------------

def test_kinematic_movement_orthogonal(
    mock_board,
    mock_payload
):
    mock_player = mock_board.player()
    payload = mock_payload(goals=[PlayerGoals.UP.value]) 
    
    kinematic.update([mock_player], payload, 1.0)
    
    assert mock_player.state.velocity.vx == 0.0
    assert mock_player.state.velocity.vy == -10.0


def test_kinematic_movement_diagonal(
    mock_board,
    mock_payload
):
    mock_player = mock_board.player()
    payload = mock_payload(goals=[PlayerGoals.UP, PlayerGoals.RIGHT])
    
    kinematic.update([mock_player], payload, 1.0)
    
    expected_velocity = 10.0 / math.sqrt(2)
    assert math.isclose(
        mock_player.state.velocity.vx, 
        expected_velocity, 
        rel_tol=1e-4
    )
    assert math.isclose(
        mock_player.state.velocity.vy, 
        -expected_velocity, 
        rel_tol=1e-4
    )


def test_kinematic_no_movement(
    mock_board,
    mock_payload
):
    mock_player = mock_board.player()
    mock_player.state.velocity.vx = 5.0
    mock_player.state.velocity.vy = 5.0
    
    # Input ceases
    payload = mock_payload(goals=[], intention=None, menus=[])
    
    kinematic.update([mock_player], payload, 1.0)
    
    # Velocity should immediately decay to zero due to kinemetic physics behavior
    assert mock_player.state.velocity.vx == 0.0
    assert mock_player.state.velocity.vy == 0.0


def test_kinematic_axis_snap(
    mock_board,
    mock_payload
):    
    mock_player = mock_board.player()
    # Provide an initial diagonal trajectory
    mock_player.state.velocity.vx = 5.0
    mock_player.state.velocity.vy = 5.0
    
    # User begins strictly holding right
    payload = mock_payload(goals=[PlayerGoals.RIGHT])
    
    kinematic.update([mock_player], payload, 1.0)
    
    assert mock_player.state.velocity.vx == 10.0
    assert mock_player.state.velocity.vy == 0.0