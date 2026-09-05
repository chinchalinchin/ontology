import pytest
import math
from app.game.logic.mechanics.motion import motive

def test_motive_no_intention(mock_board_assets):
    sprite = mock_board_assets[0]
    sprite.state.intention = "IDLE" 
    sprite.state.velocity.vx = 5.0
    sprite.state.velocity.vy = 5.0
    
    motive.update([sprite], 1.0)
    
    # When sprite is idle, motives are removed
    assert sprite.state.velocity.vx == 0.0
    assert sprite.state.velocity.vy == 0.0

def test_motive_at_goal(mock_board_assets, monkeypatch):
    sprite = mock_board_assets[0]
    monkeypatch.setattr('app.game.logic.mechanics.motion.motive.NavigationIntentions', ["FIND"])
    sprite.state.intention = "FIND"
    
    sprite.state.position.x = 10
    sprite.state.position.y = 10
    sprite.state.goal.position.x = 10
    sprite.state.goal.position.y = 10
    
    sprite.state.velocity.vx = 5.0
    
    motive.update([sprite], 1.0)
    
    assert sprite.state.velocity.vx == 0.0
    assert sprite.state.velocity.vy == 0.0

def test_motive_accelerates_towards_goal(mock_board_assets, monkeypatch):
    sprite = mock_board_assets[0]
    monkeypatch.setattr('app.game.logic.mechanics.motion.motive.NavigationIntentions', ["FIND"])
    sprite.state.intention = "FIND"
    
    sprite.state.position.x = 0
    sprite.state.position.y = 0
    sprite.state.goal.position.x = 100
    sprite.state.goal.position.y = 0
    
    sprite.state.character.speed = 20
    sprite.state.character.impulse = 5
    sprite.state.velocity.vx = 0.0
    sprite.state.velocity.vy = 0.0
    
    motive.update([sprite], 1.0)
    
    assert sprite.state.velocity.vx == 5.0
    assert sprite.state.velocity.vy == 0.0

def test_motive_clamps_to_speed(mock_board_assets, monkeypatch):
    sprite = mock_board_assets[0]
    monkeypatch.setattr('app.game.logic.mechanics.motion.motive.NavigationIntentions', ["FIND"])
    sprite.state.intention = "FIND"
    
    sprite.state.position.x = 0
    sprite.state.position.y = 0
    sprite.state.goal.position.x = 100
    sprite.state.goal.position.y = 0
    
    sprite.state.character.speed = 10
    sprite.state.character.impulse = 15
    sprite.state.velocity.vx = 0.0
    
    motive.update([sprite], 1.0)
    
    # Impulse pushes speed to 15, but magnitude clamping prevents exceeding 10
    assert sprite.state.velocity.vx == 10.0

def test_motive_arrival_clamp(mock_board_assets, monkeypatch):
    sprite = mock_board_assets[0]
    monkeypatch.setattr('app.game.logic.mechanics.motion.motive.NavigationIntentions', ["FIND"])
    sprite.state.intention = "FIND"
    
    sprite.state.position.x = 0
    sprite.state.position.y = 0
    sprite.state.goal.position.x = 5
    sprite.state.goal.position.y = 0
    
    sprite.state.character.speed = 20
    sprite.state.character.impulse = 5
    
    # distance (5) is less than speed * delta (20 * 1.0)
    # Velocity scales exactly to reach the goal to prevent jitter oscillation 
    motive.update([sprite], 1.0)
    
    assert sprite.state.velocity.vx == 5.0
    assert sprite.state.velocity.vy == 0.0