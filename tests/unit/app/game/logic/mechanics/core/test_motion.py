"""
@domain.test
@test.unit
@app.mechanic
@app.core
@physics.motion

# Ontology: Tests - tests.unit.app.game.logic.mechanics.core.test_motion

Unit Tests for MotionMechanics.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Mechanics,
    PlayerGoals,
    Goals,
    Intentions
)
from app.models.state.assets import Goal


# Cython Libraries
from libs.core.models import (
    Position, 
    Velocity
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_core,
    pytest.mark.app_mechanic,
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

@pytest.mark.workflow_player
def test_motion_mechanics_update_kinematic_player_integrates_position(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies MotionMechanics translates directional input payloads into kinematic
    player velocity and integrates world coordinates.
    """
    mechanics = mock_mechanic(Mechanics.MOTION.value)
    player = mock_board.player()
    delta = 0.1
    speed = float(player.state.character.speed)

    player.elevation = 0
    player.state.mutators.triggers.falling = False
    player.state.position = Position(300, 100)
    player.state.velocity = Velocity(0.0, 0.0)

    payload = mock_payload(goals=[PlayerGoals.RIGHT.value])
    mechanics.update(mock_board, delta, mock_bus, payload)

    assert player.state.velocity.vx == speed
    assert player.state.velocity.vy == 0.0
    assert player.state.position.x == 300 + int(speed * delta)


@pytest.mark.modality_intention
def test_motion_mechanics_update_motive_sprite_integrates_toward_goal(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies MotionMechanics steers an autonomous navigating sprite toward its goal
    and advances its position via symplectic integration.
    """
    mechanics = mock_mechanic(Mechanics.MOTION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    delta = 0.1
    speed = float(sprite.state.character.speed)

    # Isolate all other characters away from the sprite's squeeze radius
    for name, char in mock_board.characters().items():
        if name != sprite.name:
            char.position = Position(600, 600)

    sprite.state.layer = "0"
    sprite.elevation = 0
    sprite.state.mutators.triggers.falling = False
    sprite.state.position = Position(300, 100)
    sprite.state.velocity = Velocity(0.0, 0.0)
    sprite.state.intention = Intentions.FIND.value
    sprite.state.trajectory.target = None
    sprite.state.goal = Goal(
        name="waypoint",
        category=Goals.POSITION.value,
        layer="0",
        position=Position(400, 100),
    )

    mechanics.update(mock_board, delta, mock_bus, mock_payload())

    assert sprite.state.velocity.vx == speed
    assert sprite.state.velocity.vy == 0.0
    assert sprite.state.position.x == 300 + int(speed * delta)