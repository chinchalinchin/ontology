"""
# Ontology: tests.unit.app.game.test_engine

Unit tests for the core Engine loop and time management.
"""
# Standard Libraries
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraries
from app.game.engine import Engine
from app.game.logic.mechanics.base import Mechanic
from app.game.menus.events import Event
from app.game.menus.handlers import EventHandler


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


class TerminatingMechanic(Mechanic):
    """
    Live Mechanic that toggles engine.running to False after its first execution.
    """
    def __init__(self, engine: Engine):
        super().__init__()
        self.engine = engine
        self.executed = False

    def update(self, board, delta, bus, payload) -> None:
        self.executed = True
        self.engine.running = False


class SpyEventHandler(EventHandler):
    """
    Concrete event handler to record dispatched events during drain cycles.
    """
    def __init__(self):
        self.handled_events = []
        self.handled_contexts = []

    def handle(self, event, context) -> None:
        self.handled_events.append(event)
        self.handled_contexts.append(context)


class SampleEvent(Event):
    pass


# ---------------------------------------------------------------------------
# --------------------------------------------------------------------- TESTS

@pytest.mark.main
def test_engine_time():
    """Test the static time method returns a float from perf_counter."""
    with patch('time.perf_counter', return_value=123.45):
        assert Engine.time() == 123.45


@pytest.mark.main
def test_engine_start(mock_engine_core):
    """
    Ensure the engine loop executes mechanics, renders the screen, 
    and handles pacing correctly using live components and stubbed rendering.
    """
    mock_engine_core.board.loaded = True
    mock_engine_core.board.paused = False

    mechanic = TerminatingMechanic(mock_engine_core)
    mock_engine_core.core = [mechanic]

    screen = mock_engine_core.screens["0"]

    with patch.object(Engine, 'time', side_effect=IncrementalTime(step=0.017)):
        with patch('time.sleep'):
            mock_engine_core.start()

    assert mechanic.executed is True
    assert screen.cleared is True
    assert screen.presented is True
    assert len(screen.drawn_assets) > 0


@pytest.mark.main
def test_engine_drain_routes_events_to_handlers(mock_engine_core):
    """
    Validates EventBus draining and strategy dispatch to concrete handlers.
    """
    spy_handler = SpyEventHandler()
    mock_engine_core.handlers[SampleEvent] = spy_handler

    event = SampleEvent()
    mock_engine_core.bus.append(event)

    mock_engine_core._drain()

    assert len(mock_engine_core.bus) == 0
    assert len(spy_handler.handled_events) == 1
    assert spy_handler.handled_events[0] is event
    assert spy_handler.handled_contexts[0] == mock_engine_core.context