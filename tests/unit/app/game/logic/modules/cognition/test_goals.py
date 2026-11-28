"""
@domain.test
@test.unit
@app.module
@modality.intention
@workflow.cognition

# Ontology: Tests - tests.unit.app.game.logic.modules.cognition.test_goals

Unit tests for Goal Resolution operators: ResponseOperator, ReflexOperator,
LocatorOperator (DoorLocator), OutcomeOperator, and GoalResolver.
"""
# Standard Libraries
from dataclasses import replace

# External Libraries
import pytest

# Application Libraries
from app.assets.base import Asset, Taxonomy
from app.models.state.assets.sheets import Goal, Memory, Psyche
from app.static.semantics import (
    AssetInstances,
    Expressions,
    ExpressionsPalette,
    Goals,
    LayerProjections,
    Locators,
    Outcomes,
    Reflexes,
    Responses,
    Translators,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_module,
    pytest.mark.modality_intention,
    pytest.mark.workflow_cognition,
]

# ---------------------------------------------------------------------------
# RESPONSE OPERATOR (MEMORY)
# ---------------------------------------------------------------------------


def test_response_operator_forget_store_push_unwind(mock_response_operator):
    memory = Memory()
    parent = Goal(name="boss", category=Goals.TARGET, layer="1")
    door_goal = Goal(name="door-1", category=Goals.DOOR, layer="0")

    # store marks dormant=True and saves into memory.goals
    mock_response_operator.resolve([Responses.STORE], parent, memory)
    assert parent.dormant is True
    assert memory.goals["boss"] is parent

    # forget evicts by goal.name
    mock_response_operator.resolve([Responses.FORGET], parent, memory)
    assert "boss" not in memory.goals

    # push appends to stack and deduplicates consecutive identical top entries
    mock_response_operator.resolve([Responses.PUSH], parent, memory)
    duplicate = Goal(name="boss", category=Goals.TARGET, layer="1")
    mock_response_operator.resolve([Responses.PUSH], duplicate, memory)
    assert len(memory.stack) == 1
    assert memory.stack[-1] is duplicate

    # unwind pops top parent from stack, sets dormant=True, stores in memory.goals
    duplicate.dormant = False
    mock_response_operator.resolve([Responses.FORGET, Responses.UNWIND], door_goal, memory)
    assert memory.stack == []
    assert memory.goals["boss"] is duplicate
    assert duplicate.dormant is True

    # unwind on empty stack is a safe no-op
    mock_response_operator.resolve([Responses.UNWIND], door_goal, memory)
    assert memory.stack == []


def test_response_operator_unregistered_key_raises(mock_response_operator):
    with pytest.raises(KeyError):
        mock_response_operator.get("unknown-response")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# REFLEX OPERATOR (PSYCHE)
# ---------------------------------------------------------------------------


def test_reflex_operator_confusion_spawns_and_attaches_expression(
    mock_reflex_operator,
    mock_board,
):
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    psyche = Psyche()
    goal = Goal(name="lost-target", category=Goals.TARGET, layer="0")

    def _spawn(palette: ExpressionsPalette, expression: Expressions):
        return mock_board.cradle.spawn_expression(palette, expression, sprite)

    mock_reflex_operator.resolve([Reflexes.CONFUSION], goal, psyche, _spawn)
    assert psyche.expression is not None
    assert psyche.expression.icon == Expressions.CONFUSION.value

    # Spawner returning None leaves psyche.expression unchanged
    existing = psyche.expression
    mock_reflex_operator.resolve(
        [Reflexes.CONFUSION], goal, psyche, lambda p, e: None
    )
    assert psyche.expression is existing


def test_reflex_operator_unregistered_key_raises(mock_reflex_operator):
    with pytest.raises(KeyError):
        mock_reflex_operator.get("unknown-reflex")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# LOCATOR OPERATOR & DOOR LOCATOR (B080, B087)
# ---------------------------------------------------------------------------


def test_door_locator_bidirectional_in_and_out_doors_and_memory_map(
    mock_locator_operator,
    mock_board,
):
    """
    Verifies DoorLocator resolves both LayerProjections.IN and LayerProjections.OUT
    Doors and reads bidirectional memory.doors[from_layer][door_name] = to_layer (B080).
    """
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    in_door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]
    interior_layer = in_door.state.outlayer
    out_doors = mock_board.instances(AssetInstances.DOORS.value, interior_layer)
    assert len(out_doors) >= 1
    out_door = out_doors[0]
    assert out_door.state.projection == LayerProjections.OUT

    # 1. Mapped IN Door found even outside vision.radius
    sprite.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    sprite.state.mutators.parameters.vision.radius = 10
    sprite.state.memory.doors = {
        "0": {in_door.name: interior_layer},
        interior_layer: {out_door.name: "0"},
    }
    sprite.state.goal = Goal(
        name="target", category=Goals.TARGET, layer=interior_layer
    )
    located_in = mock_locator_operator.resolve(Locators.DOOR, sprite, mock_board)
    assert located_in is in_door

    # 2. Reciprocal OUT Door found from interior_layer back to "0" without overwriting IN edge
    sprite.state.layer = interior_layer
    sprite.state.goal = Goal(name="target", category=Goals.TARGET, layer="0")
    located_out = mock_locator_operator.resolve(Locators.DOOR, sprite, mock_board)
    assert located_out is out_door


