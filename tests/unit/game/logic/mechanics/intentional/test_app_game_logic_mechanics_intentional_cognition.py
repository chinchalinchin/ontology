"""
# Ontology: tests.unit.test_app_game_logic_mechanics_intentional_cognition
"""
from unittest.mock import MagicMock, patch

import pytest
from app.config.enums import Goals, Intentions, AssetInstances
from app.game.logic.mechanics.intentional.cognition import CognitionMechanics, WANDER
from app.models.state import Goal
from libs.core.models import Position


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


def test_cognition_resolve_position_goal(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    sprite.state.position = Position(50, 50)
    sprite.state.mutators.parameters.action.radius = 15

    sprite.state.goal = Goal(
        name="waypoint",
        category=Goals.POSITION.value,
        position=Position(55, 55)
    )

    mechanic._resolve(sprite, mock_board)
    assert sprite.state.goal is None


def test_cognition_resolve_object_door_transition(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    sprite.state.layer = "brick-house-compose-layer"

    sprite.state.goal = Goal(
        name="door-1",
        category=Goals.OBJECT.value,
        layer="0",
        position=Position(100, 100)
    )
    sprite.state.memory.goals["door-1"] = sprite.state.goal

    mechanic._resolve(sprite, mock_board)
    assert sprite.state.goal is None
    assert "door-1" not in sprite.state.memory.goals


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


def test_cognition_door_finder(mock_board, mock_door_asset):
    mock_board.add([mock_door_asset])
    sprite = mock_board.instances("sprites")[0]
    sprite.state.position = Position(90, 90)
    sprite.state.mutators.parameters.vision.radius = 50
    sprite.state.goal = Goal(name="target", category=Goals.TARGET.value, layer="brick-house-compose-layer")

    door = CognitionMechanics.door(sprite, mock_board)
    assert door is not None
    assert door.name == "wood-door"


def test_cognition_track_cross_layer_subsumption(mock_board, mock_door_asset):
    mock_board.add([mock_door_asset])
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    sprite.state.position = Position(90, 90)
    sprite.state.mutators.parameters.vision.radius = 50

    sprite.state.goal = Goal(
        name="evil-wizard",
        category=Goals.TARGET.value,
        layer="brick-house-compose-layer",
        position=Position(500, 500)
    )

    mechanic._track(sprite, mock_board)

    # Overarching goal subsumed into episodic memory
    assert "evil-wizard" in sprite.state.memory.goals
    assert sprite.state.memory.goals["evil-wizard"].layer == "brick-house-compose-layer"

    # Prerequisite OBJECT door goal injected into active slot
    assert sprite.state.goal.name == "wood-door"
    assert sprite.state.goal.category == Goals.OBJECT.value
    assert sprite.state.goal.layer == sprite.state.layer


def test_cognition_project_escape(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    sprite.state.intention = Intentions.ESCAPE.value
    sprite.state.mutators.triggers.vision = True
    sprite.state.position = Position(100, 100)
    sprite.state.goal = Goal(name="threat", category=Goals.TARGET.value, position=Position(80, 80))

    mechanic._project(sprite, mock_board)

    # dx = 20, dy = 20 -> projected destination = (100 + 200, 100 + 200) = (300, 300)
    assert sprite.state.goal.position.x == 300
    assert sprite.state.goal.position.y == 300


def test_cognition_project_wander(mock_board):
    mechanic = CognitionMechanics()
    sprite = mock_board.instances("sprites")[0]
    sprite.state.intention = Intentions.WANDER.value
    sprite.state.goal = None
    sprite.state.position = Position(50, 50)
    sprite.state.mutators.parameters.vision.radius = 20

    mechanic._project(sprite, mock_board)

    assert sprite.state.goal is not None
    assert sprite.state.goal.name == WANDER
    assert sprite.state.goal.category == Goals.POSITION.value
    assert sprite.state.goal.layer == sprite.state.layer


def test_cognition_complete(mock_board):
    sprite = mock_board.instances("sprites")[0]
    sprite.state.goal = None
    assert CognitionMechanics.complete(sprite, mock_board) is True

    player = mock_board.player()
    player.state.mutators.triggers.dead = False
    sprite.state.goal = Goal(name=player.name, category=Goals.TARGET.value)
    assert CognitionMechanics.complete(sprite, mock_board) is False

    player.state.mutators.triggers.dead = True
    assert CognitionMechanics.complete(sprite, mock_board) is True