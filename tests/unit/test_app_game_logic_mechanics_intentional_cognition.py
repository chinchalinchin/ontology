"""
# Ontology: tests.unit.test_app_game_logic_mechanics_intentional_cognition
"""
import pytest
from unittest.mock import MagicMock, patch
from collections import deque

import app.config.settings as settings
from app.game.logic.mechanics.intentional.cognition import CognitionMechanics
from app.config.enums import Goals, Intentions
from libs.core.models import Position, Boundary, Dimensions
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

def test_cognition_anchor_with_hitbox(mock_sprite_with_hitbox):
    # Position: (175, 200), Hitbox: pos=(21, 23), dim=(22, 21)
    # Footprint anchor: x = 175 + 21 + 22 // 2 = 207, y = 200 + 23 + 21 // 2 = 233
    anchor = CognitionMechanics.anchor(mock_sprite_with_hitbox)
    assert anchor.x == 207
    assert anchor.y == 233


def test_cognition_anchor_fallback_dimensions(mock_crate):
    # Position: (10, 10), Dimensions: (32, 32), default hitbox generated matching dimensions
    anchor = CognitionMechanics.anchor(mock_crate)
    assert anchor.x == 10 + 32 // 2
    assert anchor.y == 10 + 32 // 2


def test_cognition_obstacles_multi_hitbox(mock_board, mock_multi_hitbox_asset):
    mock_board.add([mock_multi_hitbox_asset])
    obs = CognitionMechanics.obstacles(layer="0", board=mock_board, exclude=[])

    # Position: (250, 250)
    # Hitbox 1: (178, 102, 25, 12) -> (428, 352, 25, 12)
    # Hitbox 2: (17, 102, 25, 12)  -> (267, 352, 25, 12)
    # Hitbox 3: (5, 39, 203, 63)   -> (255, 289, 203, 63)
    assert (428, 352, 25, 12) in obs
    assert (267, 352, 25, 12) in obs
    assert (255, 289, 203, 63) in obs


def test_cognition_obstacles_offset_hitbox(mock_board, mock_offset_hitbox_asset):
    mock_board.add([mock_offset_hitbox_asset])
    obs = CognitionMechanics.obstacles(layer="brick-house-compose-layer", board=mock_board, exclude=[])

    # Position: (150, 150), Hitbox: (6, 17, 116, 54) -> (156, 167, 116, 54)
    assert (156, 167, 116, 54) in obs


def test_cognition_obstacles_exclusion_and_perimeters(mock_board, mock_offset_hitbox_asset):
    mock_board.add([mock_offset_hitbox_asset])
    mock_board.perimeters["brick-house-compose-layer"] = [
        Boundary(Position(0, 0), Dimensions(10, 20))
    ]

    obs = CognitionMechanics.obstacles(
        layer="brick-house-compose-layer",
        board=mock_board,
        exclude=[mock_offset_hitbox_asset.name]
    )

    # Excluded asset hitbox must not be present
    assert (156, 167, 116, 54) not in obs
    # Perimeter boundary must be present
    assert (0, 0, 10, 20) in obs


def test_cognition_path_fifo_queue_injection(mock_sprite_with_hitbox):
    sprite = mock_sprite_with_hitbox
    initial_goal = Goal(name="target-entity", category=Goals.TARGET.value, layer="0", position=Position(100, 100))
    sprite.state.goal = initial_goal

    waypoints = [Position(20, 20), Position(40, 40), Position(60, 60)]
    CognitionMechanics.path(sprite, waypoints)

    assert sprite.state.goal is None
    goal_keys = list(sprite.state.memory.goals.keys())

    # Verify FIFO waypoint injection followed by original goal preservation
    expected_p0 = f"{settings.RRT_PATH_PREFIX}{settings.SEPARATOR}0"
    expected_p1 = f"{settings.RRT_PATH_PREFIX}{settings.SEPARATOR}1"
    expected_p2 = f"{settings.RRT_PATH_PREFIX}{settings.SEPARATOR}2"

    assert goal_keys == [expected_p0, expected_p1, expected_p2, "target-entity"]
    assert sprite.state.memory.goals[expected_p0].position.x == 20
    assert sprite.state.memory.goals[expected_p1].position.x == 40
    assert sprite.state.memory.goals[expected_p2].position.x == 60
    assert sprite.state.memory.goals["target-entity"] is initial_goal


def test_cognition_scrap_invalidated_waypoint(mock_board, mock_sprite_with_hitbox):
    sprite = mock_sprite_with_hitbox
    cognition = CognitionMechanics()

    waypoint_name = f"{settings.RRT_PATH_PREFIX}{settings.SEPARATOR}0"
    sprite.state.goal = Goal(name=waypoint_name, category=Goals.POSITION.value, layer="0", position=Position(200, 200))
    sprite.state.memory.goals[waypoint_name] = sprite.state.goal
    sprite.state.memory.goals["future-target"] = Goal(name="future-target", category=Goals.TARGET.value)

    # Inject an obstacle directly bisecting the path from anchor to waypoint
    with patch.object(CognitionMechanics, "obstacles", return_value=[(180.0, 180.0, 50.0, 50.0)]):
        scrapped = cognition._scrap(sprite, mock_board)

    assert scrapped is True
    assert sprite.state.goal is None
    assert waypoint_name not in sprite.state.memory.goals
    assert "future-target" in sprite.state.memory.goals