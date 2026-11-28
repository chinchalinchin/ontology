"""
@domain.test
@test.unit
@app.mechanic
@physics.motion
@workflow.collisions

# Ontology: Tests - tests.unit.app.game.logic.mechanics.spatial.test_collision

Unit tests for CollisionMechanics.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Mechanics,
    Directions
)

# Cython Libraries
from libs.core.models import (
    Position,
    Velocity,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.physics_motion,
    pytest.mark.workflow_collisions,
]

# ---------------------------------------------------------------------------


def test_collision_mechanics_update(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies the two-phase collision pipeline: Environmental Constraints (Phase 1)
    and Dynamic Entity Collisions (Phase 2) executing live on the board.
    """
    # Setup Phase 0: Fixtures
    payload = mock_payload()
    player = mock_board.player()
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    # Setup Phase 1: Position crate intersecting the western perimeter with incoming velocity
    crate.state.position = Position(0, 50)
    crate.state.velocity = Velocity(-10.0, 0.0)

    # Setup Phase 2: Position player and NPC overlapping in open space
    player.state.position = Position(100, 100)
    sprite.state.position = Position(100, 100)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    # Phase 1 Assertion: Crate is displaced eastward out of boundary and velocity inverts
    assert crate.state.position.x > 0
    assert crate.state.velocity.vx == 10.0

    # Phase 2 Assertion: Overlapping dynamic bodies resolve overlap
    assert (
        player.state.position.x != sprite.state.position.x
        or player.state.position.y != sprite.state.position.y
    )


