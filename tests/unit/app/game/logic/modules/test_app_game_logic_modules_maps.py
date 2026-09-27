"""
# Ontology: tests.unit.test_app_game_logic_maps.py
"""
import pytest
from unittest.mock import MagicMock

from app.game.logic.modules.maps import AnimationMap, CombatMap
from app.config.enums import Intentions, Actions, Directions
from libs.core.models import Position, Dimensions, Hitbox
from app.models.state import SpriteState, AnimationState, Inventory, Equipment
from app.models.properties import SheetProperties
from app.models.groups import EquipmentGroup


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


def test_combat_map_attackboxes_unarmed():
    state = SpriteState(id="player", inventory=Inventory(equipment=Equipment(weapon=None)))
    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={})
    assert CombatMap.attackboxes(state, equipment) == []


def test_combat_map_attackboxes_missing_weapon_properties():
    state = SpriteState(id="player", inventory=Inventory(equipment=Equipment(weapon="dagger")))
    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={})
    assert CombatMap.attackboxes(state, equipment) == []


def test_combat_map_attackboxes_matching_frame():
    hitbox = Hitbox(Position(10, 15), Dimensions(20, 25))
    props = SheetProperties(
        dimensions=Dimensions(64, 64),
        attackboxes={"slash-right-3": [hitbox]}
    )
    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={"shortsword": props})
    state = SpriteState(
        id="player",
        inventory=Inventory(equipment=Equipment(weapon="shortsword")),
        animation=AnimationState(action="slash", direction="right", frame=3)
    )

    boxes = CombatMap.attackboxes(state, equipment)
    assert len(boxes) == 1
    assert boxes[0] == hitbox


def test_combat_map_attackboxes_unmatched_frame():
    props = SheetProperties(
        dimensions=Dimensions(64, 64),
        attackboxes={"slash-right-3": [Hitbox(Position(10, 15), Dimensions(20, 25))]}
    )
    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={"shortsword": props})
    state = SpriteState(
        id="player",
        inventory=Inventory(equipment=Equipment(weapon="shortsword")),
        animation=AnimationState(action="slash", direction="right", frame=0)
    )

    assert CombatMap.attackboxes(state, equipment) == []