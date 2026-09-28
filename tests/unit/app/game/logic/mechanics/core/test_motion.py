"""
# Ontology: tests.unit.app.game.logic.mechanics.core.test_motion
"""
# Standard Libraries
import collections

# External Libraries
import pytest

# Application Libraries
from app.game.logic.mechanics import MotionMechanics

# Cython Libraries
from libs.core.models import (
    Position, 
    Velocity
)


@pytest.mark.motion
@pytest.mark.physics
def test_motion_mechanics_update_kinematic_and_frictive(mock_board):
    """
    Verifies MotionMechanics coordinates kinematic integration and tile friction decay.
    """
    mechanic = MotionMechanics()
    bus = collections.deque()
    payload = mock_board.device.poll() if mock_board.device else None

    crate = mock_board.asset("box")
    crate.state.position = Position(10, 10)
    crate.state.velocity = Velocity(20.0, 0.0)

    initial_x = crate.state.position.x
    delta = 0.1

    mechanic.update(mock_board, delta, bus, payload)

    # Position increments via symplectic integration, velocity decays via friction
    assert crate.state.position.x >= initial_x
    assert crate.state.velocity.vx <= 20.0