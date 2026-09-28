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
def test_collision_mechanics_resolve_no_collision(mock_player, mock_crate):
    """
    Verifies Phase 2 bypasses resolution when hitboxes do not intersect.
    """
    mechanic = CollisionMechanics()

    mock_player.state.position = Position(10, 10)
    mock_crate.state.position = Position(200, 200)

    initial_x = mock_crate.state.position.x
    initial_y = mock_crate.state.position.y
    mechanic._resolve(mock_player, mock_crate)

    assert mock_crate.state.position.x == initial_x
    assert mock_crate.state.position.y == initial_y


@pytest.mark.physics
def test_collision_mechanics_resolve_boundary(mock_crate):
    """
    Verifies Phase 1 narrow-phase environmental constraint resolution.
    """
    mechanic = CollisionMechanics()

    mock_crate.state.position = Position(10, 0)
    mock_crate.state.velocity = Velocity(0.0, -10.0)
    boundary = Boundary(Position(0, 0), Dimensions(100, 1))

    mechanic._boundary(mock_crate, boundary)

    assert mock_crate.state.position.y > 0
    assert mock_crate.state.velocity.vy == 10.0


@pytest.mark.physics
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