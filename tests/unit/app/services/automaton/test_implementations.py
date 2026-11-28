"""
@domain.test
@test.unit
@app.service
@modality.intention
@workflow.cognition
@workflow.plot
@workflow.seasons
@workflow.transitions

# Ontology: Tests - tests.unit.app.services.automaton.test_implementations

Unit tests for ISL Backends, TransitionExecutor, GoalEvaluator, Environ helpers,
and static/runtime Intention Transition Matrix invariants.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.configurations.automata.goals import GoalConfiguration
from app.models.state.assets.sheets import Goal
from app.services.automaton import (
    Compiler,
    GoalEvaluator,
    GoalRule,
    Lambda,
    Transition,
    TransitionExecutor,
)
from app.services.automaton.environ import (
    any_goals,
    any_memories_visible,
    is_near,
)
from app.services.automaton.executors.resolutions import OUTCOME_PRECEDENCE
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Expressions,
    ExpressionsPalette,
    Goals,
    Intentions,
    Motivations,
    Outcomes,
    Reflexes,
    Relationships,
    RequiredAssets,
    Responses,
    Translators,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_service,
    pytest.mark.workflow_transitions,
]

BACKENDS = [
    Translators.COMPILER.value,
    Translators.LAMBDA.value,
]

# ---------------------------------------------------------------------------
# BACKEND COMPILATION & FAIL-FAST VALIDATION (B069)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "implementation,executor_cls,backend_cls",
    [
        (Translators.COMPILER.value, TransitionExecutor, Compiler),
        (Translators.LAMBDA.value, TransitionExecutor, Lambda),
    ],
)
def test_executor_compiles(
    implementation,
    executor_cls,
    backend_cls,
    mock_transitions,
    mock_configurations_schema,
):
    translator = mock_transitions(implementation)
    executor = translator.compile(mock_configurations_schema.intentions)

    assert isinstance(executor, executor_cls)
    assert isinstance(executor.backend, backend_cls)


@pytest.mark.parametrize("implementation", BACKENDS)
def test_backend_empty_conditions_returns_false(implementation, mock_backend):
    backend = mock_backend(implementation)
    assert backend.evaluate((), {}) is False


@pytest.mark.parametrize("implementation", BACKENDS)
def test_backend_fail_fast_on_syntax_error(
    implementation,
    mock_transitions,
    mock_goals,
):
    """Verifies B069: both backends raise SyntaxError instead of silently dropping conjuncts."""
    bad_transitions = {
        "bad_syntax": [
            Transition(
                next="more-bad-syntax",
                conditions=["not thing nor any(this for this in thing)"],
            )
        ]
    }
    with pytest.raises(SyntaxError):
        mock_transitions(implementation).compile(bad_transitions)

    bad_goals = {
        Goals.TARGET: {
            Outcomes.COMPLETE: GoalConfiguration(
                reflexes=[],
                responses=[],
                conditions=["sprite.goal == == None"],
            )
        }
    }
    with pytest.raises(SyntaxError):
        mock_goals(implementation).compile(bad_goals)


@pytest.mark.parametrize("implementation", BACKENDS)
def test_backend_fail_fast_on_non_string_condition(implementation, mock_backend):
    backend = mock_backend(implementation)
    with pytest.raises(TypeError):
        backend.conditionalize(123)  # type: ignore[arg-type]


@pytest.mark.parametrize("implementation", BACKENDS)
def test_goal_translator_rejects_unknown_outcome(implementation, mock_goals):
    invalid_goals = {
        Goals.TARGET: {
            "invalid-outcome": GoalConfiguration(
                reflexes=[],
                responses=[],
                conditions=["True"],
            )
        }
    }
    with pytest.raises(ValueError):
        mock_goals(implementation).compile(invalid_goals)


# ---------------------------------------------------------------------------
# ENVIRON HELPER FUNCTIONS (B070)
# ---------------------------------------------------------------------------


@pytest.mark.workflow_cognition
def test_environ_is_near_closed_ball_semantics():
    p1 = Position(0, 0)
    assert is_near(p1, Position(3, 4), 5) is True
    assert is_near(p1, Position(3, 4), 4) is False
    assert is_near(p1, Position(0, 0), 0) is True
    assert is_near(p1, Position(0, 0), -1) is False
    assert is_near(None, p1, 10) is False
    assert is_near(p1, None, 10) is False


@pytest.mark.workflow_cognition
def test_environ_any_goals():
    assert any_goals({}) is False
    goals = {
        "foe": Goal(name="foe", category=Goals.TARGET),
    }
    assert any_goals(goals) is True
    assert any_goals(goals, Goals.TARGET) is True
    assert any_goals(goals, Goals.SUBJECT) is False


@pytest.mark.workflow_cognition
def test_environ_any_memories_visible_filters_dead_and_cross_layer(mock_state):
    """Verifies B070: dead, cross-layer, out-of-range, and wrong-category targets are excluded."""
    sprite = mock_state(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite.layer = "0"
    sprite.position = Position(100, 100)
    vision = sprite.mutators.parameters.vision.radius

    other = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
        name="remembered-foe",
    )
    other.layer = "0"
    other.position = Position(100 + vision, 100)
    other.mutators.triggers.dead = False

    sprite.memory.goals = {
        other.name: Goal(name=other.name, category=Goals.TARGET, layer="0"),
    }
    sprites = {other.name: other}

    # Exact closed-ball boundary matches
    assert any_memories_visible(sprite, sprites, [Goals.TARGET]) is True
    # Wrong category excluded
    assert any_memories_visible(sprite, sprites, [Goals.SUBJECT]) is False

    # Dead target excluded (B070)
    other.mutators.triggers.dead = True
    assert any_memories_visible(sprite, sprites, [Goals.TARGET]) is False

    # Cross-layer living target excluded
    other.mutators.triggers.dead = False
    other.layer = "1"
    assert any_memories_visible(sprite, sprites, [Goals.TARGET]) is False

    # Same-layer out-of-vision target excluded
    other.layer = "0"
    other.position = Position(100 + vision + 1, 100)
    assert any_memories_visible(sprite, sprites, [Goals.TARGET]) is False


# ---------------------------------------------------------------------------
# GOAL EVALUATOR PARITY & OUTCOME PRECEDENCE (COMPILER VS LAMBDA)
# ---------------------------------------------------------------------------


@pytest.mark.workflow_cognition
@pytest.mark.parametrize("implementation", BACKENDS)
def test_goal_evaluator_compiles_canonical_precedence(
    implementation,
    mock_goals,
    mock_configurations_schema,
):
    evaluator = mock_goals(implementation).compile(mock_configurations_schema.goals)
    assert isinstance(evaluator, GoalEvaluator)

    for category, rules in evaluator.rules.items():
        outcomes = [r.outcome for r in rules]
        expected_order = [o for o in OUTCOME_PRECEDENCE if o in outcomes]
        assert outcomes == expected_order


@pytest.mark.workflow_cognition
@pytest.mark.parametrize("implementation", BACKENDS)
def test_goal_evaluator_precedence_complete_beats_layered_beats_lost(
    implementation,
    mock_goals,
    mock_configurations_schema,
    mock_state,
):
    evaluator = mock_goals(implementation).compile(mock_configurations_schema.goals)
    sprite = mock_state(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    enemy = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
        name="enemy",
    )

    # COMPLETE > LAYERED: dead cross-layer TARGET resolves COMPLETE
    sprite.layer = "0"
    sprite.position = Position(100, 100)
    sprite.mutators.triggers.vision = False
    sprite.trajectory.stalled = True
    sprite.goal = Goal(
        name=enemy.name,
        category=Goals.TARGET,
        layer="1",
        position=Position(100, 100),
    )
    enemy.layer = "1"
    enemy.mutators.triggers.dead = True

    rule = evaluator.evaluate(
        Goals.TARGET,
        {"sprite": sprite, "sprites": {enemy.name: enemy}, "assets": {}},
    )
    assert isinstance(rule, GoalRule)
    assert rule.outcome == Outcomes.COMPLETE
    assert rule.responses == (Responses.FORGET,)
    assert rule.reflexes == ()

    # LAYERED > LOST: living cross-layer stalled TARGET resolves LAYERED
    enemy.mutators.triggers.dead = False
    rule = evaluator.evaluate(
        Goals.TARGET,
        {"sprite": sprite, "sprites": {enemy.name: enemy}, "assets": {}},
    )
    assert rule.outcome == Outcomes.LAYERED
    assert rule.responses == (Responses.PUSH,)

    # Same-layer stalled unseen TARGET resolves LOST with confusion + store
    sprite.goal.layer = "0"
    rule = evaluator.evaluate(
        Goals.TARGET,
        {"sprite": sprite, "sprites": {enemy.name: enemy}, "assets": {}},
    )
    assert rule.outcome == Outcomes.LOST
    assert rule.responses == (Responses.STORE,)
    assert rule.reflexes == (Reflexes.CONFUSION,)


@pytest.mark.workflow_cognition
@pytest.mark.parametrize("implementation", BACKENDS)
def test_goal_evaluator_all_seven_categories_with_assets_local(
    implementation,
    mock_goals,
    mock_configurations_schema,
    mock_board,
):
    evaluator = mock_goals(implementation).compile(mock_configurations_schema.goals)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0].state
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]
    chest = mock_board.instances(AssetInstances.CHESTS.value, "0")[0]
    crop = mock_board.instances(AssetInstances.CROPS.value, "0")[0]

    sprite.layer = "0"
    sprite.position = Position(1800, 1800)
    sprite.trajectory.stalled = False
    sprite.mutators.triggers.interacted = False
    sprite.mutators.triggers.frightened = False
    sprites = mock_board.characters()
    assets = mock_board.states("0")

    # 1. DOOR: complete on layer mismatch; lost on missing asset or stall
    sprite.goal = Goal(name=door.name, category=Goals.DOOR, layer="other-layer")
    rule = evaluator.evaluate(
        Goals.DOOR, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.COMPLETE
    assert rule.responses == (Responses.FORGET,)

    sprite.goal = Goal(name=door.name, category=Goals.DOOR, layer="0")
    assert (
        evaluator.evaluate(
            Goals.DOOR, {"sprite": sprite, "sprites": sprites, "assets": assets}
        )
        is None
    )
    sprite.trajectory.stalled = True
    rule = evaluator.evaluate(
        Goals.DOOR, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.LOST
    assert rule.responses == (Responses.FORGET, Responses.UNWIND)

    sprite.trajectory.stalled = False
    sprite.goal = Goal(name="missing-door", category=Goals.DOOR, layer="0")
    rule = evaluator.evaluate(
        Goals.DOOR, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.LOST

    # 2. OBJECT: free while present and not interacted; complete on interacted or removed
    sprite.goal = Goal(name=chest.name, category=Goals.OBJECT, layer="0")
    assert (
        evaluator.evaluate(
            Goals.OBJECT, {"sprite": sprite, "sprites": sprites, "assets": assets}
        )
        is None
    )
    sprite.mutators.triggers.interacted = True
    rule = evaluator.evaluate(
        Goals.OBJECT, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.COMPLETE
    sprite.mutators.triggers.interacted = False

    sprite.goal = Goal(name="removed-chest", category=Goals.OBJECT, layer="0")
    rule = evaluator.evaluate(
        Goals.OBJECT, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.COMPLETE

    # 3. RESOURCE: free while present; complete when removed; lost when stalled
    sprite.goal = Goal(name=crop.name, category=Goals.RESOURCE, layer="0")
    assert (
        evaluator.evaluate(
            Goals.RESOURCE, {"sprite": sprite, "sprites": sprites, "assets": assets}
        )
        is None
    )
    sprite.trajectory.stalled = True
    rule = evaluator.evaluate(
        Goals.RESOURCE, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.LOST
    assert rule.responses == (Responses.STORE,)
    sprite.trajectory.stalled = False

    sprite.goal = Goal(name="harvested-crop", category=Goals.RESOURCE, layer="0")
    rule = evaluator.evaluate(
        Goals.RESOURCE, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.COMPLETE

    # 4. PROPERTY: complete when registered in memory.property; lost when stalled
    sprite.goal = Goal(name="my-house", category=Goals.PROPERTY, layer="0")
    sprite.memory.property.clear()
    assert (
        evaluator.evaluate(
            Goals.PROPERTY, {"sprite": sprite, "sprites": sprites, "assets": assets}
        )
        is None
    )
    sprite.memory.property["my-house"] = Position(100, 100)
    rule = evaluator.evaluate(
        Goals.PROPERTY, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.COMPLETE

    # 5. SUBJECT: complete when dialogue cleared or target dead
    sprite.psyche.dialogue = None
    sprite.goal = Goal(name="player", category=Goals.SUBJECT, layer="0")
    rule = evaluator.evaluate(
        Goals.SUBJECT, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.COMPLETE

    # 6. POSITION: escape completes when not frightened; wander lost when frightened
    sprite.intention = Intentions.ESCAPE
    sprite.mutators.triggers.frightened = False
    sprite.goal = Goal(
        name=Intentions.ESCAPE.value,
        category=Goals.POSITION,
        layer="0",
        position=Position(2200, 2200),
    )
    rule = evaluator.evaluate(
        Goals.POSITION, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.COMPLETE

    sprite.intention = Intentions.WANDER
    sprite.mutators.triggers.frightened = True
    sprite.goal = Goal(
        name=Intentions.WANDER.value,
        category=Goals.POSITION,
        layer="0",
        position=Position(2200, 2200),
    )
    rule = evaluator.evaluate(
        Goals.POSITION, {"sprite": sprite, "sprites": sprites, "assets": assets}
    )
    assert rule.outcome == Outcomes.LOST

    # 7. Unknown category returns None
    assert (
        evaluator.evaluate(
            "unknown-category",  # type: ignore[arg-type]
            {"sprite": sprite, "sprites": sprites, "assets": assets},
        )
        is None
    )


# ---------------------------------------------------------------------------
# INTENTION TRANSITION EXECUTOR & STATIC MATRIX VERIFICATION
# ---------------------------------------------------------------------------


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_executor_compiles_intentions(
    implementation,
    mock_transitions,
    mock_configurations_schema,
):
    translator = mock_transitions(implementation)
    executor = translator.compile(mock_configurations_schema.intentions)

    assert Intentions.IDLE.value in executor.transitions
    idle_targets = [t.next for t in executor.transitions[Intentions.IDLE.value]]
    assert idle_targets == [
        Intentions.ESCAPE.value,
        Intentions.WANDER.value,
        Intentions.FIND.value,
        Intentions.HUNT.value,
    ]


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_intention_executor_idle_hub_routing(
    implementation,
    mock_transitions,
    mock_configurations_schema,
    mock_state,
):
    """Verifies IDLE hub routes every Goal category cleanly and stays IDLE with no Goal."""
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    sprite = mock_state(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite.layer = "0"
    sprite.position = Position(100, 100)

    # No goal -> stay IDLE (goal-less idle -> wander removed)
    sprite.goal = None
    assert executor.evaluate(Intentions.IDLE.value, {"sprite": sprite}) is None

    # POSITION + not frightened -> WANDER
    sprite.mutators.triggers.frightened = False
    sprite.goal = Goal(
        name=Intentions.WANDER.value,
        category=Goals.POSITION,
        layer="0",
        position=Position(200, 200),
    )
    assert (
        executor.evaluate(Intentions.IDLE.value, {"sprite": sprite})
        == Intentions.WANDER.value
    )

    # POSITION + frightened -> ESCAPE
    sprite.mutators.triggers.frightened = True
    assert (
        executor.evaluate(Intentions.IDLE.value, {"sprite": sprite})
        == Intentions.ESCAPE.value
    )
    sprite.mutators.triggers.frightened = False

    # SUBJECT, OBJECT, DOOR route unconditionally to FIND even at distance 0 (B073)
    for cat in (Goals.SUBJECT, Goals.OBJECT, Goals.DOOR):
        sprite.goal = Goal(
            name="entity",
            category=cat,
            layer="0",
            position=Position(100, 100),
        )
        assert (
            executor.evaluate(Intentions.IDLE.value, {"sprite": sprite})
            == Intentions.FIND.value
        )

    # TARGET -> HUNT
    sprite.goal = Goal(name="foe", category=Goals.TARGET, layer="0")
    assert (
        executor.evaluate(Intentions.IDLE.value, {"sprite": sprite})
        == Intentions.HUNT.value
    )

    # Cross-layer Goal stays IDLE until CognitionMechanics subsumes a Door
    sprite.goal = Goal(name="foe", category=Goals.TARGET, layer="other-layer")
    assert executor.evaluate(Intentions.IDLE.value, {"sprite": sprite}) is None


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_intention_matrix_strict_idle_hub_and_no_shortcuts(
    implementation,
    mock_transitions,
    mock_configurations_schema,
):
    """Static verification of hub-bypass removal (wander -> hunt/find, escape -> return, attack -> scavenge)."""
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )

    wander_targets = {t.next for t in executor.transitions[Intentions.WANDER.value]}
    assert wander_targets == {Intentions.IDLE.value}

    escape_targets = {t.next for t in executor.transitions[Intentions.ESCAPE.value]}
    assert Intentions.RETURN.value not in escape_targets
    assert Intentions.IDLE.value in escape_targets

    attack_targets = {t.next for t in executor.transitions[Intentions.ATTACK.value]}
    assert Intentions.SCAVENGE.value not in attack_targets
    assert Intentions.IDLE.value in attack_targets


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_intention_matrix_non_deadlocking_idle_exits_per_intention(
    implementation,
    mock_transitions,
    mock_configurations_schema,
    mock_state,
):
    """
    Verifies every non-IDLE Intention returns to IDLE when goal is None, and that
    navigation/combat/interaction states exit to IDLE on Goal category mismatch (B064).
    """
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    sprite = mock_state(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite.layer = "0"
    sprite.psyche.expression = None
    sprite.mutators.triggers.frightened = False

    # 1. Every configured non-IDLE intention must exit to IDLE when goal is None
    for intention in mock_configurations_schema.intentions:
        if intention == Intentions.IDLE.value:
            continue
        sprite.goal = None
        result = executor.evaluate(
            intention,
            {"sprite": sprite, "sprites": {}, "assets": {}},
        )
        assert result == Intentions.IDLE.value, (
            f"Intention '{intention}' failed to exit to IDLE with goal=None (got {result!r})"
        )

    # 2. Cross-layer Goals.DOOR substitution cleanly exits combat/social/wander/escape loops (B064)
    door_goal = Goal(name="door-1", category=Goals.DOOR, layer="0")
    for intention in (
        Intentions.HUNT.value,
        Intentions.ATTACK.value,
        Intentions.FOLLOW.value,
        Intentions.THREATEN.value,
        Intentions.ESCAPE.value,
        Intentions.WANDER.value,
        Intentions.BARTER.value,
        Intentions.BUILD.value,
        Intentions.MINE.value,
        Intentions.MOCK.value,
        Intentions.RETURN.value,
    ):
        sprite.goal = door_goal
        result = executor.evaluate(
            intention,
            {"sprite": sprite, "sprites": {}, "assets": {}},
        )
        assert result == Intentions.IDLE.value, (
            f"Intention '{intention}' deadlocked on Goals.DOOR (got {result!r})"
        )

    # 3. FIND and INTERACT exit to IDLE on TARGET or layer mismatch
    for intention in (Intentions.FIND.value, Intentions.INTERACT.value):
        sprite.goal = Goal(name="foe", category=Goals.TARGET, layer="0")
        assert (
            executor.evaluate(
                intention, {"sprite": sprite, "sprites": {}, "assets": {}}
            )
            == Intentions.IDLE.value
        )
        sprite.goal = Goal(name="door-1", category=Goals.DOOR, layer="other-layer")
        assert (
            executor.evaluate(
                intention, {"sprite": sprite, "sprites": {}, "assets": {}}
            )
            == Intentions.IDLE.value
        )


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_executor_evaluation_with_dictionary_lookup(
    implementation,
    mock_transitions,
    mock_configurations_schema,
    mock_state,
):
    """Verifies ATTACK exits to IDLE on dead target (B060) and transitions to HUNT on range loss."""
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    sprite = mock_state(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite.layer = "0"
    sprite.position = Position(100, 100)
    action_radius = sprite.mutators.parameters.action.radius

    enemy = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
        name="enemy",
    )
    enemy.layer = "0"

    # Dead target -> IDLE
    enemy.mutators.triggers.dead = True
    sprite.goal = Goal(
        name=enemy.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(100, 100),
    )
    assert (
        executor.evaluate(
            Intentions.ATTACK.value,
            {"sprite": sprite, "sprites": {enemy.name: enemy}},
        )
        == Intentions.IDLE.value
    )

    # Living target out of action.radius -> HUNT
    enemy.mutators.triggers.dead = False
    sprite.goal.position = Position(100 + action_radius + 10, 100)
    assert (
        executor.evaluate(
            Intentions.ATTACK.value,
            {"sprite": sprite, "sprites": {enemy.name: enemy}},
        )
        == Intentions.HUNT.value
    )


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_intention_speak_frightened_and_follow_subject_guards(
    implementation,
    mock_transitions,
    mock_configurations_schema,
    mock_board,
):
    """Verifies frightened exit from speak even with active expression, and follow -> speak guard (B073)."""
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    sprite_asset = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite = sprite_asset.state
    other = mock_board.instances(AssetInstances.SPRITES.value)[1].state

    sprite.layer = "0"
    other.layer = "0"
    sprite.position = Position(100, 100)
    other.position = Position(100, 100)
    other.mutators.triggers.dead = False
    sprite.psyche.dialogue = "greeting"
    sprite.psyche.expression = mock_board.cradle.spawn_expression(
        ExpressionsPalette.BUBBLES, Expressions.CONFUSION, sprite_asset
    )
    sprite.goal = Goal(
        name=other.name,
        category=Goals.SUBJECT,
        layer="0",
        position=Position(100, 100),
    )

    # Non-frightened with active expression stays in speak
    sprite.mutators.triggers.frightened = False
    assert (
        executor.evaluate(
            Intentions.SPEAK.value,
            {"sprite": sprite, "sprites": {other.name: other}},
        )
        is None
    )

    # Frightened exits speak -> idle immediately despite active expression
    sprite.mutators.triggers.frightened = True
    assert (
        executor.evaluate(
            Intentions.SPEAK.value,
            {"sprite": sprite, "sprites": {other.name: other}},
        )
        == Intentions.IDLE.value
    )

    # Player subject exits speak -> idle
    sprite.mutators.triggers.frightened = False
    sprite.goal.name = RequiredAssets.PLAYER
    assert (
        executor.evaluate(
            Intentions.SPEAK.value,
            {"sprite": sprite, "sprites": {}},
        )
        == Intentions.IDLE.value
    )

    # FIND -> SPEAK requires triggers.vision (no cross-vision telepathy)
    sprite.goal = Goal(
        name=other.name,
        category=Goals.SUBJECT,
        layer="0",
        position=Position(100, 100),
    )
    sprite.memory.relationships[other.name] = Relationships.FRIEND
    sprite.mutators.triggers.vision = False
    assert (
        executor.evaluate(
            Intentions.FIND.value,
            {"sprite": sprite, "sprites": {other.name: other}},
        )
        is None
    )
    sprite.mutators.triggers.vision = True
    assert (
        executor.evaluate(
            Intentions.FIND.value,
            {"sprite": sprite, "sprites": {other.name: other}},
        )
        == Intentions.SPEAK.value
    )

    # FOLLOW -> SPEAK rejects non-SUBJECT goal category (B073)
    sprite.goal = Goal(
        name=other.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(100, 100),
    )
    assert (
        executor.evaluate(
            Intentions.FOLLOW.value,
            {"sprite": sprite, "sprites": {other.name: other}},
        )
        == Intentions.IDLE.value
    )


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_intention_barter_and_mine_missing_keys_safe(
    implementation,
    mock_transitions,
    mock_configurations_schema,
    mock_state,
):
    """Verifies B071: missing inventory/price keys default to 0 without raising TypeError."""
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    sprite = mock_state(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite.goal = Goal(name="unlisted-item", category=Goals.RESOURCE, layer="0")
    sprite.inventory.pouch.clear()
    sprite.inventory.pack.clear()
    sprite.memory.prices.clear()
    sprite.psyche.motivation = Motivations.SURVIVAL

    # barter: 0 < 0 is False -> None (no TypeError)
    assert executor.evaluate(Intentions.BARTER.value, {"sprite": sprite}) is None

    # barter: pouch missing (0) < price (10.0) -> threaten
    sprite.memory.prices["unlisted-item"] = 10.0
    assert (
        executor.evaluate(Intentions.BARTER.value, {"sprite": sprite})
        == Intentions.THREATEN.value
    )

    # mine: pack missing (0) == 0 -> mine; pack > 0 -> build
    assert (
        executor.evaluate(Intentions.MINE.value, {"sprite": sprite})
        == Intentions.MINE.value
    )
    sprite.inventory.pack["unlisted-item"] = 2
    assert (
        executor.evaluate(Intentions.MINE.value, {"sprite": sprite})
        == Intentions.BUILD.value
    )


@pytest.mark.workflow_plots
@pytest.mark.parametrize("implementation", BACKENDS)
def test_executor_evaluation_with_plot_metadata(
    implementation,
    mock_transitions,
    mock_configurations_schema,
    mock_state_schema,
):
    translator = mock_transitions(implementation)
    executor = translator.compile(mock_configurations_schema.plots)

    mock_player_state = mock_state_schema.sheets.players[0]
    mock_plot_state = mock_state_schema.plots
    mock_player_state.inventory.pack["writ-of-dawn"] = 1

    result = executor.evaluate(
        mock_plot_state.current,
        {
            "plot": mock_plot_state,
            "sprites": {"player": mock_player_state},
        },
    )
    assert result == "castle-dawn-unlocked"


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_executor_evaluation_attribute_error_handling(
    implementation,
    mock_configurations_schema,
    mock_transitions,
    mock_state,
):
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    mock_crate_state = mock_state(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    assert executor.evaluate(Intentions.IDLE.value, {"sprite": mock_crate_state}) is None


@pytest.mark.modality_intention
@pytest.mark.parametrize("implementation", BACKENDS)
def test_executor_evaluation_with_environ_functions(
    implementation,
    mock_transitions,
    mock_configurations_schema,
    mock_state,
):
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    sprite = mock_state(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite.position.x = 0
    sprite.position.y = 0

    for cat in (Goals.OBJECT, Goals.DOOR):
        sprite.goal = Goal(
            name="test-goal",
            layer=sprite.layer,
            category=cat,
            position=Position(x=1, y=1),
        )
        assert (
            executor.evaluate(Intentions.FIND.value, {"sprite": sprite})
            == Intentions.INTERACT.value
        )


@pytest.mark.parametrize("implementation", BACKENDS)
def test_executor_evaluation_with_bad_arguments(
    implementation,
    mock_transitions,
    mock_configurations_schema,
):
    executor = mock_transitions(implementation).compile(
        mock_configurations_schema.intentions
    )
    assert executor.evaluate("unknown", {}) is None
