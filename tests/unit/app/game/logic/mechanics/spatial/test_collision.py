"""
# Ontology: tests.unit.app.game.logic.mechanics.spatial.test_collision
"""
# Standard Libraries
import collections

# External Libraries
import pytest

# Application Libraries
from app.game.logic.mechanics import CollisionMechanics

# Cython Libraries
from libs.core.models import (
    Position,
    Dimensions,
    Velocity,
    Boundary
)


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_update(mock_board):
    """
    Verifies the two-phase collision pipeline: Environmental Constraints (Phase 1)
    and Dynamic Entity Collisions (Phase 2) executing live on the board.
    """
    mechanic = CollisionMechanics()
    bus = collections.deque()
    payload = mock_board.device.poll() if mock_board.device else None

    # Setup Phase 1: Position crate intersecting the western perimeter with incoming velocity
    crate = mock_board.asset("box")
    crate.state.position = Position(0, 50)
    crate.state.velocity = Velocity(-10.0, 0.0)

    # Setup Phase 2: Position player and NPC overlapping in open space
    player = mock_board.player()
    npc = mock_board.asset("npc")
    player.state.position = Position(100, 100)
    npc.state.position = Position(100, 100)

    mechanic.update(mock_board, 0.016, bus, payload)

    # Phase 1 Assertion: Crate is displaced eastward out of boundary and velocity inverts
    assert crate.state.position.x > 0
    assert crate.state.velocity.vx == 10.0

    # Phase 2 Assertion: Overlapping dynamic bodies resolve overlap
    assert player.state.position.x != npc.state.position.x or player.state.position.y != npc.state.position.y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve(mock_player, mock_crate):
    """
    Verifies Phase 2 narrow-phase AABB overlap resolution and spatial separation.
    """
    mechanic = CollisionMechanics()

    mock_player.state.position = Position(10, 10)
    mock_crate.state.position = Position(20, 20)

    initial_crate_y = mock_crate.state.position.y
    mechanic._resolve(mock_player, mock_crate)

    assert mock_crate.state.position.y != initial_crate_y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_no_collision(mock_player, mock_crate):
    """
    Verifies Phase 2 bypasses resolution when hitboxes do not intersect.
    """
    mechanic = CollisionMechanics()

    mock_player.state.position = Position(10, 10)
    mock_crate.state.position = Position(20, 20)

    initial_x = mock_crate.state.position.x
    initial_y = mock_crate.state.position.y
    mechanic._resolve(mock_player, mock_crate)

    assert mock_crate.state.position.x == initial_x
    assert mock_crate.state.position.y == initial_y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary(mock_crate):
    """
    Verifies Phase 1 narrow-phase environmental constraint resolution on dynamic bodies (m > 0).
    """
    mechanic = CollisionMechanics()

    mock_crate.state.position = Position(10, 0)
    mock_crate.state.velocity = Velocity(0.0, -10.0)
    boundary = Boundary(Position(0, 0), Dimensions(100, 1))

    mechanic._boundary(mock_crate, boundary)

    assert mock_crate.state.position.y > 0
    assert mock_crate.state.velocity.vy == 10.0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary_no_collision(mock_crate):
    """
    Verifies Phase 1 ignores boundary constraint when entity is clear.
    """
    mechanic = CollisionMechanics()

    mock_crate.state.position = Position(10, 50)
    mock_crate.state.velocity = Velocity(0.0, -10.0)
    boundary = Boundary(Position(0, 0), Dimensions(100, 1))

    mechanic._boundary(mock_crate, boundary)

    assert mock_crate.state.position.y == 50
    assert mock_crate.state.velocity.vy == -10.0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary_static_mass_zero_ignored(mock_strut):
    """
    Verifies Phase 1 environmental boundary constraints bypass static bodies (m = 0),
    preventing positional mutation and 60 Hz perimeter jittering.
    """
    mechanic = CollisionMechanics()

    # Position static strut (m = 0) intersecting the environmental boundary
    mock_strut.state.position = Position(10, 0)
    boundary = Boundary(Position(0, 0), Dimensions(100, 10))

    initial_x = mock_strut.state.position.x
    initial_y = mock_strut.state.position.y

    mechanic._boundary(mock_strut, boundary)

    assert mock_strut.state.position.x == initial_x
    assert mock_strut.state.position.y == initial_y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary_kinematic_player(mock_player):
    """
    Verifies Phase 1 environmental boundary constraints enforce spatial bounds on kinematic
    players despite m = 0, shifting position out of the boundary hull.
    """
    mechanic = CollisionMechanics()

    mock_player.state.position = Position(10, 0)
    mock_player.state.velocity = Velocity(0.0, -10.0)
    boundary = Boundary(Position(0, 0), Dimensions(100, 10))

    mechanic._boundary(mock_player, boundary)

    assert mock_player.state.position.y > 0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_update_static_vs_dynamic_boundary_filtering(mock_board):
    """
    Verifies live Board Phase 1 boundary filtering excludes static architecture (m = 0)
    from constraint queries while preserving boundary displacement on dynamic bodies.
    """
    mechanic = CollisionMechanics()
    bus = collections.deque()
    payload = mock_board.device.poll() if mock_board.device else None

    # Static strut (m = 0) placed intersecting western perimeter boundary (x = 0)
    strut = mock_board.asset("castle")
    strut.state.position = Position(0, 50)
    strut_initial_x = strut.state.position.x
    strut_initial_y = strut.state.position.y

    # Dynamic crate (m = 5) placed intersecting western perimeter boundary with incoming velocity
    crate = mock_board.asset("box")
    crate.state.position = Position(0, 100)
    crate.state.velocity = Velocity(-10.0, 0.0)

    mechanic.update(mock_board, 0.016, bus, payload)

    # Static architecture must remain completely immutable
    assert strut.state.position.x == strut_initial_x
    assert strut.state.position.y == strut_initial_y

    # Dynamic body must be displaced out of the boundary with inverted velocity
    assert crate.state.position.x > 0
    assert crate.state.velocity.vx == 10.0