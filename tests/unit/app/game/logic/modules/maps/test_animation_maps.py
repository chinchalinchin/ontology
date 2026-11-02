"""
@domain.test
@test.unit
@app.module
@modality.action
@modality.intention

# Ontology: Tests - tests.unit.app.game.logic.modules.maps.test_animation

Unit tests for AnimationMap.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.modules.maps.animation import AnimationMap
from app.static.semantics import (
    Actions,
    AssetCategories,
    AssetInstances,
    Directions,
    Intentions,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_module,
    pytest.mark.modality_action,
    pytest.mark.modality_intention,
]

# -----------------------------------------------------


def test_animation_map_static_intentions(mock_state, mock_equipment):
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    for intention in (
        Intentions.IDLE.value,
        Intentions.SPEAK.value,
        Intentions.BARTER.value,
        Intentions.THREATEN.value,
    ):
        state.intention = intention
        assert AnimationMap.action(state, mock_equipment) == Actions.WALK.value


def test_animation_map_attack_weapons(mock_state, mock_equipment):
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    state.intention = Intentions.ATTACK.value

    state.inventory.equipment.weapon = None
    assert AnimationMap.action(state, mock_equipment) == Actions.CAST.value

    state.inventory.equipment.weapon = "shortsword"
    assert AnimationMap.action(state, mock_equipment) == Actions.SLASH.value

    state.inventory.equipment.weapon = "spear"
    assert AnimationMap.action(state, mock_equipment) == Actions.THRUST.value

    state.inventory.equipment.weapon = "longbow"
    assert AnimationMap.action(state, mock_equipment) == Actions.SHOOT.value


def test_animation_map_mine_and_build(mock_state, mock_equipment):
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )

    state.intention = Intentions.MINE.value
    state.inventory.equipment.tool = None
    assert AnimationMap.action(state, mock_equipment) == Actions.THRUST.value

    state.inventory.equipment.tool = "axe"
    assert AnimationMap.action(state, mock_equipment) == Actions.SLASH.value

    state.inventory.equipment.tool = "pickaxe"
    assert AnimationMap.action(state, mock_equipment) == Actions.THRUST.value

    state.intention = Intentions.BUILD.value
    state.inventory.equipment.utility = None
    assert AnimationMap.action(state, mock_equipment) == Actions.CAST.value

    state.inventory.equipment.utility = "lantern"
    assert AnimationMap.action(state, mock_equipment) == Actions.CAST.value


def test_animation_map_directions():
    origin = Position(50, 50)
    assert AnimationMap.direction(origin, Position(50, 80)) == Directions.DOWN.value
    assert AnimationMap.direction(origin, Position(50, 20)) == Directions.UP.value
    assert AnimationMap.direction(origin, Position(20, 50)) == Directions.LEFT.value
    assert AnimationMap.direction(origin, Position(80, 50)) == Directions.RIGHT.value