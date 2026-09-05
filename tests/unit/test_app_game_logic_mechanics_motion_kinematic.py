import pytest
import math
from app.game.logic.mechanics.motion import kinematic
from app.config.enums import PlayerGoals
from app.models.state import DevicePayload, WorldPayload, MenuPayload

def test_kinematic_movement_orthogonal(mock_board_assets):
    player = mock_board_assets[2]
    player.state.character.speed = 10
    
    payload = DevicePayload(
        world=WorldPayload(goals=[PlayerGoals.UP]),
        menu=MenuPayload()
    )
    
    kinematic.update([player], payload, 1.0)
    
    assert player.state.velocity.vx == 0.0
    assert player.state.velocity.vy == -10.0

def test_kinematic_movement_diagonal(mock_board_assets):
    player = mock_board_assets[2]
    player.state.character.speed = 10
    
    payload = DevicePayload(
        world=WorldPayload(goals=[PlayerGoals.UP, PlayerGoals.RIGHT]),
        menu=MenuPayload()
    )
    
    kinematic.update([player], payload, 1.0)
    
    expected_velocity = 10.0 / math.sqrt(2)
    assert math.isclose(player.state.velocity.vx, expected_velocity, rel_tol=1e-4)
    assert math.isclose(player.state.velocity.vy, -expected_velocity, rel_tol=1e-4)

def test_kinematic_no_movement(mock_board_assets):
    player = mock_board_assets[2]
    player.state.velocity.vx = 5.0
    player.state.velocity.vy = 5.0
    
    # Input ceases
    payload = DevicePayload(
        world=WorldPayload(goals=[]),
        menu=MenuPayload()
    )
    
    kinematic.update([player], payload, 1.0)
    
    # Velocity should immediately decay to zero due to kinemetic physics behavior
    assert player.state.velocity.vx == 0.0
    assert player.state.velocity.vy == 0.0

def test_kinematic_axis_snap(mock_board_assets):
    player = mock_board_assets[2]
    player.state.character.speed = 10
    
    # Provide an initial diagonal trajectory
    player.state.velocity.vx = 5.0
    player.state.velocity.vy = 5.0
    
    # User begins strictly holding right
    payload = DevicePayload(
        world=WorldPayload(goals=[PlayerGoals.RIGHT]),
        menu=MenuPayload()
    )
    
    kinematic.update([player], payload, 1.0)
    
    assert player.state.velocity.vx == 10.0
    assert player.state.velocity.vy == 0.0