"""
@domain.test
@test.unit
@app.mechanic
@physics.motion
@workflow.collisions

# Ontology: Tests - tests.unit.app.game.logic.mechanics.spatial.test_collision

Unit tests for CollisionMechanics.
"""
# Standard Libraries
import math

# External Libraries
import pytest

# Application Libraries
# Application Libraries
from app.game.board import Board
from app.game.logic.mechanics.spatial.collision import (
    STAIR_ASCENT_HIGH,
    STAIR_ASCENT_LOW,
    STAIR_DESCENT_HIGH,
    STAIR_DESCENT_LOW,
)
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
    Mechanics,
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import (
    Dimensions,
    Hitbox,
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

    player_hbs = player.hitboxes
    hb_center_x = (
        min(hb.position.x for hb in player_hbs)
        + max(hb.position.x + hb.dimensions.w for hb in player_hbs)
    ) // 2
    hb_bottom_y = max(hb.position.y + hb.dimensions.l for hb in player_hbs)

    stair_hbs = stairs.hitboxes
    min_x = min(stairs.state.position.x + hb.position.x for hb in stair_hbs)
    max_x = max(
        stairs.state.position.x + hb.position.x + hb.dimensions.w
        for hb in stair_hbs
    )
    min_y = min(stairs.state.position.y + hb.position.y for hb in stair_hbs)
    max_y = max(
        stairs.state.position.y + hb.position.y + hb.dimensions.l
        for hb in stair_hbs
    )
    stair_w = max_x - min_x
    stair_l = max_y - min_y
    aligned_x = min_x + (stair_w // 2) - hb_center_x

    # Ascent: place hitbox foot inside upper tread (<= STAIR_ASCENT_HIGH) with vy < 0
    player.elevation = stairs.elevation
    player.state.position = Position(
        aligned_x,
        min_y - hb_bottom_y + int(stair_l * 0.5),
    )
    player.state.velocity = Velocity(0.0, -20.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta

    # Descent: place hitbox foot at/below STAIR_DESCENT_HIGH with vy > 0
    player.state.position = Position(
        aligned_x,
        min_y - hb_bottom_y + math.ceil(stair_l * STAIR_DESCENT_HIGH),
    )
    player.state.velocity = Velocity(0.0, 20.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation


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

    player_hbs = player.hitboxes
    player_hb = player_hbs[0]
    hb_center_x = (
        min(hb.position.x for hb in player_hbs)
        + max(hb.position.x + hb.dimensions.w for hb in player_hbs)
    ) // 2

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

    # RIGHT Ascent (vx > 0, tread_progress >= STAIR_ASCENT_LOW)
    player.elevation = stairs.elevation
    player.state.position = Position(
        right_min_x - hb_center_x + int(right_w * 0.5),
        right_y,
    )
    player.state.velocity = Velocity(20.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta

    # RIGHT Descent (vx < 0, tread_progress <= STAIR_DESCENT_LOW)
    player.state.position = Position(
        right_min_x - hb_center_x + int(right_w * STAIR_DESCENT_LOW),
        right_y,
    )
    player.state.velocity = Velocity(-20.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

    # LEFT Ascent (vx < 0, tread_progress <= STAIR_ASCENT_HIGH)
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
        left_min_x - hb_center_x + int(left_w * 0.5),
        left_y,
    )
    player.state.velocity = Velocity(-20.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta

    # LEFT Descent (vx > 0, tread_progress >= STAIR_DESCENT_HIGH)
    player.state.position = Position(
        left_min_x - hb_center_x + math.ceil(left_w * STAIR_DESCENT_HIGH),
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

    player_hbs = player.hitboxes
    hb_center_x = (
        min(hb.position.x for hb in player_hbs)
        + max(hb.position.x + hb.dimensions.w for hb in player_hbs)
    ) // 2
    hb_bottom_y = max(hb.position.y + hb.dimensions.l for hb in player_hbs)

    stair_hbs = stairs.hitboxes
    min_x = min(stairs.state.position.x + hb.position.x for hb in stair_hbs)
    max_x = max(
        stairs.state.position.x + hb.position.x + hb.dimensions.w
        for hb in stair_hbs
    )
    min_y = min(stairs.state.position.y + hb.position.y for hb in stair_hbs)
    max_y = max(
        stairs.state.position.y + hb.position.y + hb.dimensions.l
        for hb in stair_hbs
    )
    aligned_x = min_x + ((max_x - min_x) // 2) - hb_center_x
    ascent_y = min_y - hb_bottom_y + int((max_y - min_y) * 0.5)

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

    player_hbs = player.hitboxes
    hb_center_x = (
        min(hb.position.x for hb in player_hbs)
        + max(hb.position.x + hb.dimensions.w for hb in player_hbs)
    ) // 2
    hb_bottom_y = max(hb.position.y + hb.dimensions.l for hb in player_hbs)

    stair_hbs = stairs.hitboxes
    min_x = min(stairs.state.position.x + hb.position.x for hb in stair_hbs)
    max_x = max(
        stairs.state.position.x + hb.position.x + hb.dimensions.w
        for hb in stair_hbs
    )
    min_y = min(stairs.state.position.y + hb.position.y for hb in stair_hbs)
    max_y = max(
        stairs.state.position.y + hb.position.y + hb.dimensions.l
        for hb in stair_hbs
    )
    stair_l = max_y - min_y
    aligned_x = min_x + ((max_x - min_x) // 2) - hb_center_x
    mid_y = min_y - hb_bottom_y + int(stair_l * 0.5)
    bottom_y = min_y - hb_bottom_y + math.ceil(stair_l * STAIR_DESCENT_HIGH)

    # Moving South at E = 0 mid-tread does not ascend
    player.elevation = stairs.elevation
    player.state.position = Position(aligned_x, mid_y)
    player.state.velocity = Velocity(0.0, 20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

    # Moving North at E = 0 below STAIR_ASCENT_HIGH (>= STAIR_DESCENT_HIGH) does not ascend yet
    player.state.position = Position(aligned_x, bottom_y)
    player.state.velocity = Velocity(0.0, -20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

    # Moving South at E = 1 above STAIR_DESCENT_HIGH (mid-tread) does not descend yet
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

    player_hbs = player.hitboxes
    hb_center_x = (
        min(hb.position.x for hb in player_hbs)
        + max(hb.position.x + hb.dimensions.w for hb in player_hbs)
    ) // 2
    hb_bottom_y = max(hb.position.y + hb.dimensions.l for hb in player_hbs)

    stair_hbs = stairs.hitboxes
    min_x = min(stairs.state.position.x + hb.position.x for hb in stair_hbs)
    max_x = max(
        stairs.state.position.x + hb.position.x + hb.dimensions.w
        for hb in stair_hbs
    )
    min_y = min(stairs.state.position.y + hb.position.y for hb in stair_hbs)
    max_y = max(
        stairs.state.position.y + hb.position.y + hb.dimensions.l
        for hb in stair_hbs
    )
    stair_l = max_y - min_y
    aligned_x = min_x + ((max_x - min_x) // 2) - hb_center_x

    player.elevation = stairs.elevation
    player.state.position = Position(
        aligned_x,
        min_y - hb_bottom_y + int(stair_l * 0.5),
    )
    player.state.velocity = Velocity(0.0, -20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta

    player.state.position = Position(
        aligned_x,
        min_y - hb_bottom_y + math.ceil(stair_l * STAIR_DESCENT_HIGH),
    )
    player.state.velocity = Velocity(0.0, 20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation


def test_collision_mechanics_stair_hysteresis_deadband(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies the (STAIR_ASCENT_HIGH, STAIR_DESCENT_HIGH) deadband prevents
    oscillation when reversing direction near the base of an UP stair.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    player = mock_board.player()
    stairs = mock_board.instances(AssetInstances.STAIRS.value)[0]

    stairs.elevation = 0
    stairs.state.delta = 1
    stairs.state.blueprint = Directions.UP.value
    stairs.state.position = Position(500, 500)

    player_hbs = player.hitboxes
    hb_center_x = (
        min(hb.position.x for hb in player_hbs)
        + max(hb.position.x + hb.dimensions.w for hb in player_hbs)
    ) // 2
    hb_bottom_y = max(hb.position.y + hb.dimensions.l for hb in player_hbs)

    stair_hbs = stairs.hitboxes
    min_x = min(stairs.state.position.x + hb.position.x for hb in stair_hbs)
    max_x = max(
        stairs.state.position.x + hb.position.x + hb.dimensions.w
        for hb in stair_hbs
    )
    min_y = min(stairs.state.position.y + hb.position.y for hb in stair_hbs)
    max_y = max(
        stairs.state.position.y + hb.position.y + hb.dimensions.l
        for hb in stair_hbs
    )
    stair_l = max_y - min_y
    aligned_x = min_x + ((max_x - min_x) // 2) - hb_center_x
    deadband_offset = round(stair_l * ((STAIR_ASCENT_HIGH + STAIR_DESCENT_HIGH) / 2.0))
    deadband_y = min_y - hb_bottom_y + deadband_offset

    # At E = 0 inside deadband moving North -> does not prematurely ascend
    player.elevation = stairs.elevation
    player.state.position = Position(aligned_x, deadband_y)
    player.state.velocity = Velocity(0.0, -20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation

    # At E = 1 inside deadband moving South -> does not prematurely descend
    player.elevation = stairs.elevation + stairs.state.delta
    player.state.position = Position(aligned_x, deadband_y)
    player.state.velocity = Velocity(0.0, 20.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == stairs.elevation + stairs.state.delta


# ---------------------------------------------------------------------------
# PHASE 03.07: COMPOUND MULTI-HITBOX, STATIC CACHING & INACTIVE-TIER SKIPPING
# ---------------------------------------------------------------------------


def test_collision_mechanics_compound_multi_hitbox_l_corner_resolution(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
    mock_asset,
):
    """
    Verifies Bug B053.2: a dynamic body simultaneously overlapping both orthogonal
    arms of a compound multi-hitbox static obstacle resolves clear of both hitboxes
    in a single tick.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    layer = crate.state.layer
    c_hb = crate.hitboxes[0]

    bar_t = max(20, c_hb.dimensions.w, c_hb.dimensions.l)
    bar_span = bar_t * 4
    pen = min(5, max(1, min(c_hb.dimensions.w, c_hb.dimensions.l) // 4))

    wall = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CHESTS.value)
    wall.taxonomy.name = "compound-l-wall"
    wall.state.name = "compound-l-wall"
    wall.state.layer = layer
    wall.elevation = 0
    wall.state.position = Position(5000, 5000)
    wall.properties.mass = 0
    wall.properties.hitboxes = [
        Hitbox(Position(0, 0), Dimensions(bar_span, bar_t)),
        Hitbox(Position(0, 0), Dimensions(bar_t, bar_span)),
    ]
    mock_board.add([wall])

    crate.elevation = 0
    crate.state.mutators.triggers.falling = False
    crate.state.position = Position(
        5000 + bar_t - pen - c_hb.position.x,
        5000 + bar_t - pen - c_hb.position.y,
    )
    crate.state.velocity = Velocity(-10.0, -10.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert not geometry.intersects(
        crate.state.position,
        crate.hitboxes,
        wall.state.position,
        wall.hitboxes,
    )
    assert crate.state.position.x + c_hb.position.x == 5000 + bar_t
    assert crate.state.position.y + c_hb.position.y == 5000 + bar_t
    assert wall.state.position.x == 5000
    assert wall.state.position.y == 5000


def test_collision_mechanics_compound_multi_hitbox_seam_no_ghost_nudge(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
    mock_asset,
):
    """
    Verifies deepest-overlap-first sorting resolves a dynamic body straddling the
    shared seam of two adjacent collinear static hitboxes strictly along the surface
    normal with zero lateral ghost displacement.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    layer = crate.state.layer
    c_hb = crate.hitboxes[0]

    seg_w = max(40, c_hb.dimensions.w * 2)
    seg_l = max(20, c_hb.dimensions.l)
    pen = max(4, min(6, c_hb.dimensions.w // 3))
    minor_x = max(1, pen // 2)

    wall = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CHESTS.value)
    wall.taxonomy.name = "compound-seam-wall"
    wall.state.name = "compound-seam-wall"
    wall.state.layer = layer
    wall.elevation = 0
    wall.state.position = Position(5000, 5000)
    wall.properties.mass = 0
    # Place smaller-overlap segment FIRST to confirm area sorting takes precedence over list order
    wall.properties.hitboxes = [
        Hitbox(Position(seg_w, 0), Dimensions(seg_w, seg_l)),
        Hitbox(Position(0, 0), Dimensions(seg_w, seg_l)),
    ]
    mock_board.add([wall])

    initial_x = 5000 + seg_w - c_hb.dimensions.w + minor_x - c_hb.position.x
    initial_y = 5000 + seg_l - pen - c_hb.position.y
    crate.elevation = 0
    crate.state.mutators.triggers.falling = False
    crate.state.position = Position(initial_x, initial_y)
    crate.state.velocity = Velocity(0.0, -20.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == initial_x
    assert crate.state.position.y == initial_y + pen
    assert not geometry.intersects(
        crate.state.position,
        crate.hitboxes,
        wall.state.position,
        wall.hitboxes,
    )


def test_collision_mechanics_static_cache_invalidation_on_gate_toggle(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies persistent static Space caches rebuild cleanly after Gate toggle +
    board.invalidate_statics(layer): closed blocks, open passes, re-closed blocks.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    layer = crate.state.layer

    if gate.state.layer != layer:
        mock_board.relayer(gate, layer)

    gate.elevation = 0
    gate.state.position = Position(5000, 5000)
    gate.state.switch = False
    mock_board.invalidate_statics(layer)

    g_hb = gate.hitboxes[0]
    c_hb = crate.hitboxes[0]
    overlap_x = (
        gate.state.position.x
        + g_hb.position.x
        + (g_hb.dimensions.w // 2)
        - c_hb.position.x
    )
    overlap_y = (
        gate.state.position.y
        + g_hb.position.y
        + (g_hb.dimensions.l // 2)
        - c_hb.position.y
    )

    # 1. Closed gate blocks dynamic body
    crate.elevation = 0
    crate.state.mutators.triggers.falling = False
    crate.state.position = Position(overlap_x, overlap_y)
    crate.state.velocity = Velocity(0.0, 0.0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert not geometry.intersects(
        crate.state.position,
        crate.hitboxes,
        gate.state.position,
        gate.hitboxes,
    )

    # 2. Opening gate + invalidating statics allows free passage
    gate.state.switch = True
    mock_board.invalidate_statics(layer)
    crate.state.position = Position(overlap_x, overlap_y)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert crate.state.position.x == overlap_x
    assert crate.state.position.y == overlap_y

    # 3. Re-closing gate + invalidating statics restores solid blocking
    gate.state.switch = False
    mock_board.invalidate_statics(layer)
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert crate.state.position.x != overlap_x or crate.state.position.y != overlap_y


def test_collision_mechanics_skips_inactive_layer_and_static_vs_static(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
    mock_asset,
):
    """
    Verifies Bug B053.1: layers with zero active non-falling dynamic bodies are
    skipped and overlapping static-vs-static bodies never displace one another.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    isolated_layer = "inactive-collision-layer"

    wall_a = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    wall_b = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    wall_a.taxonomy.name = "static-a"
    wall_a.state.name = "static-a"
    wall_a.state.layer = isolated_layer
    wall_a.state.switch = False
    wall_a.elevation = 0
    wall_a.state.position = Position(5000, 5000)

    wall_b.taxonomy.name = "static-b"
    wall_b.state.name = "static-b"
    wall_b.state.layer = isolated_layer
    wall_b.state.switch = False
    wall_b.elevation = 0
    wall_b.state.position = Position(5004, 5004)
    mock_board.add([wall_a, wall_b])

    # Static-only layer: zero displacement
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert wall_a.state.position.x == 5000 and wall_a.state.position.y == 5000
    assert wall_b.state.position.x == 5004 and wall_b.state.position.y == 5004

    # Layer with only a falling dynamic body: still skipped
    crate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    crate.taxonomy.name = "falling-crate"
    crate.state.name = "falling-crate"
    crate.state.layer = isolated_layer
    crate.elevation = 0
    g_hb = wall_a.hitboxes[0]
    c_hb = crate.hitboxes[0]
    overlap_x = (
        wall_a.state.position.x
        + g_hb.position.x
        + (g_hb.dimensions.w // 2)
        - c_hb.position.x
    )
    overlap_y = (
        wall_a.state.position.y
        + g_hb.position.y
        + (g_hb.dimensions.l // 2)
        - c_hb.position.y
    )
    crate.state.position = Position(overlap_x, overlap_y)
    crate.state.mutators.triggers.falling = True
    mock_board.add([crate])

    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert crate.state.position.x == overlap_x and crate.state.position.y == overlap_y

    # Clearing falling flag activates tier: dynamic crate separates, statics stay fixed
    crate.state.mutators.triggers.falling = False
    mechanics.update(mock_board, 0.016, mock_bus, payload)
    assert crate.state.position.x != overlap_x or crate.state.position.y != overlap_y
    assert wall_a.state.position.x == 5000 and wall_a.state.position.y == 5000
    assert wall_b.state.position.x == 5004 and wall_b.state.position.y == 5004


def test_collision_mechanics_board_switch_clears_static_cache(
    mock_mechanic,
    mock_board,
    mock_configurations_schema,
    mock_equipment,
    mock_asset,
    mock_bus,
    mock_payload,
):
    """
    Verifies switching Board instances invalidates CollisionMechanics static caches
    so static obstacles from the first Board cannot collide on the second Board.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    layer = mock_board.player().state.layer

    wall = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    wall.taxonomy.name = "board-a-wall"
    wall.state.name = "board-a-wall"
    wall.state.layer = layer
    wall.state.switch = False
    wall.elevation = 0
    wall.state.position = Position(5000, 5000)
    mock_board.add([wall])

    # Warm CollisionMechanics static cache on mock_board (contains wall at tier 0)
    mechanics.update(mock_board, 0.016, mock_bus, payload)

    # Create a second Board with NO obstacle at the exact hitbox-overlapping coordinate
    crate_b = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    crate_b.taxonomy.name = "board-b-crate"
    crate_b.state.name = "board-b-crate"
    crate_b.state.layer = layer
    crate_b.elevation = 0
    g_hb = wall.hitboxes[0]
    c_hb = crate_b.hitboxes[0]
    overlap_x = (
        wall.state.position.x
        + g_hb.position.x
        + (g_hb.dimensions.w // 2)
        - c_hb.position.x
    )
    overlap_y = (
        wall.state.position.y
        + g_hb.position.y
        + (g_hb.dimensions.l // 2)
        - c_hb.position.y
    )
    crate_b.state.position = Position(overlap_x, overlap_y)
    crate_b.state.mutators.triggers.falling = False

    board_b = Board(
        assets=[crate_b],
        configurations=mock_configurations_schema,
        equipment=mock_equipment,
    )

    mechanics.update(board_b, 0.016, mock_bus, payload)

    assert crate_b.state.position.x == overlap_x
    assert crate_b.state.position.y == overlap_y