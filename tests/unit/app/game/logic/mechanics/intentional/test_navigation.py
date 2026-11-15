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

# ---------------------------------------------------------------------------
# ANCHOR, PADDING & OBSTACLE TESTS
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


def test_navigation_padding_with_hitbox_and_squeeze(mock_asset):
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    pad_x, pad_y = NavigationMechanics.padding(sprite)
    hb = sprite.hitboxes[0]
    squeeze = float(sprite.state.mutators.parameters.squeeze.radius)
    assert pad_x == hb.dimensions.w / 2.0 + squeeze
    assert pad_y == hb.dimensions.l / 2.0 + squeeze


def test_navigation_padding_fallback_dimensions(mock_asset):
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.properties.hitboxes = []
    crate.state.mutators.parameters.squeeze = None
    pad_x, pad_y = NavigationMechanics.padding(crate)
    assert pad_x == crate.dimensions.w / 2.0
    assert pad_y == crate.dimensions.l / 2.0


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


def test_navigation_obstacles_minkowski_inflation(mock_board):
    sprite = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]
    hb = sprite.hitboxes[0]
    obs = NavigationMechanics.obstacles(
        layer="0",
        board=mock_board,
        exclude=[],
        pad_x=10.0,
        pad_y=8.0,
    )

    expected = (
        float(sprite.state.position.x + hb.position.x) - 10.0,
        float(sprite.state.position.y + hb.position.y) - 8.0,
        float(hb.dimensions.w) + 20.0,
        float(hb.dimensions.l) + 16.0,
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


def test_navigation_obstacles_queries_requested_elevation_tier(mock_board):
    """
    Verifies Bug B030: obstacles() resolves hitboxes at the target elevation
    argument rather than the asset's base elevation.
    """
    strut = mock_board.asset("test-strut", "0")
    hb_tier0 = Hitbox(Position(0, 0), Dimensions(10, 10))
    hb_tier1 = Hitbox(Position(20, 20), Dimensions(30, 30))

    strut.elevation = 0
    strut.hitbox.elevations = lambda props, state: [0, 1]
    strut.hitbox.get = lambda props, state, elev: [hb_tier0] if elev == 0 else [hb_tier1]

    sx, sy = strut.state.position.x, strut.state.position.y
    obs_tier1 = NavigationMechanics.obstacles(
        layer="0",
        board=mock_board,
        exclude=[],
        elevation=1,
    )

    assert (float(sx + 20), float(sy + 20), 30.0, 30.0) in obs_tier1
    assert (float(sx), float(sy), 10.0, 10.0) not in obs_tier1


# ---------------------------------------------------------------------------
# STATE & TARGET ANCHOR TESTS
# ---------------------------------------------------------------------------


def test_navigation_navigating(mock_asset):
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite.state.goal = Goal(name="target", category=Goals.TARGET.value)

    for nav_intention in (
        Intentions.FIND,
        Intentions.FOLLOW,
        Intentions.HUNT,
        Intentions.ESCAPE,
        Intentions.WANDER,
        Intentions.RETURN,
    ):
        sprite.state.intention = nav_intention
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


def test_navigation_target_none_when_no_goal(mock_mechanic, mock_asset, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite.state.goal = None

    assert mechanic._target(sprite, mock_board) is None


def test_navigation_target_none_when_goal_position_none(mock_mechanic, mock_asset, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite.state.goal = Goal(
        name="missing-entity",
        category=Goals.TARGET.value,
        layer="0",
        position=None,
    )

    assert mechanic._target(sprite, mock_board) is None


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


def test_navigation_target_cross_layer_asset_falls_back_to_displacement(
    mock_mechanic,
    mock_board,
):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    mock_board.relayer(player, "house-layer")
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer=sprite.state.layer,
        position=Position(80, 90),
    )

    anchor = NavigationMechanics.anchor(sprite)
    offset_x = anchor.x - sprite.state.position.x
    offset_y = anchor.y - sprite.state.position.y

    target_anchor = mechanic._target(sprite, mock_board)
    assert target_anchor.x == 80 + offset_x
    assert target_anchor.y == 90 + offset_y


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


def test_navigation_inactive_intention_clears_trajectory(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.intention = Intentions.IDLE.value
    sprite.state.trajectory.target = Position(100, 100)
    sprite.state.trajectory.vertices = [Position(100, 100)]
    sprite.state.trajectory.stalled = True

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.target is None
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.stalled is False


def test_navigation_cross_layer_goal_clears_trajectory(mock_mechanic, mock_board):
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="remote-target",
        category=Goals.POSITION.value,
        layer="house-layer",
        position=Position(100, 100),
    )
    sprite.state.trajectory.target = Position(50, 50)
    sprite.state.trajectory.vertices = [Position(50, 50)]
    sprite.state.trajectory.stalled = True

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.target is None
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.stalled is False


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


def test_navigation_clear_los_tracks_moving_same_layer_asset_when_goal_position_none(
    mock_mechanic,
    mock_board,
):
    """
    Verifies Bug B031: when pursuing a same-layer asset with clear LOS and
    goal.position=None, trajectory.target resolves to the target asset's
    offset-adjusted coordinate.
    """
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    player = mock_board.player()

    mock_board.relayer(player, sprite.state.layer)
    sprite.state.position = Position(100, 800)
    player.state.position = Position(200, 800)
    sprite.state.intention = Intentions.FOLLOW.value
    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer=sprite.state.layer,
        position=None,
    )

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.target == Position(200, 800)


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


def test_navigation_minkowski_los_detects_grazing_obstacle(mock_mechanic, mock_board):
    """
    Verifies Bug B028: an obstacle whose top edge lies 1px below the raw 1D
    anchor ray (y=542 vs y=541) but intersects the sprite's physical hitbox
    and squeeze envelope triggers RRT waypoint generation instead of direct LOS.
    """
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value, "0")[0]

    sprite.state.position = Position(100, 500)
    sprite.state.intention = Intentions.FIND.value
    crate.state.position = Position(180, 542)
    sprite.state.goal = Goal(
        name="grazing-crate",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(260, 500),
    )
    mock_board.perimeters["0"] = {0: []}

    mechanic._navigate(sprite, mock_board)

    assert len(sprite.state.trajectory.vertices) >= 1
    assert sprite.state.trajectory.target == sprite.state.trajectory.vertices[0]


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


