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
    Mechanics
)

# Cython Libraries
from libs.core.models import (
    Position,
    Dimensions,
    Velocity
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.physics_motion,
    pytest.mark.workflow_collisions
]

# ---------------------------------------------------------------------------


def test_collision_mechanics_update(
    mock_mechanic, 
    mock_board, 
    mock_bus, 
    mock_payload
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
    assert player.state.position.x != sprite.state.position.x or player.state.position.y != sprite.state.position.y


def test_collision_mechanics_resolve(
    mock_mechanic, 
    mock_board, 
    mock_bus, 
    mock_payload
):
    """
    Verifies Phase 2 narrow-phase AABB overlap resolution and spatial separation.
    """
    # Setup Phase 0: Fixtures
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
    mock_payload
):
    """
    Verifies Phase 2 bypasses resolution when hitboxes do not intersect.
    """
    # Setup Phase 0: Fixtures
    player = mock_board.player()
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    player.state.position = Position(10, 10)
    crate.state.position = Position(200, 200)

    initial_x = crate.state.position.x
    initial_y = crate.state.position.y

    mechanics._resolve(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == initial_x
    assert crate.state.position.y == initial_y


def test_collision_mechanics_resolve_boundary(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload
):
    """
    Verifies Phase 1 narrow-phase environmental constraint resolution on dynamic bodies (m > 0).
    """
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    payload = mock_payload()
    boundary = mock_board.perimeters[crate.state.layer][crate.state.elevation][0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    crate.state.position = Position(
        boundary.position.x,
        boundary.position.y - 2 * crate.properties.dimensions.l
    )
    crate.state.velocity = Velocity(0.0, 100.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.velocity.vy < 0 


def test_collision_mechanics_resolve_boundary_no_collision(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload
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
        boundary.position.y - crate.properties.dimensions.l
    )
    crate.state.velocity = Velocity(0.0, -100.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == 0
    assert crate.state.position.y == boundary.position.y - crate.properties.dimensions.l - 100*0.016
    assert crate.state.velocity.vy == -100.0


def test_collision_mechanics_resolve_boundary_static_mass_zero_ignored(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload
):
    """
    Verifies Phase 1 environmental boundary constraints bypass static bodies (m = 0),
    preventing positional mutation and 60 Hz perimeter jittering.
    """
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    payload = mock_payload()
    boundary = mock_board.perimeters[strut.state.layer][strut.state.elevation][0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    strut.state.position = Position(10, 0)
    strut.state.position = Position(
        boundary.position.x,
        boundary.position.y - strut.properties.dimensions.l / 2 
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
    mock_payload
):
    """
    Verifies Phase 1 environmental boundary constraints enforce spatial bounds on kinematic
    players despite m = 0, shifting position out of the boundary hull.
    """
    player = mock_board.player()
    payload = mock_payload()
    boundary = mock_board.perimeters[player.state.layer][player.state.elevation][0]
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    player.state.position = Position(
        boundary.position.x,
        boundary.position.y - player.properties.dimensions.l
    )
    player.state.velocity = Velocity(0.0, 10.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.velocity.vy < 0


def test_collision_mechanics_update_static_vs_dynamic_boundary_filtering(
    mock_mechanic, 
    mock_board, 
    mock_bus,
    mock_payload
):
    """
    Verifies live Board Phase 1 boundary filtering excludes static architecture (m = 0)
    from constraint queries while preserving boundary displacement on dynamic bodies.
    """
    payload = mock_payload()
    player = mock_board.player()
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    strut = mock_board.instance(AssetInstances.STRUTS.value)[0]
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
    mock_payload
):
    """
    Verifies dynamic entities on different elevation tiers bypass overlap resolution.
    """
    payload = mock_payload()
    player = mock_board.player()
    crate = mock_board.instances(AssetInstances.CRATES.values)[0]
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
    mock_payload
):
    """
    Verifies dynamic entities with elevation >= 1 do not interact with Tier 0 perimeters.
    """
    payload = mock_payload()
    mechanics = mock_mechanic(Mechanics.COLLISION.value)

    crate = mock_board.instances(AssetInstances.CRATES.values)[0]
    crate.elevation = 1
    crate.state.position = Position(0, 50)
    crate.state.velocity = Velocity(-10.0, 0.0)

    mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == 0
    assert crate.state.velocity.vx == -10.0