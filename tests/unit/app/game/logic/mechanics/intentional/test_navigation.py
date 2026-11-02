"""
@domain.test
@test.unit
@app.mechanic
@modality.intention
@workflow.navigation

# Ontology: Tests - tests.unit.app.game.logic.mechanics.intentional.test_navigation

Unit tests for NavigationMechanics.
"""
# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Goals,
    Intentions,
    Mechanics,
)
from app.game.logic.mechanics import NavigationMechanics
from app.models.state import Goal

# Cython Libraries
from libs.core.models import (
    Boundary,
    Dimensions,
    Hitbox,
    Position,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.modality_intention,
    pytest.mark.workflow_navigation,
]

# -----------------------------------------------------

# ---------------------------------------------------------------------------
# ANCHOR & OBSTACLE TESTS
# ---------------------------------------------------------------------------


def test_navigation_anchor_with_hitbox(mock_asset):
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    anchor = NavigationMechanics.anchor(sprite)
    assert anchor.x == (
        sprite.state.position.x
        + sprite.hitboxes[0].position.x
        + sprite.hitboxes[0].dimensions.w // 2
    )
    assert anchor.y == (
        sprite.state.position.y
        + sprite.hitboxes[0].position.y
        + sprite.hitboxes[0].dimensions.l // 2
    )


def test_navigation_anchor_fallback_dimensions(mock_asset):
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.properties.hitboxes = []
    anchor = NavigationMechanics.anchor(crate)
    assert anchor.x == crate.state.position.x + crate.dimensions.w // 2
    assert anchor.y == crate.state.position.y + crate.dimensions.l // 2


def test_navigation_obstacles_offset_hitbox(mock_board):
    sprite = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]
    hb = sprite.hitboxes[0]
    obs = NavigationMechanics.obstacles(layer="0", board=mock_board, exclude=[])

    expected = (
        float(sprite.state.position.x + hb.position.x),
        float(sprite.state.position.y + hb.position.y),
        float(hb.dimensions.w),
        float(hb.dimensions.l),
    )
    assert expected in obs


def test_navigation_obstacles_multi_hitbox(mock_board):
    strut = mock_board.asset("test-strut", "0")
    hb1 = Hitbox(Position(178, 102), Dimensions(25, 12))
    hb2 = Hitbox(Position(17, 102), Dimensions(25, 12))
    hb3 = Hitbox(Position(5, 39), Dimensions(203, 63))
    strut.properties.hitboxes[strut.state.blueprint] = [hb1, hb2, hb3]

    obs = NavigationMechanics.obstacles(layer="0", board=mock_board, exclude=[])

    sx, sy = strut.state.position.x, strut.state.position.y
    assert (float(sx + 178), float(sy + 102), 25.0, 12.0) in obs
    assert (float(sx + 17), float(sy + 102), 25.0, 12.0) in obs
    assert (float(sx + 5), float(sy + 39), 203.0, 63.0) in obs


def test_navigation_obstacles_exclusion_and_perimeters(mock_board):
    sprite = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]
    hb = sprite.hitboxes[0]
    sprite_box = (
        float(sprite.state.position.x + hb.position.x),
        float(sprite.state.position.y + hb.position.y),
        float(hb.dimensions.w),
        float(hb.dimensions.l),
    )
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(0, 0), Dimensions(10, 20))],
    }

    obs = NavigationMechanics.obstacles(
        layer="0",
        board=mock_board,
        exclude=[sprite.name],
        elevation=0,
    )

    assert sprite_box not in obs
    assert (0.0, 0.0, 10.0, 20.0) in obs


def test_navigation_obstacles_elevation_partitioning(mock_board):
    sprite = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]
    sprite.elevation = 1
    hb = sprite.hitboxes[0]
    sprite_box = (
        float(sprite.state.position.x + hb.position.x),
        float(sprite.state.position.y + hb.position.y),
        float(hb.dimensions.w),
        float(hb.dimensions.l),
    )
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(0, 0), Dimensions(10, 20))],
        1: [Boundary(Position(50, 50), Dimensions(30, 40))],
    }

    obs_tier0 = NavigationMechanics.obstacles(
        layer="0",
        board=mock_board,
        exclude=[],
        elevation=0,
    )
    assert sprite_box not in obs_tier0
    assert (0.0, 0.0, 10.0, 20.0) in obs_tier0
    assert (50.0, 50.0, 30.0, 40.0) not in obs_tier0

    obs_tier1 = NavigationMechanics.obstacles(
        layer="0",
        board=mock_board,
        exclude=[],
        elevation=1,
    )
    assert sprite_box in obs_tier1
    assert (0.0, 0.0, 10.0, 20.0) not in obs_tier1
    assert (50.0, 50.0, 30.0, 40.0) in obs_tier1


# ---------------------------------------------------------------------------
# STATE & TARGET ANCHOR TESTS
# ---------------------------------------------------------------------------


def test_navigation_navigating(mock_asset):
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite.state.goal = Goal(name="target", category=Goals.TARGET.value)

    sprite.state.intention = Intentions.FIND
    assert NavigationMechanics.navigating(sprite) is True

    sprite.state.intention = Intentions.HUNT
    assert NavigationMechanics.navigating(sprite) is True

    sprite.state.intention = Intentions.WANDER
    assert NavigationMechanics.navigating(sprite) is True

    sprite.state.intention = Intentions.IDLE
    assert NavigationMechanics.navigating(sprite) is False

    sprite.state.intention = Intentions.ATTACK
    assert NavigationMechanics.navigating(sprite) is False

    sprite.state.goal = None
    sprite.state.intention = Intentions.FIND
    assert NavigationMechanics.navigating(sprite) is False


