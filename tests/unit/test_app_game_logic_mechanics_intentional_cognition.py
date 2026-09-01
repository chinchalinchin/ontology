"""
# Ontology: tests.unit.test_app_game_logic_intentional_cognition

Unit tests for CognitionMechanics.
"""
import random
import collections
from unittest.mock import MagicMock

from app.game.logic.mechanics.intentional.cognition import CognitionMechanics
from app.config.enums import Intentions, Goals, Motivations, AssetInstances
from libs.core.models import Position
from app.models.state import Goal


def test_cognition_skips_player(mock_board):
    mechanic = CognitionMechanics()
    player = mock_board.player()
    
    player.state.goal = None
    player.state.mutators.parameters = None
    
    bus = collections.deque()
    mechanic.update(mock_board, 0.16, bus, MagicMock())
    
    # Player's goal logic should remain untouched
    assert player.state.goal is None


def test_cognition_acquire_target_conquest(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    player = mock_board.player()
    
    sprite.state.goal = None
    sprite.state.psyche.motivation = Motivations.CONQUEST.value
    sprite.state.mutators.parameters.vision.radius = 100
    
    # Place player within 100 pixels (10,10 to 20,20)
    player.state.position = Position(20, 20)
    
    mechanic._acquire_target(sprite, mock_board)
    
    assert sprite.state.goal is not None
    assert sprite.state.goal.category == 'sprite'
    assert sprite.state.goal.name == player.name
    assert sprite.state.goal.position.x == 20


def test_cognition_track_target_in_range(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    player = mock_board.player()
    
    # Player moves
    player.state.position = Position(30, 30)
    
    # Sprite previously targeted player
    sprite.state.goal = Goal(
        name=player.name, 
        category=Goals.ASSET, 
        position=Position(0, 0)
    )
    sprite.state.mutators.parameters.vision.radius = 100
    
    mechanic._track_target(sprite, mock_board)
    
    assert sprite.state.mutators.triggers.vision is True
    # Position updates to match player
    assert sprite.state.goal.position.x == 30
    assert sprite.state.goal.position.y == 30


def test_cognition_track_target_out_of_range(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    player = mock_board.player()
    
    # Player moves far away (300, 300) > 100 pixel radius
    player.state.position = Position(300, 300)
    
    sprite.state.goal = Goal(
        name=player.name, 
        category=Goals.ASSET, 
        position=Position(50, 50)
    )
    sprite.state.mutators.parameters.vision.radius = 100
    
    mechanic._track_target(sprite, mock_board)
    
    assert sprite.state.mutators.triggers.vision is False
    # Position freezes at last known location
    assert sprite.state.goal.position.x == 50
    assert sprite.state.goal.position.y == 50


def test_cognition_project_escape(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    
    sprite.state.intention = Intentions.ESCAPE
    sprite.state.mutators.triggers.vision = True
    sprite.state.position = Position(10, 10)
    sprite.state.goal = Goal(
        name="threat", 
        category="sprite", 
        position=Position(20, 20)
    )
    
    mechanic._project_intention(sprite)
    
    # Threat is at (20,20). Sprite is at (10,10). 
    # dx = 10-20 = -10. dy = 10-20 = -10.
    # Extrapolation (dx * 10, dy * 10) -> (-100, -100). 
    # Current pos + Extrapolation = (-90, -90)
    assert sprite.state.goal.position.x == -90
    assert sprite.state.goal.position.y == -90


def test_cognition_project_wander(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    
    sprite.state.intention = Intentions.WANDER
    sprite.state.goal = None
    sprite.state.position = Position(10, 10)
    
    # Fix random seed so testing offsets is deterministic
    random.seed(42)
    mechanic._project_intention(sprite)
    
    assert sprite.state.goal is not None
    assert sprite.state.goal.name == "wander_point"
    assert sprite.state.goal.category == Goals.POSITION.value
    # Random offsets will be applied to the (10, 10) baseline
    assert isinstance(sprite.state.goal.position.x, int)
    assert isinstance(sprite.state.goal.position.y, int)