"""
# Ontology: tests.unit.logic.mechanics.intentional.test_player
"""
# Standard Libraries
from unittest.mock import MagicMock

# External Libraries
import pytest

# Application Libraries
from app.game.logic.mechanics import PlayerMechanics
from app.config.enums import (
    Intentions, 
    PlayerGoals
)
from app.models.state import (
    DevicePayload, 
    WorldPayload, 
    MenuPayload, 
    Inventory, 
    Equipment, 
    Mutators, 
    MutatorTriggers, 
    Character
)

def _setup_player(mock_board):
    player = mock_board.player()
    player.state.inventory = Inventory(equipment=Equipment())
    player.state.mutators = Mutators(triggers=MutatorTriggers())
    player.state.character = Character(speed=5)
    player.state.animation.frame = 0
    player.state.animation.tick = 0
    return player


@pytest.mark.player
def test_player_new_intention_resets_animation(mock_board):
    mechanic = PlayerMechanics()
    player = mock_board.player()
    player.state.intention = Intentions.IDLE
    player.state.animation.frame = 5
    player.state.animation.tick = 3
    
    payload = DevicePayload(
        world=WorldPayload(intention=Intentions.ATTACK, goals=[]),
        menu=MenuPayload()
    )
    
    mechanic.update(mock_board, 0.16, MagicMock(), payload)
    
    assert player.state.intention == Intentions.ATTACK
    assert player.state.animation.frame == 0
    assert player.state.animation.tick == 0


@pytest.mark.player
def test_player_blocking_intention_persists(mock_board):
    mechanic = PlayerMechanics()
    player = mock_board.player()
    player.state.intention = Intentions.ATTACK
    player.state.animation.frame = 1  # Indicates animation is currently active
    player.state.animation.tick = 0
    
    payload = DevicePayload(
        world=WorldPayload(intention=None, goals=[]),
        menu=MenuPayload()
    )
    
    mechanic.update(mock_board, 0.16, MagicMock(), payload)
    
    # Engine should not fallback to IDLE while a blocking animation is resolving
    assert player.state.intention == Intentions.ATTACK


@pytest.mark.player
def test_player_blocking_intention_completes(mock_board):
    mechanic = PlayerMechanics()
    player = mock_board.player()
    player.state.intention = Intentions.ATTACK
    player.state.animation.frame = 0  # Animation has completed its sequence
    player.state.animation.tick = 0
    
    payload = DevicePayload(
        world=WorldPayload(intention=None, goals=[]),
        menu=MenuPayload()
    )
    
    mechanic.update(mock_board, 0.16, MagicMock(), payload)
    
    # Engine should safely fallback to IDLE
    assert player.state.intention == Intentions.IDLE


@pytest.mark.player
def test_player_movement_updates_goal(mock_board):
    mechanic = PlayerMechanics()
    player = mock_board.player()
    player.state.position.x = 100
    player.state.position.y = 100
    player.state.goal = None
    
    payload = DevicePayload(
        world=WorldPayload(
            intention=None, 
            goals=[PlayerGoals.RIGHT, PlayerGoals.DOWN]
        ),
        menu=MenuPayload()
    )
    
    mechanic.update(mock_board, 0.16, MagicMock(), payload)
    
    assert player.state.goal is not None
    assert player.state.goal.position.x == 110
    assert player.state.goal.position.y == 110
    assert player.state.mutators.triggers.animated is True