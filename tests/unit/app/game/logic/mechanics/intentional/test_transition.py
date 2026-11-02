"""
# Ontology: tests.unit.app.game.logic.mechanics.intentional.test_transition

Unit tests for TransitionMechanics.
"""
# Standard Libraries
import collections

# External Libraries
import pytest

# Application Libraries
from app.game.logic.mechanics import TransitionMechanics
from app.static.semantics import (
    AssetInstances,
    Intentions, 
    Actions,
    Mechanics
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.workflow_intentions,
    pytest.mark.workflow_transitions
]

# -----------------------------------------------------

def test_transition_update_evaluates_executor(
    mock_mechanic,
    mock_bus,
    mock_board
):
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    
    # Setup sprite state
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]  # 'jasilynn'
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.position = Position(x=10, y=10)
    
    # Mutate health to trigger real ISL transition to 'attack'
    sprite.state.meters.health.current = 40
    
    # Run loop
    mechanic.update(mock_board, 0.16, mock_bus, None)
    
    # Assert ISL logic mutated the intention
    assert sprite.state.intention == Intentions.ATTACK.value
    
    # Assert AnimationMap correctly resolved the intention action 
    # (ATTACK without weapon defaults to CAST)
    assert sprite.state.animation.action == Actions.CAST.value


def test_transition_update_skips_without_executor(
    mock_mechanic,
    mock_bus,
    mock_board
):
    mechanic = mock_mechanic(Mechanics.TRANSITION.value)
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]

    sprite.state.intention = Intentions.IDLE.value
    sprite.state.meters.health.current = 40  # Would normally transition to attack
    
    mechanic.update(mock_board, 0.16, mock_bus, None)
    
    # Should safely skip ISL evaluation and remain IDLE
    assert sprite.state.intention == Intentions.IDLE.value
    assert sprite.state.animation.action == Actions.WALK.value