def test_door_locator_multihop_bfs_cycle_safety_and_exclusions(
    mock_locator_operator,
    mock_board,
):
    """
    Verifies multi-hop BFS over memory.doors, cycle termination, unmapped visible
    fallback, and stalled Door exclusion (B087).
    """
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    door1 = mock_board.instances(AssetInstances.DOORS.value, "0")[0]

    # Add a second distinct Door on layer "0" nearby door1
    alt_state = replace(
        door1.state,
        name="alt-door",
        position=Position(door1.state.position.x + 20, door1.state.position.y),
        outlayer="alt-layer",
    )
    door2 = Asset(
        taxonomy=Taxonomy(
            id=door1.id,
            name="alt-door",
            category=door1.category,
            instance=door1.instance,
        ),
        properties=door1.properties,
        state=alt_state,
        frame=door1.frame,
        animation=door1.animation,
        hitbox=door1.hitbox,
        substrate=door1.substrate,
    )
    mock_board.add([door2])

    sprite.state.layer = "0"
    sprite.state.position = Position(door1.state.position.x, door1.state.position.y)
    sprite.state.mutators.parameters.vision.radius = 50
    sprite.state.goal = Goal(name="target", category=Goals.TARGET, layer="deep-layer")

    # Multi-hop BFS: door2 (1 hop) beats closer door1 (2 hops)
    sprite.state.memory.doors = {
        "0": {door1.name: "mid-layer", door2.name: "deep-layer"},
        "mid-layer": {"d-mid": "deep-layer"},
    }
    assert mock_locator_operator.resolve(Locators.DOOR, sprite, mock_board) is door2

    # Excluding stalled door2 falls back to multi-hop door1 (B087)
    assert (
        mock_locator_operator.resolve(
            Locators.DOOR, sprite, mock_board, excluded=frozenset({door2.name})
        )
        is door1
    )

    # Cycle safety with unreachable target and no unmapped doors returns None
    sprite.state.memory.doors = {
        "0": {door1.name: "mid-layer", door2.name: "mid-layer"},
        "mid-layer": {"d-back": "0"},
    }
    sprite.state.goal = Goal(name="target", category=Goals.TARGET, layer="unreachable")
    assert mock_locator_operator.resolve(Locators.DOOR, sprite, mock_board) is None

    # Unmapped door within vision.radius acts as exploratory fallback
    sprite.state.memory.doors = {"0": {door1.name: "mid-layer"}}
    assert mock_locator_operator.resolve(Locators.DOOR, sprite, mock_board) is door2


# ---------------------------------------------------------------------------
# GOAL RESOLVER & OUTCOME OPERATOR (B079)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "implementation",
    [Translators.COMPILER.value, Translators.LAMBDA.value],
)
def test_goal_resolver_evaluate_is_pure_and_resolve_handles_layered_and_unreachable(
    implementation,
    mock_goal_resolver,
    mock_board,
):
    resolver = mock_goal_resolver(implementation)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]

    # 1. evaluate() is pure: classifies LAYERED without mutating stack or goal
    sprite.state.layer = "0"
    sprite.state.position = Position(
        door.state.position.x + 10, door.state.position.y + 10
    )
    sprite.state.memory.doors.clear()
    sprite.state.memory.stack.clear()
    sprite.state.memory.goals.clear()

    remote_goal = Goal(
        name="remote-chest",
        category=Goals.OBJECT,
        layer=door.state.outlayer,
        position=Position(100, 100),
    )
    sprite.state.goal = remote_goal

    rule = resolver.evaluate(sprite.state, mock_board.characters(), mock_board.states("0"))
    assert rule is not None
    assert rule.outcome == Outcomes.LAYERED
    assert sprite.state.goal is remote_goal
    assert sprite.state.memory.stack == []

    # 2. resolve() with reachable Door pushes parent onto stack and assigns Goals.DOOR
    outcome = resolver.resolve(sprite, mock_board)
    assert outcome == Outcomes.LAYERED
    assert sprite.state.memory.stack == [remote_goal]
    assert sprite.state.goal.category == Goals.DOOR
    assert sprite.state.goal.name == door.name

    # 3. resolve() when all Doors are unreachable/excluded demotes to dormant memory.goals (no stack push)
    sprite.state.memory.stack.clear()
    sprite.state.memory.goals.clear()
    sprite.state.position = Position(1800, 1800)
    sprite.state.mutators.parameters.vision.radius = 20
    sprite.state.goal = remote_goal

    outcome = resolver.resolve(sprite, mock_board)
    assert outcome == Outcomes.LAYERED
    assert sprite.state.goal is None
    assert sprite.state.memory.stack == []
    assert sprite.state.memory.goals[remote_goal.name] is remote_goal
    assert remote_goal.dormant is True
