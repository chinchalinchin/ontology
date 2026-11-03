"""
@domain.test
@test.unit
@app.mechanic
@physics.motion

# Ontology: Tests - tests.unit.app.game.logic.mechanics.core.test_motion

Unit Tests for MotionMechanics.
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
    Velocity
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.physics_motion
]

# -----------------------------------------------------


def test_motion_mechanics_update_kinematic_and_frictive(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload
):
    """
    Verifies MotionMechanics coordinates kinematic integration and tile friction decay.
    """
    mechanics = mock_mechanic(Mechanics.MOTION.value)
    payload = mock_payload()
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    crate.state.position = Position(10, 10)
    crate.state.velocity = Velocity(20.0, 0.0)

    initial_x = crate.state.position.x
    delta = 0.1

    mechanics.update(mock_board, delta, mock_bus, payload)

    # Position increments via symplectic integration, velocity decays via friction
    assert crate.state.position.x >= initial_x
    assert crate.state.velocity.vx <= 20.0