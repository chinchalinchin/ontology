"""
# Ontology: tests.unit.app.game.logic.modules.maps.test_animation_maps
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.modules.maps import AnimationMap
from app.config.enums import (
    Intentions, 
    Actions, 
    Directions
)

# Cython Libraries
from libs.core.models import Position

@pytest.mark.animations
def test_animation_map_action_idle(mock_board):
    player = mock_board.player()
    player.state.intention = Intentions.IDLE.value

    assert AnimationMap.action(
        player.state, 
        mock_board.equipment
    ) == Actions.WALK.value


@pytest.mark.animations
def test_animation_map_action_attack_unarmed(mock_board):
    player = mock_board.player()
    player.state.intention = Intentions.ATTACK.value
    player.state.inventory.equipment.weapon = None

    assert AnimationMap.action(
        player.state, 
        mock_board.equipment
    ) == Actions.CAST.value


@pytest.mark.animations
def test_animation_map_action_attack_armed(mock_board):
    player = mock_board.player()
    player.state.intention = Intentions.ATTACK.value
    player.state.inventory.equipment.weapon = "shortsword"
    
    assert AnimationMap.action(
        player.state, 
        mock_board.equipment
    ) == Actions.SLASH.value 


@pytest.mark.animations
def test_animation_map_direction_down():
    pos = Position(10, 10)
    target = Position(10, 20)
    assert AnimationMap.direction(pos, target) == Directions.DOWN.value


@pytest.mark.animations
def test_animation_map_direction_up():
    pos = Position(10, 20)
    target = Position(10, 10)
    assert AnimationMap.direction(pos, target) == Directions.UP.value


@pytest.mark.animations
def test_animation_map_direction_right():
    pos = Position(10, 10)
    target = Position(20, 10)
    assert AnimationMap.direction(pos, target) == Directions.RIGHT.value


@pytest.mark.animations
def test_animation_map_direction_left():
    pos = Position(20, 10)
    target = Position(10, 10)
    assert AnimationMap.direction(pos, target) == Directions.LEFT.value