def test_navigation_clear(mock_mechanic, mock_asset):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite.state.trajectory.target = Position(10, 10)
    sprite.state.trajectory.vertices = [Position(10, 10), Position(20, 20)]
    sprite.state.trajectory.stalled = True

    mechanic._clear(sprite)

    assert sprite.state.trajectory.target is None
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.stalled is False


def test_navigation_target_same_layer_asset(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    mock_board.relayer(player, sprite.state.layer)
    player.state.position = Position(300, 300)

    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer=player.state.layer,
        position=Position(300, 300),
    )

    target_anchor = mechanic._target(sprite, mock_board)
    expected_anchor = NavigationMechanics.anchor(player)

    assert target_anchor.x == expected_anchor.x
    assert target_anchor.y == expected_anchor.y


def test_navigation_target_coordinate_displacement(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.goal = Goal(
        name=None,
        category=Goals.POSITION.value,
        position=Position(50, 50),
    )

    anchor = NavigationMechanics.anchor(sprite)
    offset_x = anchor.x - sprite.state.position.x
    offset_y = anchor.y - sprite.state.position.y

    target_anchor = mechanic._target(sprite, mock_board)
    assert target_anchor.x == 50 + offset_x
    assert target_anchor.y == 50 + offset_y


# ---------------------------------------------------------------------------
# TRAJECTORY PLANNING & PROGRESSION TESTS
# ---------------------------------------------------------------------------


def test_navigation_clear_line_of_sight(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(10, 10)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="open-space",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(30, 10),
    )

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.target == sprite.state.goal.position
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.stalled is False
    assert sprite.state.trajectory.cooldown == 0


def test_navigation_occluded_los_generates_waypoints(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value, "0")[0]

    sprite.state.position = Position(100, 500)
    sprite.state.intention = Intentions.FIND.value
    crate.state.position = Position(180, 515)
    sprite.state.goal = Goal(
        name="behind-crate",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(260, 500),
    )
    mock_board.perimeters["0"] = {0: []}

    mechanic._navigate(sprite, mock_board)

    assert len(sprite.state.trajectory.vertices) >= 1
    assert sprite.state.trajectory.target == sprite.state.trajectory.vertices[0]
    assert sprite.state.trajectory.stalled is False
    assert sprite.state.trajectory.cooldown == 0


def test_navigation_stalled_path_enters_cooldown(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(100, 500)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="unreachable",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 500),
    )
    # Enclose the destination inside an impassable boundary box
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(250, 450), Dimensions(150, 150))],
    }

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.stalled is True
    assert sprite.state.trajectory.target is None
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.cooldown == getattr(
        settings, "PATH_RETRY_INTERVAL", 60
    )


def test_navigation_cooldown_active_bypasses_planner(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(100, 500)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="unreachable",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 500),
    )
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(250, 450), Dimensions(150, 150))],
    }
    sprite.state.trajectory.cooldown = 10

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.cooldown == 9
    assert sprite.state.trajectory.vertices == []


def test_navigation_waypoint_arrival_advances_queue(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(100, 500)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 500),
    )
    # Block direct LOS to goal (x=300), while keeping LOS to wp1 (x=100) clear
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(220, 450), Dimensions(40, 150))],
    }

    wp1 = Position(100, 500)
    wp2 = Position(150, 400)
    sprite.state.trajectory.vertices = [wp1, wp2]
    sprite.state.trajectory.target = wp1

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.vertices == [wp2]
    assert sprite.state.trajectory.target == wp2


def test_navigation_waypoint_arrival_final_sets_goal_target(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(150, 500)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 500),
    )
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(220, 450), Dimensions(40, 150))],
    }

    wp_last = Position(150, 500)
    sprite.state.trajectory.vertices = [wp_last]
    sprite.state.trajectory.target = wp_last

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.target == sprite.state.goal.position


def test_navigation_dynamic_replan_when_waypoint_blocked(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(100, 500)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(260, 500),
    )

    old_wp = Position(200, 500)
    sprite.state.trajectory.vertices = [old_wp]
    sprite.state.trajectory.target = old_wp

    # Place an obstacle between sprite (x=100) and old_wp (x=200)
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(160, 510), Dimensions(24, 24))],
    }

    mechanic._navigate(sprite, mock_board)

    assert len(sprite.state.trajectory.vertices) >= 1
    assert sprite.state.trajectory.vertices[0] != old_wp
    assert sprite.state.trajectory.target == sprite.state.trajectory.vertices[0]


def test_navigation_update_processes_sprites_skips_player(
    mock_mechanic,
    mock_board,
    mock_payload,
    mock_bus,
):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite1 = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()
    payload = mock_payload()

    sprite1.state.position = Position(10, 10)
    sprite1.state.goal = Goal(
        name="target1",
        category=Goals.POSITION.value,
        layer=sprite1.state.layer,
        position=Position(30, 10),
    )
    sprite1.state.intention = Intentions.FIND.value

    player.state.intention = Intentions.FIND.value
    player.state.goal = Goal(
        name="player-goal",
        category=Goals.POSITION.value,
        layer=player.state.layer,
        position=Position(50, 50),
    )

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert sprite1.state.trajectory.target == sprite1.state.goal.position
    assert not hasattr(player.state, "trajectory")