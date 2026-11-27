"""
@domain.test
@test.unit
@app.module
@modality.intention
@workflow.cognition

# Ontology: Tests - tests.unit.app.game.logic.modules.cognition.test_pipeline

Unit tests for Perception, Recall, and tiered Instincts (Survival, Combat,
Social, Explore).
"""
# External Libraries
import pytest

# Application Libraries
from app.models.state.assets.sheets import Goal
from app.static.semantics import (
    AssetInstances,
    Goals,
    Intentions,
    Relationships,
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
# PERCEPTION TESTS
# ---------------------------------------------------------------------------


def test_perception_scan_copies_positions_wakes_dormant_and_evicts_dead(
    mock_perception,
    mock_board,
):
    """Verifies B074 (Position snapshot copy), B019/B059 (dormant wake), and B086 (dead eviction)."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    sprite.state.layer = "0"
    player.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    player.state.position = Position(1840, 1820)
    player.state.mutators.triggers.dead = False
    sprite.state.memory.sprites.clear()

    dormant_goal = Goal(
        name=player.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(0, 0),
        dormant=True,
    )
    sprite.state.memory.goals = {player.name: dormant_goal}

    mock_perception.scan(sprite, mock_board)

    # Copied Position snapshot is decoupled from live player.state.position (B074)
    snapshot = sprite.state.memory.sprites[player.name]
    assert (snapshot.x, snapshot.y) == (1840, 1820)
    player.state.position.x = 1890
    assert snapshot.x == 1840

    # Dormant goal woken and coordinates refreshed (B019, B059)
    assert dormant_goal.dormant is False
    assert (dormant_goal.position.x, dormant_goal.position.y) == (1840, 1820)

    # Observing dead target evicts it from memory.goals (B086)
    player.state.position = Position(1840, 1820)
    player.state.mutators.triggers.dead = True
    mock_perception.scan(sprite, mock_board)
    assert player.name not in sprite.state.memory.goals


def test_perception_scan_cross_layer_wake_rules_and_stall_suppression(
    mock_perception,
    mock_board,
):
    """Verifies B081: cross-layer dormant goals wake on new edges or layer changes, not stalled doors."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]

    sprite.state.layer = "0"
    sprite.state.position = Position(
        door.state.position.x + 10, door.state.position.y + 10
    )
    sprite.state.memory.doors.clear()

    cross_goal = Goal(
        name="remote-chest",
        category=Goals.OBJECT,
        layer=door.state.outlayer,
        dormant=True,
    )
    sprite.state.memory.goals = {cross_goal.name: cross_goal}

    # Initial sighting of an unmapped Door wakes cross-layer dormant goal
    mock_perception.scan(sprite, mock_board)
    assert cross_goal.dormant is False

    # After door stalls and unwinds, re-scanning the same stalled Door does NOT re-wake (B081)
    cross_goal.dormant = True
    mock_perception.mark_stalled_door(sprite.name, "0", door.name)
    mock_perception.scan(sprite, mock_board)
    assert cross_goal.dormant is True

    # Learning a new memory.doors edge reaching cross_goal.layer DOES wake it
    sprite.state.memory.doors = {"0": {door.name: door.state.outlayer}}
    mock_perception.scan(sprite, mock_board)
    assert cross_goal.dormant is False


def test_perception_scan_static_goal_backoff_and_eviction(
    mock_perception,
    mock_board,
):
    """Verifies B088: stalled static goals respect backoff cooldown before waking, and missing ones evict."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    chest = mock_board.instances(AssetInstances.CHESTS.value, "0")[0]

    sprite.state.layer = "0"
    sprite.state.position = Position(
        chest.state.position.x + 10, chest.state.position.y + 10
    )
    chest_goal = Goal(
        name=chest.name,
        category=Goals.OBJECT,
        layer="0",
        position=Position(chest.state.position.x, chest.state.position.y),
        dormant=True,
    )
    sprite.state.memory.goals = {chest.name: chest_goal}
    mock_perception.mark_stalled_static(sprite.name, "0", chest.name, cooldown=2)

    # Tick 1: cooldown 2 -> 1 (remains dormant)
    mock_perception.scan(sprite, mock_board)
    assert chest_goal.dormant is True

    # Tick 2: cooldown 1 -> 0 (expired, wakes)
    mock_perception.scan(sprite, mock_board)
    assert chest_goal.dormant is False

    # Missing static asset observed within vision.radius is evicted
    ghost_goal = Goal(
        name="missing-chest",
        category=Goals.OBJECT,
        layer="0",
        position=Position(sprite.state.position.x, sprite.state.position.y),
        dormant=True,
    )
    sprite.state.memory.goals[ghost_goal.name] = ghost_goal
    mock_perception.scan(sprite, mock_board)
    assert ghost_goal.name not in sprite.state.memory.goals


def test_perception_fear_low_health_and_outnumbered(mock_perception, mock_board):
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    other = mock_board.instances(AssetInstances.SPRITES.value)[1]
    player = mock_board.player()

    sprite.state.layer = "0"
    other.state.layer = "0"
    player.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    other.state.position = Position(1820, 1800)
    player.state.position = Position(1830, 1800)
    sprite.state.meters.health.current = sprite.state.meters.health.maximum
    sprite.state.mutators.parameters.fear.enemy = 2
    sprite.state.memory.relationships = {
        other.name: Relationships.FOE,
        player.name: Relationships.FOE,
    }

    # 2 living same-layer FOEs within fear.radius -> frightened
    assert mock_perception.fear(sprite, mock_board) is True
    assert sprite.state.mutators.triggers.frightened is True

    # Dead FOE excluded -> below threshold -> not frightened
    other.state.mutators.triggers.dead = True
    assert mock_perception.fear(sprite, mock_board) is False

    # Low health ratio (< fear.limit) triggers frightened even with 0 threats
    player.state.position = Position(100, 100)
    sprite.state.meters.health.current = 1
    assert mock_perception.fear(sprite, mock_board) is True

    # Dead sprite clears frightened
    sprite.state.mutators.triggers.dead = True
    assert mock_perception.fear(sprite, mock_board) is False


def test_perception_track_epistemic_isolation_and_observed_door_transit(
    mock_perception,
    mock_board,
):
    """
    Verifies unseen cross-layer targets do NOT leak goal.layer (no telepathy), while
    directly observing a target transit a visible Door updates goal.layer, exit coords,
    and memory.doors (B083).
    """
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]

    # 1. Unseen target changing layers does NOT update goal.layer
    sprite.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    sprite.state.mutators.triggers.vision = False
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(100, 100),
    )
    mock_board.relayer(player, door.state.outlayer)

    mock_perception.track(sprite, mock_board)
    assert sprite.state.goal.layer == "0"
    assert sprite.state.mutators.triggers.vision is False

    # 2. Observed Door transit updates goal.layer to outlayer, coords to door.state.out, and memory.doors
    sprite.state.position = Position(
        door.state.position.x + 15, door.state.position.y + 15
    )
    sprite.state.mutators.triggers.vision = True
    sprite.state.memory.doors.clear()
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET,
        layer="0",
        position=Position(door.state.position.x, door.state.position.y),
    )

    mock_perception.track(sprite, mock_board)

    assert sprite.state.goal.layer == door.state.outlayer
    assert (sprite.state.goal.position.x, sprite.state.goal.position.y) == (
        door.state.out.x,
        door.state.out.y,
    )
    assert sprite.state.memory.doors["0"][door.name] == door.state.outlayer
    assert sprite.state.mutators.triggers.vision is False


def test_perception_track_static_object_aligns_contact_origin(
    mock_perception,
    mock_board,
):
    """Verifies B084: tracking an OBJECT aligns goal.position to hitbox-contact Sprite origin."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    chest = mock_board.instances(AssetInstances.CHESTS.value, "0")[0]

    sprite.state.layer = "0"
    sprite.state.position = Position(
        chest.state.position.x - 40, chest.state.position.y
    )
    sprite.state.goal = Goal(
        name=chest.name,
        category=Goals.OBJECT,
        layer="0",
        position=Position(0, 0),
    )

    mock_perception.track(sprite, mock_board)

    expected = mock_perception._contact_origin(sprite, chest)
    assert (sprite.state.goal.position.x, sprite.state.goal.position.y) == (
        expected.x,
        expected.y,
    )
    assert sprite.state.mutators.triggers.vision is True


# ---------------------------------------------------------------------------
# RECALL TESTS
# ---------------------------------------------------------------------------


def test_recall_idle_only_lifo_stack_and_dormant_skip(mock_recall, mock_board):
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    g_dormant = Goal(name="dormant-foe", category=Goals.TARGET, layer="0", dormant=True)
    g_awake = Goal(name="awake-obj", category=Goals.OBJECT, layer="0", dormant=False)
    g_stack_bottom = Goal(name="bottom", category=Goals.TARGET, layer="1")
    g_stack_top = Goal(name="top", category=Goals.SUBJECT, layer="1")

    sprite.state.memory.stack = [g_stack_bottom, g_stack_top]
    sprite.state.memory.goals = {
        g_dormant.name: g_dormant,
        g_awake.name: g_awake,
    }

    # Non-IDLE intention returns None
    sprite.state.intention = Intentions.HUNT
    sprite.state.goal = None
    assert mock_recall.remember(sprite, mock_board) is None

    # IDLE with active goal returns None
    sprite.state.intention = Intentions.IDLE
    sprite.state.goal = Goal(name="active", category=Goals.POSITION, layer="0")
    assert mock_recall.remember(sprite, mock_board) is None

    # IDLE with goal=None pops stack in LIFO order before memory.goals
    sprite.state.goal = None
    assert mock_recall.remember(sprite, mock_board) is g_stack_top
    assert mock_recall.remember(sprite, mock_board) is g_stack_bottom

    # Stack empty -> skips dormant goal and returns non-dormant episodic goal (B019/B059)
    assert mock_recall.remember(sprite, mock_board) is g_awake
    assert g_dormant.name in sprite.state.memory.goals
    assert mock_recall.remember(sprite, mock_board) is None


# ---------------------------------------------------------------------------
# TIERED INSTINCTS TESTS
# ---------------------------------------------------------------------------


def test_survival_instinct_flee_centroid_clamping_and_corner_deflection(
    mock_survival_instinct,
    mock_board,
):
    """Verifies B072: SurvivalInstinct generates clamped escape coordinates with corner deflection."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    sprite.state.layer = "0"
    player.state.layer = "0"
    sprite.state.memory.relationships[player.name] = Relationships.FOE

    # Not frightened -> None
    sprite.state.mutators.triggers.frightened = False
    assert mock_survival_instinct.generate(sprite, mock_board) is None

    # Frightened with threat to the east -> flees west
    sprite.state.mutators.triggers.frightened = True
    sprite.state.position = Position(1800, 1800)
    player.state.position = Position(1860, 1800)

    goal = mock_survival_instinct.generate(sprite, mock_board)
    assert goal is not None
    assert goal.category == Goals.POSITION
    assert goal.name == Intentions.ESCAPE.value
    assert goal.layer == "0"
    assert goal.position.x < sprite.state.position.x

    # Trapped in top-left corner (0, 0) with threat southeast -> corner deflection avoids action.radius
    sprite.state.position = Position(0, 0)
    player.state.position = Position(40, 40)
    action_radius = sprite.state.mutators.parameters.action.radius

    corner_goal = mock_survival_instinct.generate(sprite, mock_board)
    assert corner_goal is not None
    dist_sq = corner_goal.position.x ** 2 + corner_goal.position.y ** 2
    assert dist_sq > action_radius ** 2

    # Frightened with zero visible threats -> safe fallback goal within layer bounds
    player.state.position = Position(2500, 2500)
    sprite.state.position = Position(1800, 1800)
    fallback_goal = mock_survival_instinct.generate(sprite, mock_board)
    assert fallback_goal is not None
    assert fallback_goal.category == Goals.POSITION
    assert fallback_goal.name == Intentions.ESCAPE.value


def test_combat_instinct_selects_nearest_visible_living_foe_when_armed(
    mock_combat_instinct,
    mock_board,
):
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    other = mock_board.instances(AssetInstances.SPRITES.value)[1]
    player = mock_board.player()

    sprite.state.layer = "0"
    other.state.layer = "0"
    player.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    other.state.position = Position(1880, 1800)
    player.state.position = Position(1830, 1800)
    sprite.state.memory.relationships = {
        other.name: Relationships.FOE,
        player.name: Relationships.FOE,
    }

    # Unarmed -> None (inadmissible ATTACK equipment)
    sprite.state.slots.equipment.weapon = None
    assert mock_combat_instinct.generate(sprite, mock_board) is None

    # Armed -> picks nearest living FOE (player at dx=30 vs other at dx=80)
    sprite.state.slots.equipment.weapon = "sword"
    goal = mock_combat_instinct.generate(sprite, mock_board)
    assert goal is not None
    assert goal.category == Goals.TARGET
    assert goal.name == player.name

    # Dead nearest FOE skipped -> picks living second FOE
    player.state.mutators.triggers.dead = True
    goal = mock_combat_instinct.generate(sprite, mock_board)
    assert goal is not None
    assert goal.name == other.name


def test_social_instinct_selects_visible_friend_or_family_with_dialogue(
    mock_social_instinct,
    mock_board,
):
    """Verifies B073: SocialInstinct requires psyche.dialogue and FRIEND/FAMILY relationship."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    sprite.state.layer = "0"
    player.state.layer = "0"
    sprite.state.position = Position(1800, 1800)
    player.state.position = Position(1840, 1800)
    sprite.state.memory.relationships = {player.name: Relationships.FOE}
    sprite.state.psyche.dialogue = "greeting"

    # FOE is not conversable
    assert mock_social_instinct.generate(sprite, mock_board) is None

    # FRIEND with dialogue -> Goals.SUBJECT
    sprite.state.memory.relationships[player.name] = Relationships.FRIEND
    goal = mock_social_instinct.generate(sprite, mock_board)
    assert goal is not None
    assert goal.category == Goals.SUBJECT
    assert goal.name == player.name

    # Missing dialogue -> None
    sprite.state.psyche.dialogue = None
    assert mock_social_instinct.generate(sprite, mock_board) is None


def test_explore_instinct_generates_clamped_dry_wander_position(
    mock_explore_instinct,
    mock_board,
):
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite.state.layer = "0"
    sprite.state.position = Position(1800, 1800)

    bound_w, bound_l = mock_explore_instinct.bounds(sprite, mock_board)
    action_radius = sprite.state.mutators.parameters.action.radius

    goal = mock_explore_instinct.generate(sprite, mock_board)

    assert goal is not None
    assert goal.category == Goals.POSITION
    assert goal.name == Intentions.WANDER.value
    assert goal.layer == "0"
    assert 0 <= goal.position.x <= bound_w
    assert 0 <= goal.position.y <= bound_l
    dx = goal.position.x - sprite.state.position.x
    dy = goal.position.y - sprite.state.position.y
    assert (dx * dx + dy * dy) > (action_radius * action_radius)
    assert mock_board.fluid("0", goal.position) is False
