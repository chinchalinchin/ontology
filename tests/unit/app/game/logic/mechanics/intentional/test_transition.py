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
from app.models.state import Goal
from app.static.semantics import (
    Actions,
    AssetInstances,
    Directions,
    Goals,
    Intentions,
    Mechanics,
)

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
    sprite.state.slots.equipment.weapon = "sword"
    sprite.state.animation.action = Actions.WALK.value
    sprite.state.animation.frame = 5
    sprite.state.animation.tick = 3
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer="0",
        position=Position(x=20, y=10),
    )

    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert sprite.state.intention == Intentions.ATTACK.value
    assert sprite.state.animation.action == Actions.SLASH.value
    assert sprite.state.animation.frame == 0
    assert sprite.state.animation.tick == 1
    assert sprite.state.animation.direction == Directions.RIGHT.value
    assert sprite.state.mutators.triggers.animated is True


def test_transition_gates_and_reverts_inadmissible_equipment(
    mock_mechanic,
    mock_bus,
    mock_board,
):
    """
    Verifies TransitionMechanics rejects transitions requiring missing Equipment
    and reverts inadmissible active intentions cleanly to IDLE / WALK.
    """
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    # 1. Unarmed HUNT near target rejects HUNT -> ATTACK
    sprite.state.intention = Intentions.HUNT.value
    sprite.state.layer = "0"
    sprite.state.position = Position(x=10, y=10)
    sprite.state.mutators.parameters.action.radius = 25
    sprite.state.slots.equipment.weapon = None
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer="0",
        position=Position(x=20, y=10),
    )

    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.HUNT.value
    assert sprite.state.animation.action == Actions.WALK.value

    # 2. Unarmed sprite already in ATTACK reverts to IDLE / WALK
    sprite.state.intention = Intentions.ATTACK.value
    sprite.state.animation.action = Actions.SLASH.value
    sprite.state.animation.frame = 3

    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.IDLE.value
    assert sprite.state.animation.action == Actions.WALK.value
    assert sprite.state.animation.frame == 0
    assert sprite.state.animation.tick == 1


def test_transition_update_idle_to_hunt_wander_and_escape(
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

    # 2. IDLE with no goal stays in IDLE (CognitionMechanics owns Goal acquisition)
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.goal = None
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.IDLE.value
    assert sprite.state.animation.action == Actions.WALK.value

    # 3. IDLE with POSITION goal transitions to WANDER when not frightened
    sprite.state.mutators.triggers.frightened = False
    sprite.state.goal = Goal(
        name=Intentions.WANDER.value,
        category=Goals.POSITION.value,
        layer="0",
        position=Position(x=200, y=200),
    )
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.WANDER.value

    # 4. IDLE with POSITION goal transitions to ESCAPE when frightened
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.mutators.triggers.frightened = True
    sprite.state.goal = Goal(
        name=Intentions.ESCAPE.value,
        category=Goals.POSITION.value,
        layer="0",
        position=Position(x=200, y=200),
    )
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.ESCAPE.value


def test_transition_dead_sprite_locks_die_animation(
    mock_mechanic,
    mock_bus,
    mock_board,
):
    """Verifies B085: dead sprites lock into IDLE / DIE / UP and bypass ISL transitions."""
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.intention = Intentions.HUNT.value
    sprite.state.animation.action = Actions.WALK.value
    sprite.state.animation.direction = Directions.RIGHT.value
    sprite.state.animation.frame = 4
    sprite.state.mutators.triggers.dead = True

    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert sprite.state.intention == Intentions.IDLE.value
    assert sprite.state.animation.action == Actions.DIE.value
    assert sprite.state.animation.direction == Directions.UP.value
    assert sprite.state.animation.frame == 0
    assert sprite.state.animation.tick == 1
    assert sprite.state.mutators.triggers.animated is True


def test_transition_door_subsumption_exits_hunt_to_idle(
    mock_mechanic,
    mock_bus,
    mock_board,
):
    """Verifies B064: substituting a Goals.DOOR while in HUNT exits cleanly to IDLE."""
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.intention = Intentions.HUNT.value
    sprite.state.layer = "0"
    sprite.state.goal = Goal(
        name="door-1",
        category=Goals.DOOR.value,
        layer="0",
        position=Position(x=100, y=100),
    )

    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert sprite.state.intention == Intentions.IDLE.value


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
