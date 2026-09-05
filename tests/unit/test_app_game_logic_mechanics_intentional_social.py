"""
# Ontology: tests.unit.test_app_game_logic_mechanics_social
"""
import pytest
from unittest.mock import MagicMock
from collections import deque

from app.game.logic.mechanics.intentional.social import SocialMechanics
from app.config.enums import Goals, Intentions, Expressions, ExpressionsPalette, AssetInstances
from libs.core.models import Position
from app.models.state import Goal, SpriteState, Memory

def test_social_mechanics_npc_to_npc(mock_board):
    mechanic = SocialMechanics()
    sprite = mock_board.instances("sprites")[0]
    
    # Establish a genuine SpriteState with Memory capabilities
    target_state = SpriteState(id="target_npc", name="target_npc")
    if not target_state.memory:
        target_state.memory = Memory()
    target_state.memory.rumors = []
    
    sprite.state.intention = Intentions.SPEAK.value
    sprite.state.psyche.dialogue = "secret_rumor"
    sprite.state.psyche.expression = None
    sprite.state.goal = Goal(name="target_npc", category=Goals.SUBJECT.value)
    
    mock_target = MagicMock()
    mock_target.instance = AssetInstances.SPRITES.value
    mock_target.state = target_state
    
    mock_board.asset = MagicMock(return_value=mock_target)
    mock_board.cradle = MagicMock()
    mock_board.cradle.spawn_expression.return_value = MagicMock(ttl=120)
    
    mechanic.update(mock_board, 0.016, deque(), MagicMock())
    
    assert "secret_rumor" in target_state.memory.rumors
    mock_board.cradle.spawn_expression.assert_called_once_with(
        ExpressionsPalette.BUBBLES.value, 
        Expressions.LOQUACITY.value, 
        sprite
    )
    assert sprite.state.psyche.expression is not None

def test_social_mechanics_decay(mock_board):
    mechanic = SocialMechanics()
    sprite = mock_board.instances("sprites")[0]
    
    sprite.state.intention = Intentions.SPEAK.value
    sprite.state.psyche.dialogue = "secret_rumor"
    sprite.state.psyche.expression = MagicMock(ttl=1)
    
    mechanic.update(mock_board, 0.016, deque(), MagicMock())
    
    assert sprite.state.psyche.expression is None
    assert sprite.state.psyche.dialogue is None