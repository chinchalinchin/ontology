"""
@domain.test
@test.unit
@app.mechanic
@modality.intention
@workflow.transitions

# Ontology: Tests - tests.unit.app.game.logic.mechanics.intentional.test_transition

Unit tests for TransitionMechanics.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Actions,
    AssetInstances,
    Directions,
    Goals,
    Intentions,
    Mechanics,
)
from app.models.state import Goal

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.modality_intention,
    pytest.mark.workflow_transitions,
]

# -----------------------------------------------------


def test_transition_update_evaluates_executor(
    mock_mechanic,
    mock_bus,
    mock_board,
):
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    sprite.state.intention = Intentions.HUNT.value
    sprite.state.layer = "0"
    sprite.state.position = Position(x=10, y=10)
    sprite.state.mutators.parameters.action.radius = 25
    sprite.state.inventory.equipment.weapon = None
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer="0",
        position=Position(x=20, y=10),
    )

    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert sprite.state.intention == Intentions.ATTACK.value
    assert sprite.state.animation.action == Actions.CAST.value
    assert sprite.state.animation.direction == Directions.RIGHT.value
    assert sprite.state.mutators.triggers.animated is True


def test_transition_update_idle_to_hunt_and_wander(
    mock_mechanic,
    mock_bus,
    mock_board,
):
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    # 1. IDLE with TARGET goal on same layer transitions to HUNT
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.layer = "0"
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer="0",
        position=Position(x=100, y=100),
    )
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.HUNT.value
    assert sprite.state.animation.action == Actions.WALK.value

    # 2. IDLE with no goal transitions to WANDER
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.goal = None
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.WANDER.value
    assert sprite.state.animation.action == Actions.WALK.value


def test_transition_update_skips_without_executor(
    mock_mechanic,
    mock_bus,
    mock_board,
):
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    mechanic.executor = None

    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.goal = None
    sprite.state.velocity.vx = 0
    sprite.state.velocity.vy = 0

    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert mechanic.executor is None
    assert sprite.state.intention == Intentions.IDLE.value
    assert sprite.state.animation.action == Actions.WALK.value
    assert sprite.state.mutators.triggers.animated is False