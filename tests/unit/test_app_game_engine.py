# /home/grant/Projects/ontology/tests/unit/test_app_game_engine.py

"""
# Ontology: tests.unit.test_app_game_engine

Unit tests for the core Engine loop and time management.
"""
from unittest.mock import Mock, patch
from app.game.engine import Engine

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

    # Break the Engine's while loop by changing board.loaded to False during the first update
    def mock_update(*args, **kwargs):
        board.loaded = False

    mechanic.update.side_effect = mock_update

    engine = Engine(
        board=board, 
        screens={"0": screen}, 
        core=[mechanic], 
        world=[], 
        provider=Mock()
    )
    
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