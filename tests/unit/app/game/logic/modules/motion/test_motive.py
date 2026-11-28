"""
@domain.test
@test.unit
@app.module
@physics.motion

# Ontology: tests.unit.app.game.logic.modules.motion.test_motive

Unit tests for the motive motion module.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Intentions, 
    Goals
)
from app.game.logic.modules.motion import motive
from app.models.state import Goal

# Cython Libraries
from libs.core.models import (
    Position, 
    Velocity
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.physics_motion,
    pytest.mark.category_sheets,
    pytest.mark.modality_intention
]

# -----------------------------------------------------


def test_motive_no_intention(mock_board):
    mock_sprite = mock_board.instances(
        AssetInstances.SPRITES.value
    )[0]
    mock_sprite.state.intention = Intentions.IDLE.value
    mock_sprite.state.velocity.vx = 5.0
    mock_sprite.state.velocity.vy = 5.0
    
    motive.update([mock_sprite], mock_board, 1.0)
    
    # When sprite is idle, motives are removed
    assert mock_sprite.state.velocity.vx == 0.0
    assert mock_sprite.state.velocity.vy == 0.0


def test_motive_at_goal(mock_board):
    mock_sprite = mock_board.instances(
        AssetInstances.SPRITES.value
    )[0]
    mock_sprite.state.intention = Intentions.FIND.value
    mock_sprite.state.position.x = 10
    mock_sprite.state.position.y = 10
    mock_sprite.state.goal.position.x = 10
    mock_sprite.state.goal.position.y = 10
    mock_sprite.state.velocity.vx = 5.0
    
    motive.update([mock_sprite], mock_board, 1.0)
    
    assert mock_sprite.state.velocity.vx == 0.0
    assert mock_sprite.state.velocity.vy == 0.0


def test_motive_aims_towards_goal(mock_board):
    mock_sprite = mock_board.instances(
        AssetInstances.SPRITES.value
    )[0]
    mock_sprite.state.intention = Intentions.FIND.value
    
    # Reposition player outside squeeze radius (30) so path is clear of neighbors
    player = mock_board.player()
    if player:
        player.state.position = Position(500, 500)

    mock_sprite.state.position.x = 0
    mock_sprite.state.position.y = 0
    mock_sprite.state.goal.position.x = 100
    mock_sprite.state.goal.position.y = 0
    
    mock_sprite.state.character.speed = 20
    mock_sprite.state.velocity.vx = 0.0
    mock_sprite.state.velocity.vy = 0.0
    
    motive.update([mock_sprite], mock_board, 1.0)
    
    # Preferred velocity aims directly towards goal scaled to speed via physics.aim
    assert mock_sprite.state.velocity.vx == 20.0
    assert mock_sprite.state.velocity.vy == 0.0


def test_motive_rvo_opposing_corridor_steering(mock_board):
    mock_sprite = mock_board.instances(
        AssetInstances.SPRITES.value
    )[0]
    mock_sprite.state.layer = "0"
    mock_sprite.state.intention = Intentions.FIND.value
    mock_sprite.state.position = Position(0, 50)
    mock_sprite.state.mutators.parameters.squeeze.radius = 100  # Expand sensory footprint
    mock_sprite.state.goal = Goal(
        name="npc", 
        category=Goals.POSITION.value, 
        layer="0", 
        position=Position(100, 50)
    )
    mock_sprite.state.character.speed = 10
    mock_sprite.state.velocity = Velocity(10.0, 0.0)

    mock_sprite_alt = mock_board.instances(
        AssetInstances.SPRITES.value
    )[1]
    mock_sprite_alt.state.layer='0'
    mock_sprite_alt.state.position = Position(70, 50)
    mock_sprite_alt.state.mutators.parameters.squeeze.radius = 100  # Expand sensory footprint
    mock_sprite_alt.state.goal = Goal(
        name="npc", 
        category=Goals.POSITION.value, 
        layer="0", 
        position=Position(30, 50)
    )

    motive.update([mock_sprite, mock_sprite_alt], mock_board, 1.0)

    # RVO avoidance must cause lateral steering deviation or velocity adjustment
    assert mock_sprite.state.velocity.vx != 10.0 or mock_sprite.state.velocity.vy != 0.0

@pytest.mark.workflow_gravity
def test_motive_falling_preserves_velocity(mock_board):
    """Verifies falling sprites bypass motive steering and idle velocity zeroing."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.mutators.triggers.falling = True
    sprite.state.velocity = Velocity(15.0, 25.0)

    motive.update([sprite], mock_board, 1.0)

    assert sprite.state.velocity.vx == 15.0
    assert sprite.state.velocity.vy == 25.0


def test_motive_no_goal_zeroes_velocity(mock_board):
    """Verifies a sprite in a navigation intention with goal=None halts cleanly."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite.state.intention = Intentions.FIND.value
    sprite.state.goal = None
    sprite.state.velocity = Velocity(10.0, 10.0)

    motive.update([sprite], mock_board, 1.0)

    assert sprite.state.velocity.vx == 0.0
    assert sprite.state.velocity.vy == 0.0


def test_motive_prefers_trajectory_target_over_goal(mock_board):
    """Verifies trajectory.target takes precedence over goal.position during steering."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    speed = float(sprite.state.character.speed)

    for name, char in mock_board.characters().items():
        if name != sprite.name:
            char.position = Position(600, 600)

    sprite.state.layer = "0"
    sprite.state.intention = Intentions.FIND.value
    sprite.state.position = Position(0, 0)
    sprite.state.goal = Goal(
        name="waypoint",
        category=Goals.POSITION.value,
        layer="0",
        position=Position(100, 0),
    )
    sprite.state.trajectory.target = Position(0, 100)

    motive.update([sprite], mock_board, 1.0)

    assert sprite.state.velocity.vx == 0.0
    assert sprite.state.velocity.vy == speed


def test_motive_missing_target_position_zeroes_velocity(mock_board):
    """Verifies steering zeroes velocity when both trajectory.target and goal.position are None."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite.state.intention = Intentions.FIND.value
    sprite.state.trajectory.target = None
    sprite.state.goal = Goal(
        name="waypoint",
        category=Goals.POSITION.value,
        layer="0",
        position=None,
    )
    sprite.state.velocity = Velocity(10.0, 5.0)

    motive.update([sprite], mock_board, 1.0)

    assert sprite.state.velocity.vx == 0.0
    assert sprite.state.velocity.vy == 0.0


def test_motive_rvo_ignores_characters_on_other_layers(mock_board):
    """Verifies RVO excludes characters residing on different layers."""
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    speed = float(sprite.state.character.speed)

    for name, char in mock_board.characters().items():
        if name != sprite.name:
            char.layer = "other-layer"
            char.position = Position(50, 50)

    sprite.state.layer = "0"
    sprite.state.intention = Intentions.FIND.value
    sprite.state.position = Position(0, 50)
    sprite.state.mutators.parameters.squeeze.radius = 100
    sprite.state.trajectory.target = None
    sprite.state.goal = Goal(
        name="waypoint",
        category=Goals.POSITION.value,
        layer="0",
        position=Position(100, 50),
    )

    motive.update([sprite], mock_board, 1.0)

    assert sprite.state.velocity.vx == speed
    assert sprite.state.velocity.vy == 0.0