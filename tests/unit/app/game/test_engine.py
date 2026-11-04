"""
@domain.test
@test.unit
@app.core
@app.component
@workflow.main

# Ontology: Tests - tests.unit.app.game.test_engine

Unit tests for the core Engine loop and time management.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.engine import Engine
from app.game.logic.mechanics.core.animation import AnimationMechanics
from app.game.logic.mechanics.intentional.player import PlayerMechanics
from app.game.menus.contexts import PauseContext
from app.game.menus.events import (
    Event,
    MenuEvent,
    TerminalEvent,
)
from app.static.semantics import (
    Intentions,
    Menus,
    PlayerGoals,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_core,
    pytest.mark.app_component,
    pytest.mark.workflow_main,
]

# ---------------------------------------------------------------------------


def test_engine_time():
    """Test the static time method returns a monotonic float from perf_counter."""
    t1 = Engine.time()
    t2 = Engine.time()
    assert isinstance(t1, float)
    assert t2 >= t1


def test_engine_start(mock_engine: Engine, mock_render, monkeypatch):
    """
    Ensure the engine loop executes live core and world mechanics, renders the screen,
    and exits cleanly once a full fixed-timestep update and telemetry cycle complete.
    """
    mock_engine.board.loaded = True
    mock_engine.board.paused = False

    original_telemetry = mock_engine._telemetry

    def _terminating_telemetry(frames: int, updates: int, start: float, ticks: int = 1) -> bool:
        logged = original_telemetry(frames, updates, start, ticks=1)
        if updates >= 1:
            mock_engine.running = False
        return logged

    monkeypatch.setattr(mock_engine, "_telemetry", _terminating_telemetry)

    mock_engine.start(delta=0.001, spin=0.0001)

    assert mock_engine.running is False
    assert mock_render.clear.called
    assert mock_render.render.called
    assert mock_render.present.called
    rendered_assets = mock_render.render.call_args[0][2]
    assert len(rendered_assets) > 0


def test_engine_drain_routes_live_events_to_handlers(mock_engine: Engine):
    """
    Validates EventBus draining with live MenuEvent and TerminalEvent handlers.
    """
    pause_event = MenuEvent(
        id=Menus.PAUSE.value,
        context=PauseContext(board=mock_engine.board),
    )
    mock_engine.bus.append(pause_event)

    mock_engine._drain()

    assert len(mock_engine.bus) == 0
    assert len(mock_engine.board.menus) == 1
    assert mock_engine.board.paused is True

    mock_engine.bus.append(TerminalEvent())
    mock_engine._drain()

    assert len(mock_engine.bus) == 0
    assert len(mock_engine.board.menus) == 0
    assert mock_engine.board.paused is False


def test_engine_drain_unregistered_event_logs_warning(mock_engine: Engine):
    """
    Ensure draining an event with no registered handler empties the bus safely.
    """
    mock_engine.bus.append(Event())
    mock_engine._drain()
    assert len(mock_engine.bus) == 0


def test_engine_play_respects_paused_and_loaded_flags(
    mock_engine: Engine,
    mock_sdl,
):
    """
    Ensure _play skips world mechanics when paused or unloaded, and executes them when active.
    """
    player = mock_engine.board.player()
    player.state.intention = Intentions.IDLE.value

    # Press 'attack' (44) while board is unloaded
    mock_engine.board.loaded = False
    mock_engine.board.paused = False
    mock_sdl({44})
    mock_engine._play(0.016)
    assert player.state.intention == Intentions.IDLE.value

    # Release and press 'attack' (44) while board is loaded but paused
    mock_sdl(set())
    mock_engine.board.device.poll()
    mock_engine.board.loaded = True
    mock_engine.board.paused = True
    mock_sdl({44})
    mock_engine._play(0.016)
    assert player.state.intention == Intentions.IDLE.value

    # Release and press 'up' (26) while board is loaded and unpaused
    mock_sdl(set())
    mock_engine.board.device.poll()
    mock_engine.board.paused = False
    mock_sdl({26})
    mock_engine._play(0.016)
    assert player.state.mutators.triggers.animated is True


def test_engine_render_traps_unloaded_board_or_missing_player(
    mock_engine: Engine,
    mock_render,
):
    """
    Ensure _render bypasses world drawing and renders only the UI interface when
    the board is unloaded or no player is present.
    """
    mock_engine.board.loaded = False
    mock_render.reset_mock()

    mock_engine._render()

    assert mock_render.clear.called
    assert not mock_render.render.called
    assert mock_render.present.called


def test_engine_telemetry_interval(mock_engine: Engine):
    """
    Validate _telemetry returns True only on tick multiples and False otherwise.
    """
    start = Engine.time() - 1.0
    assert mock_engine._telemetry(frames=5, updates=5, start=start, ticks=10) is False
    assert mock_engine._telemetry(frames=10, updates=10, start=start, ticks=10) is True


def test_engine_get_mechanic(mock_engine: Engine):
    """
    Verify get_mechanic retrieves instantiated mechanics from core and world pipelines.
    """
    anim_mechanic = mock_engine.get_mechanic(AnimationMechanics)
    player_mechanic = mock_engine.get_mechanic(PlayerMechanics)

    assert isinstance(anim_mechanic, AnimationMechanics)
    assert isinstance(player_mechanic, PlayerMechanics)
    assert mock_engine.get_mechanic(dict) is None


def test_engine_stop_releases_resources(mock_engine: Engine):
    """
    Ensure stop() halts the engine, clears the event bus, destroys screen canvases,
    and wipes the board database.
    """
    mock_engine.running = True
    mock_engine.bus.append(Event())

    mock_engine.stop()

    assert mock_engine.running is False
    assert len(mock_engine.bus) == 0
    assert len(mock_engine.screens) == 0
    assert len(mock_engine.board.assets()) == 0