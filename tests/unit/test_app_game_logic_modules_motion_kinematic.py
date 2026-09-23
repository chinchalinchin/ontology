"""
# Ontology: tests.unit.test_app_game_logic_modules_motion_kinematic.py
"""
# Standard Libraries
import math

# External Libraries
import pytest

from app.game.logic.modules.motion import kinematic
from app.config.enums import PlayerGoals
from app.models.state import (
    DevicePayload, 
    WorldPayload, 
    MenuPayload
)

def test_kinematic_movement_orthogonal(mock_player):
    payload = DevicePayload(
        world=WorldPayload(goals=[PlayerGoals.UP]),
        menu=MenuPayload()
    )
    
    kinematic.update([mock_player], payload, 1.0)
    
    assert mock_player.state.velocity.vx == 0.0
    assert mock_player.state.velocity.vy == -10.0

def test_kinematic_movement_diagonal(mock_player):
    payload = DevicePayload(
        world=WorldPayload(goals=[PlayerGoals.UP, PlayerGoals.RIGHT]),
        menu=MenuPayload()
    )
    
    kinematic.update([mock_player], payload, 1.0)
    
    expected_velocity = 10.0 / math.sqrt(2)
    assert math.isclose(mock_player.state.velocity.vx, expected_velocity, rel_tol=1e-4)
    assert math.isclose(mock_player.state.velocity.vy, -expected_velocity, rel_tol=1e-4)

def test_kinematic_no_movement(mock_player):
    mock_player.state.velocity.vx = 5.0
    mock_player.state.velocity.vy = 5.0
    
    # Input ceases
    payload = DevicePayload(
        world=WorldPayload(goals=[]),
        menu=MenuPayload()
    )
    
    kinematic.update([mock_player], payload, 1.0)
    
    # Velocity should immediately decay to zero due to kinemetic physics behavior
    assert mock_player.state.velocity.vx == 0.0
    assert mock_player.state.velocity.vy == 0.0

def test_kinematic_axis_snap(mock_player):    
    # Provide an initial diagonal trajectory
    mock_player.state.velocity.vx = 5.0
    mock_player.state.velocity.vy = 5.0
    
    # User begins strictly holding right
    payload = DevicePayload(
        world=WorldPayload(goals=[PlayerGoals.RIGHT]),
        menu=MenuPayload()
    )
    
    kinematic.update([mock_player], payload, 1.0)
    
    assert mock_player.state.velocity.vx == 10.0
    assert mock_player.state.velocity.vy == 0.0