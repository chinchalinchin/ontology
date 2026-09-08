"""
# Ontology: tests.unit.test_app_game_engine

Unit tests for the core Engine loop and time management.
"""
from unittest.mock import Mock, MagicMock, patch
import pytest
from unittest.mock import MagicMock
from collections import deque

from app.game.engine import Engine
from app.game.menus.events import Event

class IncrementalTime:
    """
    Mock time generator to safely advance the engine's internal accumulator
    and spin-locks without causing infinite loops during unit testing.
    """
    def __init__(self, step: float = 0.017):
        self.t = 0.0
        self.step = step
        
    def __call__(self) -> float:
        self.t += self.step
        return self.t

def test_engine_time():
    """Test the static time method returns a float from perf_counter."""
    with patch('time.perf_counter', return_value=123.45):
        assert Engine.time() == 123.45

def test_engine_start():
    """
    Ensure the engine loop executes mechanics, renders the screen, 
    and handles pacing correctly.
    """
    board = Mock()
    board.loaded = True
    board.paused = False
    
    # Setup player for rendering context
    player_mock = Mock()
    player_mock.state.layer = "0"
    board.player.return_value = player_mock
    board.renderables.return_value = []
    
    screen = Mock()
    mechanic = Mock()

    # Pre-instantiate the Engine so our mock can mutate its state
    engine = Engine(
        board=board, 
        screens={"0": screen}, 
        core=[mechanic], 
        world=[], 
        provider=Mock()
    )

    # Break the Engine's while loop by changing engine.running to False during the first update
    def mock_update(*args, **kwargs):
        engine.running = False

    mechanic.update.side_effect = mock_update

    # Patch Engine.time to advance consistently, and mock time.sleep to avoid halting the test
    with patch.object(Engine, 'time', side_effect=IncrementalTime(step=0.017)):
        with patch('time.sleep') as mock_sleep:
            engine.start()

    # Assert Mechanic was updated
    mechanic.update.assert_called_once()
    
    # Assert Screen was drawn
    screen.draw.assert_called_once_with(
        [], 
        player_mock.state.position, 
        player_mock.dimensions
    )


def test_engine_drain_routes_events_to_handlers():
    # Setup dummy Engine
    mock_board = MagicMock()
    engine = Engine(board=mock_board, screens={}, core=[], world=[], provider=MagicMock())
    
    # Create a custom event and inject a mock handler into the Engine's router
    class DummyEvent(Event):
        pass
        
    mock_handler = MagicMock()
    engine.handlers[DummyEvent] = mock_handler
    
    # Put event on the bus
    engine.bus.append(DummyEvent())
    
    # Drain the bus
    engine._drain()
    
    # Verify the strategy successfully routed to our mock
    assert len(engine.bus) == 0
    mock_handler.handle.assert_called_once()
    assert isinstance(mock_handler.handle.call_args[0][0], DummyEvent)
    assert mock_handler.handle.call_args[0][1] == engine.event_context