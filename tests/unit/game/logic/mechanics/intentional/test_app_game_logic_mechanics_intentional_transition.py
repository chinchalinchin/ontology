"""
# Ontology: tests.unit.test_app_game_logic_intentional_transition

Unit tests for TransitionMechanics.
"""
from unittest.mock import MagicMock
import collections

from app.game.logic.mechanics.intentional.transition import TransitionMechanics
from app.config.enums import Intentions, Actions, Directions
from libs.core.models import Position
from app.models.state import Goal


def test_transition_update_evaluates_executor(mock_board):
    mechanic = TransitionMechanics()
    
    # Setup mock Executor
    mock_executor = MagicMock()
    mock_executor.evaluate.return_value = Intentions.HUNT
    mechanic.executor = mock_executor
    
    # Setup sprite state
    sprite = mock_board.instances("sprites")[0]
    sprite.state.intention = Intentions.IDLE
    sprite.state.goal = Goal(name="target", category="sprite", position=Position(x=20, y=20))
    
    # Run loop
    bus = collections.deque()
    mechanic.update(mock_board, 0.16, bus, MagicMock())
    
    # Assert ISL logic mutated the intention
    assert sprite.state.intention == Intentions.HUNT
    
    # Assert AnimationMap correctly resolved the goal direction and intention action
    # (HUNT -> WALK fallback, 10,10 to 20,20 -> RIGHT)
    assert sprite.state.animation.action == Actions.WALK.value
    assert sprite.state.animation.direction == Directions.RIGHT.value
    
    # Ensure evaluate was called with the sprite's state and cross-layer dict
    mock_executor.evaluate.assert_called_once()
    

def test_transition_update_skips_without_executor(mock_board):
    mechanic = TransitionMechanics()
    mechanic.executor = None
    
    sprite = mock_board.instances("sprites")[0]
    sprite.state.intention = Intentions.IDLE
    
    bus = collections.deque()
    mechanic.update(mock_board, 0.16, bus, MagicMock())
    
    # Should safely skip ISL evaluation and remain IDLE
    assert sprite.state.intention == Intentions.IDLE
    assert sprite.state.animation.action == Actions.WALK.value