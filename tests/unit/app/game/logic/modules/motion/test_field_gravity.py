"""
@domain.test
@test.unit
@app.mechanic
@physics.motion
@physics.fields
@workflow.gravity
@workflow.collisions

# Ontology: Tests - tests.unit.app.game.logic.test_gravity

Unit tests for Phase 07.03 trigonometric gravity, multi-tier step-down, and stair tread support.
"""
# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.static.semantics import (
    AssetInstances,
    Buildings,
    Mechanics,
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
    pytest.mark.workflow_gravity,
    pytest.mark.workflow_collisions,
]

# ---------------------------------------------------------------------------


def test_gravity_single_tier_freefall_drop_distance(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies an unsupported entity at E = 1 enters freefall and descends exactly
    TIER_DROP_DISTANCE (int(32 * tan(60 deg)) = 55 px) before landing at E = 0.
    """
    payload = mock_payload()
    motion = mock_mechanic(Mechanics.MOTION.value)
    player = mock_board.player()

    initial_y = 100
    player.elevation = 1
    player.state.position = Position(100, initial_y)
    player.state.velocity = Velocity(0.0, 0.0)
    player.state.mutators.triggers.falling = False
    player.state.mutators.parameters.descension = 0.0

    # Tick 1 triggers freefall
    motion.update(mock_board, 0.016, mock_bus, payload)
    assert player.state.mutators.triggers.falling is True
    assert player.state.velocity.vy > 0.0

    # Step until landing
    for _ in range(120):
        if not player.state.mutators.triggers.falling:
            break
        motion.update(mock_board, 0.016, mock_bus, payload)

    assert settings.TIER_DROP_DISTANCE == 55
    assert player.state.mutators.triggers.falling is False
    assert player.elevation == 0
    assert player.state.mutators.parameters.descension == 0.0
    assert player.state.velocity.vy == 0.0
    assert player.state.position.y == initial_y + settings.TIER_DROP_DISTANCE


def test_gravity_multi_tier_intermediate_landing(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies an entity stepping off an E = 2 ledge onto an underlying E = 1 substrate
    transitions E: 2 -> 1 after TIER_DROP_DISTANCE pixels and lands at E = 1 without
    dropping to E = 0.
    """
    payload = mock_payload()
    motion = mock_mechanic(Mechanics.MOTION.value)
    player = mock_board.player()
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]

    initial_x = 100
    initial_y = 100

    # Configure a walkable floor strut at E = 1 positioned at the E = 2 -> 1 landing coordinate
    strut.elevation = 1
    strut.state.blueprint = Buildings.FLOORS.value
    strut.state.position = Position(initial_x, initial_y + settings.TIER_DROP_DISTANCE)

    # Deploy player at E = 2 above the E = 1 floor (unsupported at E = 2)
    player.elevation = 2
    player.state.position = Position(initial_x, initial_y)
    player.state.velocity = Velocity(0.0, 0.0)
    player.state.mutators.triggers.falling = False
    player.state.mutators.parameters.descension = 0.0

    for _ in range(120):
        motion.update(mock_board, 0.016, mock_bus, payload)
        if not player.state.mutators.triggers.falling:
            break

    assert player.state.mutators.triggers.falling is False
    assert player.elevation == 1
    assert player.state.velocity.vy == 0.0
    assert player.state.position.y == initial_y + settings.TIER_DROP_DISTANCE


def test_gravity_multi_tier_continuous_freefall_to_ground(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies an entity stepping off an E = 2 ledge with no E = 1 substrate below
    falls continuously through E = 1 and lands at E = 0 after 2 * TIER_DROP_DISTANCE (110 px).
    """
    payload = mock_payload()
    motion = mock_mechanic(Mechanics.MOTION.value)
    player = mock_board.player()

    initial_y = 100
    player.elevation = 2
    player.state.position = Position(100, initial_y)
    player.state.velocity = Velocity(0.0, 0.0)
    player.state.mutators.triggers.falling = False
    player.state.mutators.parameters.descension = 0.0

    observed_intermediate_tier_falling = False
    for _ in range(240):
        motion.update(mock_board, 0.016, mock_bus, payload)
        if player.elevation == 1 and player.state.mutators.triggers.falling:
            observed_intermediate_tier_falling = True
        if not player.state.mutators.triggers.falling:
            break

    assert observed_intermediate_tier_falling is True
    assert player.state.mutators.triggers.falling is False
    assert player.elevation == 0
    assert player.state.velocity.vy == 0.0
    assert player.state.position.y == initial_y + (2 * settings.TIER_DROP_DISTANCE)


def test_gravity_stairs_ascent_tread_support(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies an entity ascending Stairs from E = 0 -> 1 remains supported by the
    full stair tread bounding box after CollisionMechanics._traverse_stairs promotes
    its elevation to E = 1.
    """
    payload = mock_payload()
    collision = mock_mechanic(Mechanics.COLLISION.value)
    motion = mock_mechanic(Mechanics.MOTION.value)
    player = mock_board.player()
    stairs = mock_board.instances(AssetInstances.STAIRS.value)[0]

    stairs.elevation = 0
    stairs.state.delta = 1
    stairs.state.direction = "up"
    stairs.state.position = Position(500, 500)

    # Position player on the stair tread moving North (vy < 0, tread_progress <= 0.85)
    player.elevation = 0
    player.state.position = Position(
        stairs.state.position.x,
        stairs.state.position.y - player.dimensions.l + int(stairs.dimensions.l * 0.5),
    )
    player.state.velocity = Velocity(0.0, -20.0)
    player.state.mutators.triggers.falling = False

    # 1. CollisionMechanics promotes player elevation 0 -> 1 on the stair tread
    collision.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == 1

    # 2. MotionMechanics evaluates gravity support at E = 1; stair tread prevents freefall
    motion.update(mock_board, 0.016, mock_bus, payload)
    assert player.elevation == 1
    assert player.state.mutators.triggers.falling is False


def test_gravity_freefall_suppresses_locomotion_and_collisions(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies voluntary directional input and Phase 2 solid collisions are suppressed
    while an entity is airborne (falling == True).
    """
    # Provide horizontal input ("right") while player is falling at E = 1
    payload = mock_payload(goals=["right"])
    motion = mock_mechanic(Mechanics.MOTION.value)
    collision = mock_mechanic(Mechanics.COLLISION.value)
    player = mock_board.player()
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    player.elevation = 1
    player.state.position = Position(100, 100)
    player.state.velocity = Velocity(0.0, 0.0)
    player.state.mutators.triggers.falling = False

    # Place crate at the exact same coordinate on E = 1
    crate.elevation = 1
    crate.state.position = Position(100, 100)
    crate.state.velocity = Velocity(0.0, 0.0)
    crate.state.mutators.triggers.falling = True

    motion.update(mock_board, 0.016, mock_bus, payload)
    collision.update(mock_board, 0.016, mock_bus, payload)

    # Voluntary X input is suppressed during freefall (vx == 0.0) and X position does not shift from collision
    assert player.state.mutators.triggers.falling is True
    assert player.state.velocity.vx == 0.0
    assert player.state.position.x == 100