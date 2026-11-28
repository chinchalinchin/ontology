"""
@domain.test
@test.unit
@app.mechanic
@modality.intention
@workflow.cognition

# Ontology: Tests - tests.unit.app.game.logic.mechanics.intentional.test_cognition

Unit tests for the four-stage CognitionMechanics pipeline:
Sense -> Resolve -> Acquire (IDLE-only) -> Sync.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.mechanics import CognitionMechanics
from app.models.state import Goal
from app.static.semantics import (
    AssetInstances,
    Executors,
    Expressions,
    Goals,
    Intentions,
    Mechanics,
    Relationships,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.modality_intention,
    pytest.mark.workflow_cognition,
]

# -----------------------------------------------------


def test_cognition_set_executor_binds_and_clears_resolver(
    mock_executors,
):
    mechanic = CognitionMechanics()
    assert mechanic.executor is None
    assert mechanic.resolver is None

    evaluator = mock_executors()[Executors.GOAL.value]
    mechanic.set_executor(Executors.GOAL, evaluator)

    assert mechanic.executor is evaluator
    assert mechanic.resolver is not None
    assert mechanic.resolver.evaluator is evaluator

    mechanic.executor = None
    assert mechanic.executor is None
    assert mechanic.resolver is None


def test_cognition_update_safe_when_board_has_no_player(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """Verifies B074: update handles boards with no deployed Player safely."""
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    player = mock_board.player()
    mock_board.remove([player])
    assert mock_board.player() is None

    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite.state.position = Position(1800, 1800)
    sprite.state.intention = Intentions.IDLE
    sprite.state.goal = None
    sprite.state.memory.goals.clear()
    sprite.state.memory.stack.clear()
    sprite.state.meters.health.current = sprite.state.meters.health.maximum

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.goal is not None
    assert sprite.state.goal.category == Goals.POSITION
    assert sprite.state.goal.name == Intentions.WANDER.value


def test_cognition_update_skips_dead_sprites(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.mutators.triggers.dead = True
    sprite.state.intention = Intentions.IDLE
    sprite.state.goal = None
    sprite.state.memory.goals.clear()

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.goal is None


def test_cognition_wander_never_reacquires_outside_idle(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """Verifies B075: Acquisition runs strictly in IDLE so wander -> idle is reachable."""
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(1800, 1800)
    sprite.state.intention = Intentions.WANDER
    sprite.state.meters.health.current = sprite.state.meters.health.maximum
    sprite.state.memory.goals.clear()
    sprite.state.memory.stack.clear()
    # Goal already within action.radius completes during Stage 2
    sprite.state.goal = Goal(
        name=Intentions.WANDER.value,
        category=Goals.POSITION,
        layer=sprite.state.layer,
        position=Position(1800, 1800),
    )

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())
    assert sprite.state.goal is None

    # After TransitionMechanics routes wander -> idle, IDLE acquires a fresh wander Goal
    sprite.state.intention = Intentions.IDLE
    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.goal is not None
    assert sprite.state.goal.category == Goals.POSITION
    assert sprite.state.goal.name == Intentions.WANDER.value
    assert sprite.state.mutators.triggers.vision is True


def test_cognition_survival_preemption_shelves_goal_without_confusion(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Stage 2 Survival preemption shelves active Character Goals non-dormant
    without emitting confusion, and Tier 1 SurvivalInstinct acquires escape once in IDLE.
    """
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    sprite.state.layer = "0"
    player.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    player.state.position = Position(1860, 1800)

    active_goal = Goal(
        name=player.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(1860, 1800),
    )
    sprite.state.intention = Intentions.HUNT
    sprite.state.goal = active_goal
    sprite.state.memory.goals.clear()
    sprite.state.memory.stack.clear()
    sprite.state.memory.relationships[player.name] = Relationships.FOE
    sprite.state.psyche.expression = None
    # Drop health below fear.limit to trigger frightened
    sprite.state.meters.health.current = 1

    # Tick 1 (HUNT): Stage 2 preempts active_goal without confusion; Stage 3 skipped
    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.mutators.triggers.frightened is True
    assert sprite.state.goal is None
    assert sprite.state.psyche.expression is None
    assert sprite.state.memory.goals[player.name] is active_goal
    assert active_goal.dormant is False

    # Tick 2 (IDLE): Tier 1 SurvivalInstinct beats episodic memory and flees away from threat
    sprite.state.intention = Intentions.IDLE
    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.goal is not None
    assert sprite.state.goal.category == Goals.POSITION
    assert sprite.state.goal.name == Intentions.ESCAPE.value
    assert sprite.state.goal.position.x < sprite.state.position.x


