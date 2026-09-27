"""
# Ontology: tests.unit.app.game.logic.modules.motion.motive
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
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


@pytest.mark.motion
def test_motive_no_intention(mock_board, mock_sprite):
    mock_sprite.state.intention = Intentions.IDLE.value
    mock_sprite.state.velocity.vx = 5.0
    mock_sprite.state.velocity.vy = 5.0
    
    motive.update([mock_sprite], mock_board, 1.0)
    
    # When sprite is idle, motives are removed
    assert mock_sprite.state.velocity.vx == 0.0
    assert mock_sprite.state.velocity.vy == 0.0


@pytest.mark.motion
def test_motive_at_goal(mock_board, mock_sprite, monkeypatch):
    monkeypatch.setattr(
        'app.game.logic.modules.motion.motive.NavigationIntentions', 
        [ Intentions.FIND.value ]
    )
    mock_sprite.state.intention = Intentions.FIND.value
    mock_sprite.state.position.x = 10
    mock_sprite.state.position.y = 10
    mock_sprite.state.goal.position.x = 10
    mock_sprite.state.goal.position.y = 10
    mock_sprite.state.velocity.vx = 5.0
    
    motive.update([mock_sprite], mock_board, 1.0)
    
    assert mock_sprite.state.velocity.vx == 0.0
    assert mock_sprite.state.velocity.vy == 0.0


@pytest.mark.motion
def test_motive_aims_towards_goal(mock_board, mock_sprite, monkeypatch):
    monkeypatch.setattr(
        'app.game.logic.modules.motion.motive.NavigationIntentions', 
        [ Intentions.FIND.value ]
    )
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


@pytest.mark.intentions
@pytest.mark.motion
def test_motive_rvo_opposing_corridor_steering(
    mock_board, 
    mock_sprite, 
    mock_sprite_alt,
    monkeypatch
):
    monkeypatch.setattr(
        'app.game.logic.modules.motion.motive.NavigationIntentions', 
        [ Intentions.FIND.value ]
    )
    mock_sprite.state.layer = "0"
    mock_sprite.state.intention = Intentions.FIND.value
    mock_sprite.state.position = Position(0, 50)
    mock_sprite.state.goal = Goal(
        name="npc", 
        category=Goals.POSITION.value, 
        layer="0", 
        position=Position(100, 50)
    )
    mock_sprite.state.character.speed = 10
    mock_sprite.state.velocity = Velocity(10.0, 0.0)

    mock_sprite_alt.state.layer='0'
    mock_sprite_alt.state.position = Position(70, 50)
    mock_sprite_alt.state.goal = Goal(
        name="npc", 
        category=Goals.POSITION.value, 
        layer="0", 
        position=Position(30, 50)
    )

    motive.update([mock_sprite, mock_sprite_alt], mock_board, 1.0)

    # RVO avoidance must cause lateral steering deviation or velocity adjustment
    assert mock_sprite.state.velocity.vx != 10.0 or mock_sprite.state.velocity.vy != 0.0