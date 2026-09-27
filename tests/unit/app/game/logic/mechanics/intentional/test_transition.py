"""
# Ontology: tests.unit.app.game.logic.mechanics.intentional.test_transition

Unit tests for TransitionMechanics.
"""
# Standard Libraries
import collections

# External Libraries
import pytest

# Application Libraries
from app.game.engine import Engine
from app.game.logic.mechanics import TransitionMechanics
from app.config.enums import (
    Intentions, 
    Actions, 
    Directions
)

# Cython Libraries
from libs.core.models import Position


def get_mechanic(engine: Engine, cls: type) -> TransitionMechanics:
    """Retrieves a mechanic by class from the engine pipeline."""
    return next((m for m in engine.core + engine.world if isinstance(m, cls)), None)


@pytest.mark.intentions
def test_transition_update_evaluates_executor(mock_engine):
    mechanic = get_mechanic(mock_engine, TransitionMechanics)
    board = mock_engine.board
    
    # Setup sprite state
    sprite = board.instances("sprites")[0]  # 'jasilynn'
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.position = Position(x=10, y=10)
    
    # Mutate health to trigger real ISL transition to 'attack'
    sprite.state.meters.health.current = 40
    
    # Run loop
    bus = collections.deque()
    mechanic.update(board, 0.16, bus, None)
    
    # Assert ISL logic mutated the intention
    assert sprite.state.intention == Intentions.ATTACK.value
    
    # Assert AnimationMap correctly resolved the intention action 
    # (ATTACK without weapon defaults to CAST)
    assert sprite.state.animation.action == Actions.CAST.value


@pytest.mark.intentions
def test_transition_update_skips_without_executor(mock_engine):
    mechanic = get_mechanic(mock_engine, TransitionMechanics)
    mechanic.executor = None
    board = mock_engine.board
    
    sprite = board.instances("sprites")[0]
    sprite.state.intention = Intentions.IDLE.value
    sprite.state.meters.health.current = 40  # Would normally transition to attack
    
    bus = collections.deque()
    mechanic.update(board, 0.16, bus, None)
    
    # Should safely skip ISL evaluation and remain IDLE
    assert sprite.state.intention == Intentions.IDLE.value
    assert sprite.state.animation.action == Actions.WALK.value