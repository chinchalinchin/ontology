"""
@domain.test
@test.unit
@app.module
@modality.action
@modality.intention
@workflow.combat

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


def test_animation_map_navigation_and_interact_intentions(mock_state, mock_equipment):
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    for intention in (
        Intentions.INTERACT.value,
        Intentions.WANDER.value,
        Intentions.FIND.value,
        Intentions.FOLLOW.value,
        Intentions.HUNT.value,
        Intentions.ESCAPE.value,
        Intentions.RETURN.value,
        Intentions.USE.value,
    ):
        state.intention = intention
        assert AnimationMap.action(state, mock_equipment) == Actions.WALK.value


@pytest.mark.workflow_combat
@pytest.mark.workflow_projectiles
def test_animation_map_attack_weapons(mock_state, mock_equipment):
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    state.intention = Intentions.ATTACK.value

    state.slots.equipment.weapon = None
    assert AnimationMap.action(state, mock_equipment) is None

    state.slots.equipment.weapon = "non-existent-weapon"
    assert AnimationMap.action(state, mock_equipment) is None

    state.slots.equipment.weapon = "sword"
    assert AnimationMap.action(state, mock_equipment) == Actions.SLASH.value

    state.slots.equipment.weapon = "spear"
    assert AnimationMap.action(state, mock_equipment) == Actions.THRUST.value

    state.slots.equipment.weapon = "longbow"
    assert AnimationMap.action(state, mock_equipment) == Actions.SHOOT.value

    state.slots.equipment.weapon = "crossbow"
    assert AnimationMap.action(state, mock_equipment) == Actions.THRUST.value


def test_animation_map_mine_and_build(mock_state, mock_equipment):
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )

    state.intention = Intentions.MINE.value
    state.slots.equipment.tool = None
    assert AnimationMap.action(state, mock_equipment) is None

    state.slots.equipment.tool = "non-existent-tool"
    assert AnimationMap.action(state, mock_equipment) is None

    state.slots.equipment.tool = "axe"
    assert AnimationMap.action(state, mock_equipment) == Actions.SLASH.value

    state.slots.equipment.tool = "pickaxe"
    assert AnimationMap.action(state, mock_equipment) == Actions.THRUST.value

    state.intention = Intentions.BUILD.value
    state.slots.equipment.utility = None
    assert AnimationMap.action(state, mock_equipment) is None

    state.slots.equipment.utility = "non-existent-utility"
    assert AnimationMap.action(state, mock_equipment) is None

    state.slots.equipment.utility = "lantern"
    assert AnimationMap.action(state, mock_equipment) == Actions.CAST.value


@pytest.mark.workflow_combat
def test_animation_map_candidate_intention_override(mock_state, mock_equipment):
    """Verifies candidate intention gating without mutating state.intention."""
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    state.intention = Intentions.IDLE.value
    state.slots.equipment.weapon = None

    assert (
        AnimationMap.action(state, mock_equipment, intention=Intentions.ATTACK.value)
        is None
    )
    assert state.intention == Intentions.IDLE.value

    state.slots.equipment.weapon = "longbow"
    assert (
        AnimationMap.action(state, mock_equipment, intention=Intentions.ATTACK.value)
        == Actions.SHOOT.value
    )
    assert state.intention == Intentions.IDLE.value

    state.intention = Intentions.ATTACK.value
    state.slots.equipment.weapon = None
    assert (
        AnimationMap.action(state, mock_equipment, intention=Intentions.WANDER.value)
        == Actions.WALK.value
    )


@pytest.mark.workflow_combat
def test_animation_map_missing_slots_or_empty_actions_returns_none(
    mock_state,
    mock_equipment,
):
    state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    state.intention = Intentions.ATTACK.value
    state.slots = None
    assert AnimationMap.action(state, mock_equipment) is None

    state_with_slots = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    state_with_slots.intention = Intentions.ATTACK.value
    state_with_slots.slots.equipment.weapon = "sword"
    mock_equipment.weapons["sword"].properties.actions = {}
    assert AnimationMap.action(state_with_slots, mock_equipment) is None


def test_animation_map_directions():
    origin = Position(50, 50)
    assert AnimationMap.direction(origin, Position(50, 80)) == Directions.DOWN.value
    assert AnimationMap.direction(origin, Position(50, 20)) == Directions.UP.value
    assert AnimationMap.direction(origin, Position(20, 50)) == Directions.LEFT.value
    assert AnimationMap.direction(origin, Position(80, 50)) == Directions.RIGHT.value