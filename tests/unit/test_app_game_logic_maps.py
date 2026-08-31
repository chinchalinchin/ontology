"""
# Ontology: tests.unit.test_app_game_logic_maps.py
"""
import pytest
from unittest.mock import MagicMock

from app.game.logic.maps import AnimationMap
from app.config.enums import Intentions, Actions, Directions
from libs.core.models import Position

def test_animation_map_action_idle():
    state = MagicMock(intention=Intentions.IDLE)
    assert AnimationMap.action(state, None) == Actions.WALK.value

def test_animation_map_action_attack_unarmed():
    state = MagicMock(intention=Intentions.ATTACK)
    state.inventory.equipment.weapon = None
    assert AnimationMap.action(state, None) == Actions.CAST.value

def test_animation_map_action_attack_armed():
    state = MagicMock(intention=Intentions.ATTACK)
    state.inventory.equipment.weapon = "shortsword"
    
    equipment = MagicMock()
    weapon_props = MagicMock()
    weapon_props.actions = {"slash": MagicMock()}
    equipment.weapons = {"shortsword": weapon_props}
    
    assert AnimationMap.action(state, equipment) == "slash"

def test_animation_map_direction_down():
    pos = Position(10, 10)
    target = Position(10, 20)
    assert AnimationMap.direction(pos, target) == Directions.DOWN.value

def test_animation_map_direction_up():
    pos = Position(10, 20)
    target = Position(10, 10)
    assert AnimationMap.direction(pos, target) == Directions.UP.value

def test_animation_map_direction_right():
    pos = Position(10, 10)
    target = Position(20, 10)
    assert AnimationMap.direction(pos, target) == Directions.RIGHT.value

def test_animation_map_direction_left():
    pos = Position(20, 10)
    target = Position(10, 10)
    assert AnimationMap.direction(pos, target) == Directions.LEFT.value