"""
# Ontology: tests.unit.test_app_game_logic_mechanics_intentional_cognition
"""
import pytest
from unittest.mock import MagicMock
from collections import deque

from app.game.logic.mechanics.intentional.cognition import CognitionMechanics
from app.config.enums import Goals, Intentions
from libs.core.models import Position
from app.models.state import Goal

def test_cognition_track_target_in_range(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    player = mock_board.player()

    player.state.position = Position(30, 30)

    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        position=Position(0, 0)
    )
    sprite.state.mutators.parameters.vision.radius = 100
    sprite.state.memory.sprites[player.name] = player.state.position

    mechanic._track(sprite, mock_board)

    assert sprite.state.mutators.triggers.vision is True
    assert sprite.state.goal.position.x == 30
    assert sprite.state.goal.position.y == 30

def test_cognition_track_target_out_of_range(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    player = mock_board.player()

    player.state.position = Position(200, 200)

    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        position=Position(0, 0)
    )
    sprite.state.mutators.parameters.vision.radius = 100
    sprite.state.memory.sprites[player.name] = player.state.position

    mechanic._track(sprite, mock_board)

    assert sprite.state.mutators.triggers.vision is False
    assert sprite.state.goal.position.x == 0
    assert sprite.state.goal.position.y == 0

def test_cognition_resolve_target_dead(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    player = mock_board.player()
    player.state.mutators.triggers.dead = True

    sprite.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        position=Position(0, 0)
    )
    sprite.state.memory.goals[player.name] = sprite.state.goal
    
    mechanic._resolve(sprite, mock_board)

    assert sprite.state.goal is None
    assert player.name not in sprite.state.memory.goals

def test_cognition_resolve_subject_no_dialogue(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]

    sprite.state.goal = Goal(
        name="some_npc",
        category=Goals.SUBJECT.value,
        position=Position(0, 0)
    )
    sprite.state.psyche.dialogue = None
    
    mechanic._resolve(sprite, mock_board)

    assert sprite.state.goal is None

def test_cognition_ideate_dialogue_target(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    player = mock_board.player()
    
    sprite.state.psyche.dialogue = "hello"
    sprite.state.mutators.parameters.vision.radius = 100
    sprite.state.goal = Goal(name="wander", category=Goals.POSITION.value, position=Position(100, 100))
    sprite.state.position = Position(0, 0)
    player.state.position = Position(10, 10)
    
    mechanic._ideate(sprite, mock_board)
    
    assert sprite.state.goal.category == Goals.SUBJECT.value
    assert sprite.state.goal.name == player.name
    assert "wander" in sprite.state.memory.goals

def test_cognition_remember_idle_only(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    
    sprite.state.goal = None
    sprite.state.intention = Intentions.ATTACK.value
    sprite.state.memory.goals["old_goal"] = Goal(name="old_goal", category=Goals.POSITION.value, position=Position(100, 100))
    
    mechanic._remember(sprite, mock_board)
    assert sprite.state.goal is None
    
    sprite.state.intention = Intentions.IDLE.value
    mechanic._remember(sprite, mock_board)
    assert sprite.state.goal.name == "old_goal"