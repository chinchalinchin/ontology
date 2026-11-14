"""
@domain.tests
@test.unit
@app.library
@physics.motion
@workflow.collisions

# Ontology: Tests - tests.unit.libs.core.math.test_physics

Unit tests for the Cython Physics Library.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
)

# Cython Libraries
from libs.core.models import (
    Position,
    Dimensions,
    Hitbox,
    Velocity,
)
from libs.core.math import physics

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_library,
    pytest.mark.physics_motion,
    pytest.mark.workflow_collisions,
]

# ----------------------------------------------------------------------------------------
# COLLISIONS & INTEGRATION TESTS
# ----------------------------------------------------------------------------------------


def test_physics_collisions(mock_space_grid):
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))

    p1 = (0, 10, 10, 32, 32, [hb])
    p2 = (1, 20, 20, 32, 32, [hb])
    p3 = (2, 200, 200, 32, 32, [hb])

    pairs = physics.collisions([p1, p2, p3], mock_space_grid)
    assert pairs == [(0, 1)]


@pytest.mark.app_asset
def test_physics_integrate(mock_asset):
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.state.position = Position(0, 0)
    crate.state.velocity = Velocity(10.0, -10.0)

    physics.integrate([crate], 0.5)

    assert crate.state.position.x == 5
    assert crate.state.position.y == -5
    assert crate.state.position.rx == 0.0
    assert crate.state.position.ry == 0.0


@pytest.mark.app_asset
def test_physics_integrate_subpixel_accumulation(mock_asset):
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.state.position = Position(10, 20)
    crate.state.velocity = Velocity(1.0, -1.0)

    physics.integrate([crate], 0.4)
    assert crate.state.position.x == 10
    assert crate.state.position.y == 20
    assert pytest.approx(crate.state.position.rx, rel=1e-5) == 0.4
    assert pytest.approx(crate.state.position.ry, rel=1e-5) == -0.4

    physics.integrate([crate], 0.8)
    assert crate.state.position.x == 11
    assert crate.state.position.y == 19
    assert pytest.approx(crate.state.position.rx, rel=1e-5) == 0.2
    assert pytest.approx(crate.state.position.ry, rel=1e-5) == -0.2


# ----------------------------------------------------------------------------------------
# NARROW-PHASE COLLIDE RESOLUTION TESTS
# ----------------------------------------------------------------------------------------


def test_physics_collide_dynamic_x_axis():
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    pos1 = Position(0, 0)
    pos2 = Position(24, 0)
    vel1 = Velocity(10.0, 0.0)
    vel2 = Velocity(-10.0, 0.0)

    physics.collide(pos1, hb, vel1, 5.0, False, pos2, hb, vel2, 5.0, False)

    assert pos1.x == -4
    assert pos2.x == 28
    assert vel1.vx == -10.0
    assert vel2.vx == 10.0


def test_physics_collide_dynamic_y_axis():
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    pos1 = Position(0, 24)
    pos2 = Position(0, 0)
    vel1 = Velocity(0.0, -20.0)
    vel2 = Velocity(0.0, 10.0)

    physics.collide(pos1, hb, vel1, 5.0, False, pos2, hb, vel2, 5.0, False)

    assert pos1.y == 28
    assert pos2.y == -4
    assert vel1.vy == 10.0
    assert vel2.vy == -20.0


def test_physics_collide_static_vs_dynamic_inverts_velocity():
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    pos_static = Position(0, 0)
    pos_dyn = Position(20, 0)
    vel_dyn = Velocity(-15.0, 5.0)

    physics.collide(pos_static, hb, None, 0.0, False, pos_dyn, hb, vel_dyn, 5.0, False)

    assert pos_static.x == 0
    assert pos_dyn.x == 32
    assert vel_dyn.vx == 15.0
    assert vel_dyn.vy == 5.0


def test_physics_collide_dynamic_vs_static_y_axis():
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    pos_dyn = Position(0, 0)
    pos_static = Position(0, 20)
    vel_dyn = Velocity(5.0, 15.0)

    physics.collide(pos_dyn, hb, vel_dyn, 5.0, False, pos_static, hb, None, 0.0, False)

    assert pos_dyn.y == -12
    assert pos_static.y == 20
    assert vel_dyn.vy == -15.0


def test_physics_collide_kinematic_preserves_velocity():
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    pos_player = Position(0, 0)
    pos_crate = Position(24, 0)
    vel_player = Velocity(50.0, 0.0)
    vel_crate = Velocity(0.0, 0.0)

    physics.collide(
        pos_player, hb, vel_player, 5.0, True,
        pos_crate, hb, vel_crate, 5.0, False,
    )

    assert pos_player.x == -4
    assert pos_crate.x == 28
    assert vel_player.vx == 50.0
    assert vel_crate.vx == 50.0


def test_physics_collide_coincident_centers_and_static_pair():
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    pos1 = Position(10, 10)
    pos2 = Position(10, 10)
    vel1 = Velocity(0.0, 0.0)
    vel2 = Velocity(0.0, 0.0)

    # Static + Static is a no-op
    physics.collide(pos1, hb, vel1, 0.0, False, pos2, hb, vel2, 0.0, False)
    assert pos1.x == 10 and pos2.x == 10

    # Dynamic coincident centers (dx == 0, dy == 0) fallback separates along X
    physics.collide(pos1, hb, vel1, 5.0, False, pos2, hb, vel2, 5.0, False)
    assert pos1.x != pos2.x


# ----------------------------------------------------------------------------------------
# FRICTION, KINEMATICS & DYNAMICS TESTS
# ----------------------------------------------------------------------------------------


def test_physics_friction_decay_and_clamp():
    vel = Velocity(30.0, 40.0)  # magnitude = 50.0
    physics.friction(vel, 20.0, 0.5)  # dv = 10.0 -> magnitude = 40.0

    assert pytest.approx(vel.vx, rel=1e-5) == 24.0
    assert pytest.approx(vel.vy, rel=1e-5) == 32.0

    # High friction clamps cleanly to 0.0 without negative overshoot
    physics.friction(vel, 500.0, 1.0)
    assert vel.vx == 0.0
    assert vel.vy == 0.0

    # Zero velocity remains 0.0
    physics.friction(vel, 10.0, 0.5)
    assert vel.vx == 0.0
    assert vel.vy == 0.0


def test_physics_kinematics_cardinal_diagonal_and_zero():
    vel = Velocity(12.0, 34.0)

    # Horizontal-only input zeroes vy and clamps vx to speed
    physics.kinematics(vel, 1.0, 0.0, 100.0)
    assert pytest.approx(vel.vx, rel=1e-5) == 100.0
    assert vel.vy == 0.0

    # Vertical-only input zeroes vx and clamps vy to speed
    physics.kinematics(vel, 0.0, -1.0, 100.0)
    assert vel.vx == 0.0
    assert pytest.approx(vel.vy, rel=1e-5) == -100.0

    # Diagonal input normalizes vector magnitude to speed
    physics.kinematics(vel, 3.0, 4.0, 50.0)
    assert pytest.approx(vel.vx, rel=1e-5) == 30.0
    assert pytest.approx(vel.vy, rel=1e-5) == 40.0

    # Zero input zeroes velocity
    physics.kinematics(vel, 0.0, 0.0, 100.0)
    assert vel.vx == 0.0
    assert vel.vy == 0.0


def test_physics_dynamics_acceleration_clamp_and_arrival():
    vel = Velocity(0.0, 0.0)

    # Accelerate toward (100, 0) with impulse=50, delta=0.5 -> vx = 25.0
    physics.dynamics(vel, 0.0, 0.0, 100.0, 0.0, 40.0, 50.0, 0.5)
    assert pytest.approx(vel.vx, rel=1e-5) == 25.0
    assert vel.vy == 0.0

    # Second tick clamps magnitude to speed=40.0
    physics.dynamics(vel, 0.0, 0.0, 100.0, 0.0, 40.0, 50.0, 0.5)
    assert pytest.approx(vel.vx, rel=1e-5) == 40.0

    # Arrival snap when distance (5.0) < speed * delta (40.0 * 0.5 = 20.0)
    physics.dynamics(vel, 95.0, 0.0, 100.0, 0.0, 40.0, 50.0, 0.5)
    assert pytest.approx(vel.vx, rel=1e-5) == 10.0

    # Coincident target (dx == 0, dy == 0) zeroes velocity
    physics.dynamics(vel, 100.0, 0.0, 100.0, 0.0, 40.0, 50.0, 0.5)
    assert vel.vx == 0.0
    assert vel.vy == 0.0


# ----------------------------------------------------------------------------------------
# BOUNDARIES, CONSTRAIN & ENVIRONMENT SENSOR TESTS
# ----------------------------------------------------------------------------------------


def test_physics_boundaries_and_environment(mock_space_grid):
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    assets = [
        (0, 10, 10, 32, 32, [hb]),
        (1, 300, 300, 32, 32, [hb]),
    ]
    bounds = [
        (0, 20, 20, 16, 16),
    ]

    assert physics.boundaries(assets, bounds, mock_space_grid) == [(0, 0)]
    assert physics.environment(assets, bounds, mock_space_grid) == [(0, 0)]


def test_physics_constrain_x_and_y_axes():
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))

    # X-axis overlap (overlap_x = 4 < overlap_y = 32)
    pos_x = Position(0, 0)
    vel_x = Velocity(25.0, 10.0)
    physics.constrain(pos_x, hb, vel_x, False, 28, 0, 10, 32)
    assert pos_x.x == -4
    assert vel_x.vx == -25.0
    assert vel_x.vy == 10.0

    # Y-axis overlap with kinematic entity (preserves velocity)
    pos_y = Position(0, 10)
    vel_y = Velocity(0.0, -25.0)
    physics.constrain(pos_y, hb, vel_y, True, 0, 0, 32, 14)
    assert pos_y.y == 14
    assert vel_y.vy == -25.0


# ----------------------------------------------------------------------------------------
# RVO AIM & AVOID TESTS
# ----------------------------------------------------------------------------------------


def test_physics_aim():
    v = physics.aim(Position(0, 0), Position(30, 40), 50.0)
    assert pytest.approx(v.vx, rel=1e-5) == 30.0
    assert pytest.approx(v.vy, rel=1e-5) == 40.0

    v_zero = physics.aim(Position(10, 10), Position(10, 10), 50.0)
    assert v_zero.vx == 0.0
    assert v_zero.vy == 0.0


@pytest.mark.app_asset
def test_physics_avoid_clear_and_obstructed(mock_asset):
    sprite_a = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite_b = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite_a.state.position = Position(0, 0)
    sprite_a.state.velocity = Velocity(50.0, 0.0)

    # Zero speed or empty neighbors returns preferred velocity unchanged
    v_empty = physics.avoid(sprite_a, Velocity(50.0, 0.0), [], 0.016)
    assert v_empty.vx == 50.0 and v_empty.vy == 0.0

    v_stopped = physics.avoid(sprite_a, Velocity(0.0, 0.0), [sprite_b], 0.016)
    assert v_stopped.vx == 0.0 and v_stopped.vy == 0.0

    # Distant neighbor out of collision cone leaves preferred velocity intact
    sprite_b.state.position = Position(0, 300)
    sprite_b.state.velocity = Velocity(0.0, 0.0)
    v_clear = physics.avoid(sprite_a, Velocity(50.0, 0.0), [sprite_b], 0.016)
    assert pytest.approx(v_clear.vx, rel=1e-5) == 50.0
    assert pytest.approx(v_clear.vy, rel=1e-5) == 0.0

    # Head-on neighbor inside collision cone deflects velocity off the X-axis
    sprite_b.state.position = Position(80, 0)
    sprite_b.state.velocity = Velocity(-50.0, 0.0)
    v_deflected = physics.avoid(sprite_a, Velocity(50.0, 0.0), [sprite_b], 0.016)
    assert v_deflected.vy != 0.0

    # Tuple neighbor representation with kinematic flag (is_kinematic=True)
    kinematic_tuple = (80.0, 0.0, 0.0, 0.0, 32.0, True)
    v_tuple = physics.avoid((0, 0, 0, 64, 64), Velocity(50.0, 0.0), [kinematic_tuple], 0.016)
    assert v_tuple.vy != 0.0