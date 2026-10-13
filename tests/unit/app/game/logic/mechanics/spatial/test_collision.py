"""
# Ontology: tests.unit.app.game.logic.mechanics.spatial.test_collision
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import Directions

# Cython Libraries
from libs.core.models import (
    Position,
    Dimensions,
    Velocity,
    Boundary
)


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_update(mock_collision_mechanics, mock_board, mock_bus):
    """
    Verifies the two-phase collision pipeline: Environmental Constraints (Phase 1)
    and Dynamic Entity Collisions (Phase 2) executing live on the board.
    """
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

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    # Phase 1 Assertion: Crate is displaced eastward out of boundary and velocity inverts
    assert crate.state.position.x > 0
    assert crate.state.velocity.vx == 10.0

    # Phase 2 Assertion: Overlapping dynamic bodies resolve overlap
    assert player.state.position.x != npc.state.position.x or player.state.position.y != npc.state.position.y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve(mock_collision_mechanics, mock_player, mock_crate):
    """
    Verifies Phase 2 narrow-phase AABB overlap resolution and spatial separation.
    """
    mock_player.state.position = Position(10, 10)
    mock_crate.state.position = Position(20, 20)

    initial_crate_y = mock_crate.state.position.y
    mock_collision_mechanics._resolve(mock_player, mock_crate, elevation=0)

    assert mock_crate.state.position.y != initial_crate_y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_no_collision(mock_collision_mechanics, mock_player, mock_crate):
    """
    Verifies Phase 2 bypasses resolution when hitboxes do not intersect.
    """
    mock_player.state.position = Position(10, 10)
    mock_crate.state.position = Position(200, 200)

    initial_x = mock_crate.state.position.x
    initial_y = mock_crate.state.position.y
    mock_collision_mechanics._resolve(mock_player, mock_crate, elevation=0)

    assert mock_crate.state.position.x == initial_x
    assert mock_crate.state.position.y == initial_y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary(mock_collision_mechanics, mock_crate, mock_boundary):
    """
    Verifies Phase 1 narrow-phase environmental constraint resolution on dynamic bodies (m > 0).
    """
    mock_crate.state.position = Position(10, 0)
    mock_crate.state.velocity = Velocity(0.0, -10.0)

    mock_collision_mechanics._boundary(mock_crate, mock_boundary, elevation=0)

    assert mock_crate.state.position.y > 0
    assert mock_crate.state.velocity.vy == 10.0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary_no_collision(mock_collision_mechanics, mock_crate, mock_boundary):
    """
    Verifies Phase 1 ignores boundary constraint when entity is clear.
    """
    mock_crate.state.position = Position(10, 50)
    mock_crate.state.velocity = Velocity(0.0, -10.0)

    mock_collision_mechanics._boundary(mock_crate, mock_boundary, elevation=0)

    assert mock_crate.state.position.y == 50
    assert mock_crate.state.velocity.vy == -10.0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary_static_mass_zero_ignored(mock_collision_mechanics, mock_strut, mock_boundary):
    """
    Verifies Phase 1 environmental boundary constraints bypass static bodies (m = 0),
    preventing positional mutation and 60 Hz perimeter jittering.
    """
    mock_strut.state.position = Position(10, 0)
    mock_boundary.dimensions = Dimensions(100, 10)

    initial_x = mock_strut.state.position.x
    initial_y = mock_strut.state.position.y

    mock_collision_mechanics._boundary(mock_strut, mock_boundary, elevation=0)

    assert mock_strut.state.position.x == initial_x
    assert mock_strut.state.position.y == initial_y


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_resolve_boundary_kinematic_player(mock_collision_mechanics, mock_player, mock_boundary):
    """
    Verifies Phase 1 environmental boundary constraints enforce spatial bounds on kinematic
    players despite m = 0, shifting position out of the boundary hull.
    """
    # Bounding box of 50px accounts for LPC feet hitbox offset (y ~ 23..44)
    mock_player.state.position = Position(10, 0)
    mock_player.state.velocity = Velocity(0.0, -10.0)
    mock_boundary.dimensions = Dimensions(100, 50)

    mock_collision_mechanics._boundary(mock_player, mock_boundary, elevation=0)

    assert mock_player.state.position.y > 0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_update_static_vs_dynamic_boundary_filtering(mock_collision_mechanics, mock_board, mock_bus):
    """
    Verifies live Board Phase 1 boundary filtering excludes static architecture (m = 0)
    from constraint queries while preserving boundary displacement on dynamic bodies.
    """
    payload = mock_board.device.poll() if mock_board.device else None

    player = mock_board.player()
    if player:
        player.state.position = Position(200, 200)
    npc = mock_board.asset("npc")
    if npc:
        npc.state.position = Position(200, 200)

    strut = mock_board.asset("castle")
    strut.state.position = Position(100, 0)
    strut_initial_x = strut.state.position.x
    strut_initial_y = strut.state.position.y

    crate = mock_board.asset("box")
    crate.state.position = Position(0, 50)
    crate.state.velocity = Velocity(-10.0, 0.0)

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert strut.state.position.x == strut_initial_x
    assert strut.state.position.y == strut_initial_y
    assert crate.state.position.x > 0
    assert crate.state.velocity.vx == 10.0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_elevation_tier_isolation(mock_collision_mechanics, mock_board, mock_bus):
    """
    Verifies dynamic entities on different elevation tiers bypass overlap resolution.
    """
    payload = mock_board.device.poll() if mock_board.device else None

    player = mock_board.player()
    crate = mock_board.asset("box")

    player.elevation = 0
    player.state.position = Position(100, 100)

    crate.elevation = 1
    crate.state.position = Position(100, 100)

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.position.x == 100
    assert player.state.position.y == 100
    assert crate.state.position.x == 100
    assert crate.state.position.y == 100


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_boundary_elevation_isolation(mock_collision_mechanics, mock_board, mock_bus):
    """
    Verifies dynamic entities with elevation >= 1 do not interact with Tier 0 perimeters.
    """
    payload = mock_board.device.poll() if mock_board.device else None

    crate = mock_board.asset("box")
    crate.elevation = 1
    crate.state.position = Position(0, 50)
    crate.state.velocity = Velocity(-10.0, 0.0)

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    assert crate.state.position.x == 0
    assert crate.state.velocity.vx == -10.0


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_platform_tier_0_facade_obstruction(mock_collision_mechanics, mock_board, mock_platform, mock_bus):
    """
    Subtask 6.1: Asserts an entity at E = 0 is obstructed by a platform's tier 0 facade.
    """
    payload = mock_board.device.poll() if mock_board.device else None
    if not mock_board.asset(mock_platform.name):
        mock_board.add([mock_platform])

    # Platform at (100, 100); tier 0 facade hitbox at offset (0, 64) with size (96, 32) -> world y: [164, 196]
    mock_platform.elevation = 0
    mock_platform.state.position = Position(100, 100)

    # Crate at E = 0 overlapping the tier 0 facade at (120, 170)
    crate = mock_board.asset("box")
    crate.elevation = 0
    crate.state.position = Position(120, 170)
    crate.state.velocity = Velocity(0.0, -10.0)

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    # Crate is pushed out of the platform's tier 0 facade while platform remains immobile (m = 0)
    assert crate.state.position.y > 170
    assert mock_platform.state.position.x == 100
    assert mock_platform.state.position.y == 100


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_platform_tier_1_deck_traversal(mock_collision_mechanics, mock_board, mock_platform, mock_bus):
    """
    Subtask 6.2: Asserts an entity at E = 1 traverses the platform deck unhindered by the tier 0 facade.
    """
    payload = mock_board.device.poll() if mock_board.device else None
    if not mock_board.asset(mock_platform.name):
        mock_board.add([mock_platform])

    # Platform at (100, 100): tier 0 facade is y=[164, 196], tier 1 top railing is y=[100, 116]
    mock_platform.elevation = 0
    mock_platform.state.position = Position(100, 100)

    # Crate at E = 1 positioned directly over the tier 0 facade coordinates (120, 160)
    crate = mock_board.asset("box")
    crate.elevation = 1
    crate.state.position = Position(120, 160)
    crate.state.velocity = Velocity(0.0, 0.0)

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    # Unhindered by the tier 0 facade below
    assert crate.state.position.x == 120
    assert crate.state.position.y == 160


@pytest.mark.physics
@pytest.mark.collisions
def test_collision_mechanics_stair_ascent_to_platform_deck_containment(
    mock_collision_mechanics,
    mock_board,
    mock_platform,
    mock_perimeter,
    mock_bus
):
    """
    Subtask 6.3: Verifies stair ascent from E = 0 to E = 1 transitions an entity from
    tier 0 facade obstruction to tier 1 deck containment within the collision pipeline.
    """
    payload = mock_board.device.poll() if mock_board.device else None
    if not mock_board.asset(mock_platform.name):
        mock_board.add([mock_platform])

    # Place platform at (100, 100) [w=96, l=96] and synthesize tier 1 deck perimeter
    mock_platform.elevation = 0
    mock_platform.state.position = Position(100, 100)
    mock_board.perimeters["0"] = mock_perimeter.generate(mock_board, "0")

    # Configure stairs ascending UP from E = 0 to E = 1 at (120, 160)
    stairs = mock_board.asset("stairs-main")
    stairs.elevation = 0
    stairs.state.delta = 1
    stairs.state.direction = Directions.UP.value
    stairs.state.position = Position(120, 160)

    # Position player at top of stair tread (foot_y = pos.y + 64 <= 160 + 0.2 * stair_l) moving North (vy < 0)
    player = mock_board.player()
    player.elevation = 0
    player.state.position = Position(112, 100)
    player.state.velocity = Velocity(0.0, -20.0)

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    # Phase 0 transitions player to elevation = 1
    assert player.elevation == 1

    # Move player across the northern edge of the E = 1 platform deck (y = 100)
    player.state.position = Position(112, 70)
    player.state.velocity = Velocity(0.0, -20.0)

    mock_collision_mechanics.update(mock_board, 0.016, mock_bus, payload)

    # Phase 1 enforces E = 1 platform deck perimeter containment
    assert player.state.position.y > 70