def test_navigation_intermediate_corner_waypoint_waits_for_los_clearance(
    mock_mechanic,
    mock_board,
):
    """
    Verifies Bug B029: an intermediate corner waypoint within action.radius
    is not popped while the ray to the next waypoint remains occluded by the corner.
    """
    mechanic = mock_mechanic(Mechanics.NAVIGATION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.position = Position(95, 800)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 800),
    )
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(170, 820), Dimensions(40, 100))],
    }

    # wp1 is within action.radius (25px) of (95, 800), while wp2 is occluded behind the corner
    wp1 = Position(110, 785)
    wp2 = Position(240, 820)
    sprite.state.trajectory.vertices = [wp1, wp2]
    sprite.state.trajectory.target = wp1

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.vertices == [wp1, wp2]
    assert sprite.state.trajectory.target == wp1


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

    # Place an obstacle intersecting the footprint anchor ray (y=541) between x=132 and x=232
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(160, 530), Dimensions(24, 24))],
    }

    mechanic._navigate(sprite, mock_board)

    assert len(sprite.state.trajectory.vertices) >= 1
    assert sprite.state.trajectory.vertices[0] != old_wp
    assert sprite.state.trajectory.target == sprite.state.trajectory.vertices[0]


def test_navigation_dynamic_replan_stalls_when_enclosed(mock_mechanic, mock_board):
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

    old_wp = Position(260, 500)
    sprite.state.trajectory.vertices = [old_wp]
    sprite.state.trajectory.target = old_wp

    # Enclose both old_wp and destination inside an impassable box blocking y=541
    mock_board.perimeters["0"] = {
        0: [Boundary(Position(160, 450), Dimensions(250, 200))],
    }

    mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.stalled is True
    assert sprite.state.trajectory.target is None
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.cooldown == getattr(
        settings, "PATH_RETRY_INTERVAL", 60
    )


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