def test_cognition_acquire_priority_order_stack_before_episodic_before_drives(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """Verifies monotonic IDLE Acquisition priority: Stack > Episodic > Drives > Explore."""
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    sprite.state.layer = "0"
    player.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    player.state.position = Position(1850, 1800)
    sprite.state.meters.health.current = sprite.state.meters.health.maximum
    sprite.state.intention = Intentions.IDLE
    sprite.state.goal = None
    sprite.state.slots.equipment.weapon = "sword"
    sprite.state.memory.relationships[player.name] = Relationships.FOE

    stacked = Goal(
        name="stacked-spot",
        category=Goals.POSITION,
        layer="0",
        position=Position(2000, 1800),
    )
    episodic = Goal(
        name="episodic-spot",
        category=Goals.POSITION,
        layer="0",
        position=Position(2100, 1800),
        dormant=False,
    )
    sprite.state.memory.stack = [stacked]
    sprite.state.memory.goals = {episodic.name: episodic}

    # Pass 1: pops Commitment Stack first
    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())
    assert sprite.state.goal is stacked
    assert sprite.state.memory.stack == []

    # Pass 2: stack empty -> pops non-dormant Episodic Memory before CombatInstinct
    sprite.state.goal = None
    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())
    assert sprite.state.goal is episodic
    assert episodic.name not in sprite.state.memory.goals

    # Pass 3: memories empty -> Drive Instinct (CombatInstinct targets visible FOE)
    sprite.state.goal = None
    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())
    assert sprite.state.goal is not None
    assert sprite.state.goal.category == Goals.TARGET
    assert sprite.state.goal.name == player.name


def test_cognition_resolve_target_complete_and_lost_confusion(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    sprite.state.layer = "0"
    player.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    sprite.state.meters.health.current = sprite.state.meters.health.maximum
    sprite.state.intention = Intentions.HUNT
    sprite.state.memory.goals.clear()

    # 1. Unseen target at last-known coordinate within action.radius -> LOST + store dormant + confusion
    player.state.position = Position(100, 100)
    player.state.mutators.triggers.dead = False
    lost_goal = Goal(
        name=player.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(1805, 1805),
    )
    sprite.state.goal = lost_goal
    sprite.state.psyche.expression = None

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.goal is None
    assert sprite.state.memory.goals[player.name] is lost_goal
    assert lost_goal.dormant is True
    assert sprite.state.psyche.expression is not None
    assert sprite.state.psyche.expression.icon == Expressions.CONFUSION.value

    # 2. Dead target -> COMPLETE + forget
    player.state.mutators.triggers.dead = True
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(100, 100),
    )
    sprite.state.memory.goals[player.name] = sprite.state.goal

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.goal is None
    assert player.name not in sprite.state.memory.goals


def test_cognition_sync_subsumes_acquired_cross_layer_goal_same_tick(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Stage 4 (Sync) immediately subsumes a newly acquired cross-layer Goal
    with a same-layer Goals.DOOR and refreshes triggers.vision on the same tick.
    """
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]

    sprite.state.layer = door.state.layer
    sprite.state.position = Position(
        door.state.position.x + 10,
        door.state.position.y + 10,
    )
    sprite.state.meters.health.current = sprite.state.meters.health.maximum
    sprite.state.intention = Intentions.IDLE
    sprite.state.goal = None
    sprite.state.memory.doors.clear()
    sprite.state.memory.stack.clear()

    remote_goal = Goal(
        name="remote-chest",
        category=Goals.OBJECT,
        layer=door.state.outlayer,
        position=Position(200, 200),
        dormant=False,
    )
    sprite.state.memory.goals = {remote_goal.name: remote_goal}

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.memory.stack == [remote_goal]
    assert sprite.state.goal is not None
    assert sprite.state.goal.category == Goals.DOOR
    assert sprite.state.goal.name == door.name
    assert sprite.state.goal.layer == door.state.layer
    assert sprite.state.mutators.triggers.vision is True


def test_cognition_stalled_door_unwinds_and_does_not_oscillate(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies B081: stalling on an unmapped Door unwinds the parent Goal into dormant
    memory and marks the Door stalled so subsequent ticks do not infinitely re-wake it.
    """
    mechanic = mock_mechanic(Mechanics.COGNITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]

    sprite.state.layer = door.state.layer
    sprite.state.position = Position(
        door.state.position.x + 10,
        door.state.position.y + 10,
    )
    sprite.state.meters.health.current = sprite.state.meters.health.maximum
    sprite.state.memory.doors.clear()
    sprite.state.memory.goals.clear()

    parent_goal = Goal(
        name="remote-chest",
        category=Goals.OBJECT,
        layer=door.state.outlayer,
        position=Position(200, 200),
    )
    sprite.state.memory.stack = [parent_goal]
    sprite.state.intention = Intentions.FIND
    sprite.state.goal = Goal(
        name=door.name,
        category=Goals.DOOR,
        layer=door.state.layer,
        position=Position(door.state.position.x, door.state.position.y),
    )
    sprite.state.trajectory.stalled = True

    # Tick 1: door.lost unwinds parent_goal (dormant=True) and records door as stalled
    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.goal is None
    assert sprite.state.memory.stack == []
    assert sprite.state.memory.goals[parent_goal.name] is parent_goal
    assert parent_goal.dormant is True

    # Tick 2 in IDLE next to the same blocked Door: parent_goal stays dormant (no B081 loop)
    sprite.state.intention = Intentions.IDLE
    sprite.state.trajectory.stalled = False
    sprite.state.psyche.dialogue = None
    sprite.state.memory.relationships.clear()

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.memory.goals[parent_goal.name].dormant is True
    assert sprite.state.goal is not None
    assert sprite.state.goal.category == Goals.POSITION
    assert sprite.state.goal.name == Intentions.WANDER.value