def test_collision_mechanics_resolve(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 2 narrow-phase AABB overlap resolution and spatial separation.
    """
    player = mock_board.player()
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    player.state.position = Position(10, 10)
    crate.state.position = Position(20, 20)
    initial_crate_y = crate.state.position.y

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.y != initial_crate_y


def test_collision_mechanics_resolve_no_collision(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 2 bypasses resolution when hitboxes do not intersect.
    """
    player = mock_board.player()
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    player.state.position = Position(10, 10)
    crate.state.position = Position(200, 200)

    initial_x = crate.state.position.x
    initial_y = crate.state.position.y

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == initial_x
    assert crate.state.position.y == initial_y


def test_collision_mechanics_resolve_boundary(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 1 narrow-phase environmental constraint resolution on dynamic bodies (m > 0).
    """
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    payload = mock_payload()
    boundary = mock_board.perimeters[crate.state.layer][crate.state.elevation][0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    hb = crate.hitboxes[0]
    crate.state.position = Position(
        boundary.position.x + 10 - hb.position.x,
        boundary.position.y - hb.position.y,
    )
    initial_y = crate.state.position.y
    crate.state.velocity = Velocity(0.0, 100.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.y > initial_y
    assert crate.state.velocity.vy < 0


def test_collision_mechanics_resolve_boundary_no_collision(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 1 ignores boundary constraint when entity is clear.
    """
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    payload = mock_payload()
    boundary = mock_board.perimeters[crate.state.layer][crate.state.elevation][0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    crate.state.position = Position(
        boundary.position.x,
        boundary.position.y - 2 * crate.properties.dimensions.l,
    )
    crate.state.velocity = Velocity(0.0, -100.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == boundary.position.x
    assert crate.state.position.y < boundary.position.y - crate.properties.dimensions.l
    assert crate.state.velocity.vy == -100.0


def test_collision_mechanics_resolve_boundary_static_mass_zero_ignored(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 1 environmental boundary constraints bypass static bodies (m = 0),
    preventing positional mutation and 60 Hz perimeter jittering.
    """
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    payload = mock_payload()
    boundary = mock_board.perimeters[strut.state.layer][strut.state.elevation][0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    strut.state.position = Position(
        boundary.position.x,
        int(boundary.position.y - strut.properties.dimensions.l // 2),
    )
    initial_x = strut.state.position.x
    initial_y = strut.state.position.y

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert strut.state.position.x == initial_x
    assert strut.state.position.y == initial_y


def test_collision_mechanics_resolve_boundary_kinematic_player(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 1 environmental boundary constraints enforce spatial bounds on kinematic
    players, shifting position out of the boundary hull without inverting velocity.
    """
    player = mock_board.player()
    payload = mock_payload()
    boundary = mock_board.perimeters[player.state.layer][player.state.elevation][0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    hb = player.hitboxes[0]
    player.state.position = Position(
        boundary.position.x + 10 - hb.position.x,
        boundary.position.y - hb.position.y,
    )
    initial_y = player.state.position.y
    player.state.velocity = Velocity(0.0, 10.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.position.y > initial_y
    assert player.state.velocity.vy == 10.0


def test_collision_mechanics_update_static_vs_dynamic_boundary_filtering(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies live Board Phase 1 boundary filtering excludes static architecture (m = 0)
    from constraint queries while preserving boundary displacement on dynamic bodies.
    """
    payload = mock_payload()
    player = mock_board.player()
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    player.state.position = Position(200, 200)
    sprite.state.position = Position(200, 200)

    strut.state.position = Position(100, 0)
    strut_initial_x = strut.state.position.x
    strut_initial_y = strut.state.position.y

    crate.state.position = Position(0, 50)
    crate.state.velocity = Velocity(-10.0, 0.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert strut.state.position.x == strut_initial_x
    assert strut.state.position.y == strut_initial_y
    assert crate.state.position.x > 0
    assert crate.state.velocity.vx == 10.0


def test_collision_mechanics_elevation_tier_isolation(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies dynamic entities on different elevation tiers bypass overlap resolution.
    """
    payload = mock_payload()
    player = mock_board.player()
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    player.elevation = 0
    player.state.position = Position(100, 100)

    crate.elevation = 1
    crate.state.position = Position(100, 100)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.position.x == 100
    assert player.state.position.y == 100
    assert crate.state.position.x == 100
    assert crate.state.position.y == 100


def test_collision_mechanics_boundary_elevation_isolation(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies dynamic entities with elevation >= 1 do not interact with Tier 0 perimeters.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.elevation = 1
    crate.state.position = Position(0, 50)
    crate.state.velocity = Velocity(-10.0, 0.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == 0
    assert crate.state.velocity.vx == -10.0


def test_collision_mechanics_traverse_stairs_up_ascent_and_descent(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 0 vertical stair (UP) elevation ascent (vy < 0) and descent (vy > 0).
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    player = mock_board.player()
    stairs = mock_board.instances(AssetInstances.STAIRS.value)[0]

    stairs.elevation = 0
    stairs.state.delta = 1
    stairs.state.blueprint = Directions.UP.value
    stairs.state.position = Position(500, 500)

    # Ascent: place foot inside upper 85% of stair tread with northward velocity (vy < 0)
    player.elevation = 0
    player.state.position = Position(
        stairs.state.position.x,
        stairs.state.position.y - player.dimensions.l + int(stairs.dimensions.l * 0.5),
    )
    player.state.velocity = Velocity(0.0, -20.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == 1

    # Descent: place foot in lower 15% (>= 0.85) of stair tread with southward velocity (vy > 0)
    player.state.position = Position(
        stairs.state.position.x,
        stairs.state.position.y - player.dimensions.l + int(stairs.dimensions.l * 0.9),
    )
    player.state.velocity = Velocity(0.0, 20.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == 0

def test_collision_mechanics_traverse_stairs_horizontal_left_and_right(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 0 horizontal stair (RIGHT and LEFT) elevation transitions.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    player = mock_board.player()
    stairs = mock_board.instances(AssetInstances.STAIRS.value)[0]

    stairs.elevation = 0
    stairs.state.delta = 1
    stairs.state.blueprint = Directions.RIGHT.value
    stairs.state.position = Position(500, 500)

    player_hb = player.hitboxes[0]
    right_hbs = stairs.hitboxes
    right_min_x = min(stairs.state.position.x + hb.position.x for hb in right_hbs)
    right_max_x = max(
        stairs.state.position.x + hb.position.x + hb.dimensions.w
        for hb in right_hbs
    )
    right_min_y = min(stairs.state.position.y + hb.position.y for hb in right_hbs)
    right_max_y = max(
        stairs.state.position.y + hb.position.y + hb.dimensions.l
        for hb in right_hbs
    )
    right_w = right_max_x - right_min_x
    right_l = right_max_y - right_min_y
    right_y = (
        right_min_y
        + (right_l // 2)
        - player_hb.position.y
        - (player_hb.dimensions.l // 2)
    )

    # RIGHT Ascent (vx > 0, tread_progress >= 0.15)
    player.elevation = 0
    player.state.position = Position(
        right_min_x - (player.dimensions.w // 2) + int(right_w * 0.5),
        right_y,
    )
    player.state.velocity = Velocity(20.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta

    # RIGHT Descent (vx < 0, tread_progress <= 0.15)
    player.state.position = Position(
        right_min_x - (player.dimensions.w // 2) + int(right_w * 0.1),
        right_y,
    )
    player.state.velocity = Velocity(-20.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

    # LEFT Ascent (vx < 0, tread_progress <= 0.85)
    stairs.state.blueprint = Directions.LEFT.value
    left_hbs = stairs.hitboxes
    left_min_x = min(stairs.state.position.x + hb.position.x for hb in left_hbs)
    left_max_x = max(
        stairs.state.position.x + hb.position.x + hb.dimensions.w
        for hb in left_hbs
    )
    left_min_y = min(stairs.state.position.y + hb.position.y for hb in left_hbs)
    left_max_y = max(
        stairs.state.position.y + hb.position.y + hb.dimensions.l
        for hb in left_hbs
    )
    left_w = left_max_x - left_min_x
    left_l = left_max_y - left_min_y
    left_y = (
        left_min_y
        + (left_l // 2)
        - player_hb.position.y
        - (player_hb.dimensions.l // 2)
    )
    player.state.position = Position(
        left_min_x - (player.dimensions.w // 2) + int(left_w * 0.5),
        left_y,
    )
    player.state.velocity = Velocity(-20.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta

    # LEFT Descent (vx > 0, tread_progress >= 0.85)
    player.state.position = Position(
        left_min_x - (player.dimensions.w // 2) + int(left_w * 0.9),
        left_y,
    )
    player.state.velocity = Velocity(20.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

def test_collision_mechanics_traverse_stairs_elevation_mismatch_and_falling_ignored(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 0 ignores movers whose elevation matches neither stair base nor summit
    as well as movers currently in freefall (triggers.falling == True).
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    player = mock_board.player()
    stairs = mock_board.instances(AssetInstances.STAIRS.value)[0]

    stairs.elevation = 0
    stairs.state.delta = 1
    stairs.state.blueprint = Directions.UP.value
    stairs.state.position = Position(500, 500)

    player_hb = player.hitboxes[0]
    stair_hb = stairs.hitboxes[0]
    aligned_x = (
        stairs.state.position.x
        + stair_hb.position.x
        + (stair_hb.dimensions.w // 2)
        - player_hb.position.x
        - (player_hb.dimensions.w // 2)
    )
    ascent_y = (
        stairs.state.position.y
        + stair_hb.position.y
        - player.dimensions.l
        + int(stair_hb.dimensions.l * 0.5)
    )

    # Elevation mismatch: entity at E = 2 on a 0 -> 1 stair remains at E = 2
    player.elevation = stairs.elevation + stairs.state.delta + 1
    player.state.mutators.triggers.falling = False
    player.state.position = Position(aligned_x, ascent_y)
    player.state.velocity = Velocity(0.0, -20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta + 1

    # Freefall exclusion: falling entity at E = 0 bypasses Phase 0 stair promotion
    player.elevation = stairs.elevation
    player.state.mutators.triggers.falling = True
    player.state.position = Position(aligned_x, ascent_y)
    player.state.velocity = Velocity(0.0, -20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation


def test_collision_mechanics_traverse_stairs_directional_and_threshold_gating(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 0 enforces both directional velocity sign and tread_progress
    thresholds before shifting elevation.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    player = mock_board.player()
    stairs = mock_board.instances(AssetInstances.STAIRS.value)[0]

    stairs.elevation = 0
    stairs.state.delta = 1
    stairs.state.blueprint = Directions.UP.value
    stairs.state.position = Position(500, 500)

    player_hb = player.hitboxes[0]
    stair_hb = stairs.hitboxes[0]
    aligned_x = (
        stairs.state.position.x
        + stair_hb.position.x
        + (stair_hb.dimensions.w // 2)
        - player_hb.position.x
        - (player_hb.dimensions.w // 2)
    )
    mid_y = (
        stairs.state.position.y
        + stair_hb.position.y
        - player.dimensions.l
        + int(stair_hb.dimensions.l * 0.5)
    )
    bottom_y = (
        stairs.state.position.y
        + stair_hb.position.y
        - player.dimensions.l
        + int(stair_hb.dimensions.l * 0.9)
    )

    # Moving South at E = 0 mid-tread does not ascend
    player.elevation = stairs.elevation
    player.state.position = Position(aligned_x, mid_y)
    player.state.velocity = Velocity(0.0, 20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

    # Moving North at E = 0 below the 0.85 threshold (tread_progress == 0.9) does not ascend yet
    player.state.position = Position(aligned_x, bottom_y)
    player.state.velocity = Velocity(0.0, -20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

    # Moving South at E = 1 above the 0.85 threshold (tread_progress == 0.5) does not descend yet
    player.elevation = stairs.elevation + stairs.state.delta
    player.state.position = Position(aligned_x, mid_y)
    player.state.velocity = Velocity(0.0, 20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta


def test_collision_mechanics_traverse_stairs_multi_delta(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies Phase 0 shifts elevation by stairs.state.delta for multi-tier inclines.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    player = mock_board.player()
    stairs = mock_board.instances(AssetInstances.STAIRS.value)[0]

    stairs.elevation = 0
    stairs.state.delta = 2
    stairs.state.blueprint = Directions.UP.value
    stairs.state.position = Position(500, 500)

    player_hb = player.hitboxes[0]
    stair_hb = stairs.hitboxes[0]
    aligned_x = (
        stairs.state.position.x
        + stair_hb.position.x
        + (stair_hb.dimensions.w // 2)
        - player_hb.position.x
        - (player_hb.dimensions.w // 2)
    )

    player.elevation = stairs.elevation
    player.state.position = Position(
        aligned_x,
        stairs.state.position.y + stair_hb.position.y - player.dimensions.l + int(stair_hb.dimensions.l * 0.5),
    )
    player.state.velocity = Velocity(0.0, -20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta

    player.state.position = Position(
        aligned_x,
        stairs.state.position.y + stair_hb.position.y - player.dimensions.l + int(stair_hb.dimensions.l * 0.9),
    )
    player.state.velocity = Velocity(0.0, 20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation