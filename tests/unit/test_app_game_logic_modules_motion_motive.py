"""
# Ontology: tests.unit.test_app_game_logic_modules_motion_motive
"""
import pytest
from app.config.enums import Intentions, Goals
from app.game.logic.modules.motion import motive
from app.assets.base import Taxonomy, Asset
from app.models.state import (
    SpriteState, 
    Inventory, 
    Equipment, 
    Character, 
    AnimationState, 
    Goal
)
from app.models.properties import SheetProperties
from libs.core.models import Position, Dimensions, Velocity

# fixtures
from conftest import DummyFrame, DummyAnimation

def test_motive_no_intention(mock_board, mock_board_assets):
    sprite = mock_board_assets[0]
    sprite.state.intention = "IDLE" 
    sprite.state.velocity.vx = 5.0
    sprite.state.velocity.vy = 5.0
    
    motive.update([sprite], mock_board, 1.0)
    
    # When sprite is idle, motives are removed
    assert sprite.state.velocity.vx == 0.0
    assert sprite.state.velocity.vy == 0.0

def test_motive_at_goal(mock_board, mock_board_assets, monkeypatch):
    sprite = mock_board_assets[0]
    monkeypatch.setattr('app.game.logic.modules.motion.motive.NavigationIntentions', ["FIND"])
    sprite.state.intention = "FIND"
    
    sprite.state.position.x = 10
    sprite.state.position.y = 10
    sprite.state.goal.position.x = 10
    sprite.state.goal.position.y = 10
    
    sprite.state.velocity.vx = 5.0
    
    motive.update([sprite], mock_board, 1.0)
    
    assert sprite.state.velocity.vx == 0.0
    assert sprite.state.velocity.vy == 0.0

def test_motive_aims_towards_goal(mock_board, mock_board_assets, monkeypatch):
    sprite = mock_board_assets[0]
    monkeypatch.setattr('app.game.logic.modules.motion.motive.NavigationIntentions', ["FIND"])
    sprite.state.intention = "FIND"
    
    # Reposition player outside squeeze radius (30) so path is clear of neighbors
    player = mock_board.player()
    if player:
        player.state.position = Position(500, 500)

    sprite.state.position.x = 0
    sprite.state.position.y = 0
    sprite.state.goal.position.x = 100
    sprite.state.goal.position.y = 0
    
    sprite.state.character.speed = 20
    sprite.state.velocity.vx = 0.0
    sprite.state.velocity.vy = 0.0
    
    motive.update([sprite], mock_board, 1.0)
    
    # Preferred velocity aims directly towards goal scaled to speed via physics.aim
    assert sprite.state.velocity.vx == 20.0
    assert sprite.state.velocity.vy == 0.0

    
def test_motive_rvo_opposing_corridor_steering(mock_board, mock_board_assets, monkeypatch):
    monkeypatch.setattr('app.game.logic.modules.motion.motive.NavigationIntentions', ["FIND"])
    
    sprite1 = mock_board_assets[0]
    sprite1.state.layer = "0"
    sprite1.state.intention = Intentions.FIND
    sprite1.state.position = Position(0, 50)
    sprite1.state.goal = Goal(name="target2", category=Goals.POSITION.value, layer="0", position=Position(100, 50))
    sprite1.state.character.speed = 10
    sprite1.state.velocity = Velocity(10.0, 0.0)

    tax2 = Taxonomy("sprite-2", "npc_2", "sheets", "sprites")
    props2 = SheetProperties(dimensions=Dimensions(w=32, l=32), mass=10)
    state2 = SpriteState(
        id="sprite-2", name="npc_2", layer="0",
        position=Position(60, 50),
        intention=Intentions.FIND,
        goal=Goal(name="target1", category=Goals.POSITION.value, layer="0", position=Position(0, 50)),
        character=Character(speed=10),
        velocity=Velocity(-10.0, 0.0),
        inventory=Inventory(equipment=Equipment()),
        animation=AnimationState()
    )
    sprite2 = Asset(tax2, props2, state2, DummyFrame(), DummyAnimation())
    mock_board.add([sprite2])

    motive.update([sprite1, sprite2], mock_board, 1.0)

    # RVO avoidance must cause lateral steering deviation or velocity adjustment
    assert sprite1.state.velocity.vx != 10.0 or sprite1.state.velocity.vy != 0.0