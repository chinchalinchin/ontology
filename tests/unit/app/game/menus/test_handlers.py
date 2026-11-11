"""
@domain.test
@test.unit
@app.menu
@menu.handler

# Ontology: Tests - tests.unit.app.game.menus.test_handlers

Unit tests for Event Handler implementations.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.menus.core import EventData
from app.game.menus.handlers import (
    MenuEventHandler,
    SeasonEventHandler,
    StateEventHandler,
    TerminalEventHandler,
    UpdateEventHandler,
)
from app.models.menus import (
    LoadContext,
    MenuEvent,
    SeasonEvent,
    StateEvent,
    TerminalEvent,
    UpdateEvent,
)
from app.models.state import PaneState
from app.static.semantics import (
    Menus,
    Seasons,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_menu,
    pytest.mark.menu_handler,
]

# ---------------------------------------------------------------------------


@pytest.mark.workflow_rendering
def test_menu_event_handler_pushes_menu_and_stamps_canvases(
    mock_event_data: EventData,
    mock_menu_context,
    mock_render,
):
    handler = MenuEventHandler()
    event = MenuEvent(
        id=Menus.MAIN.value,
        context=mock_menu_context(Menus.MAIN.value),
    )

    mock_event_data.board.paused = False
    mock_event_data.board.menus.clear()

    handler.handle(event, mock_event_data)

    assert mock_event_data.board.paused is True
    assert len(mock_event_data.board.menus) == 1
    active_menu = mock_event_data.board.menus[-1]
    assert active_menu.id == Menus.MAIN.value
    assert any(
        isinstance(w.state, PaneState) and w.state.canvas is not None
        for w in active_menu.widgets.values()
    )
    mock_render.construct.assert_called()


def test_menu_event_handler_ignores_unknown_menu(
    mock_event_data: EventData,
    mock_menu_context,
):
    handler = MenuEventHandler()
    mock_event_data.board.paused = False
    mock_event_data.board.menus.clear()

    handler.handle(
        MenuEvent(id="nonexistent-menu", context=mock_menu_context()),
        mock_event_data,
    )

    assert mock_event_data.board.paused is False
    assert len(mock_event_data.board.menus) == 0


@pytest.mark.workflow_hydration
def test_state_event_handler_queues_load_menu(mock_event_data: EventData):
    handler = StateEventHandler()
    event = StateEvent(id="world-02")

    handler.handle(event, mock_event_data)

    assert mock_event_data.board.migrator.target == "world-02"
    assert len(mock_event_data.bus) == 1
    queued_event = mock_event_data.bus.popleft()
    assert isinstance(queued_event, MenuEvent)
    assert queued_event.id == Menus.LOAD.value
    assert isinstance(queued_event.context, LoadContext)


def test_terminal_event_handler_popping_load_menu_hydrates_hud_overlay(
    mock_event_data: EventData,
    mock_menu,
):
    handler = TerminalEventHandler()
    load_menu = mock_menu(Menus.LOAD.value)
    mock_event_data.board.menus = [load_menu]
    mock_event_data.board.overlays.clear()

    handler.handle(TerminalEvent(), mock_event_data)

    assert len(mock_event_data.board.menus) == 0
    assert len(mock_event_data.board.overlays) == 1
    assert mock_event_data.board.overlays[0].id == Menus.VIEW.value


@pytest.mark.workflow_rendering
def test_update_event_handler_restamps_pane_canvas(
    mock_event_data: EventData,
    mock_menu,
    mock_render,
):
    handler = UpdateEventHandler()
    dialogue_menu = mock_menu(Menus.DIALOGUE.value)
    speech_pane = dialogue_menu.widgets["character-speech"]
    mock_render.reset_mock()

    handler.handle(
        UpdateEvent(widget=speech_pane, content="Updated Dialogue Line"),
        mock_event_data,
    )

    mock_render.construct.assert_called_once()
    mock_render.write.assert_called_once()


@pytest.mark.workflow_seasons
def test_season_event_handler_reconstructs_screens_and_shorelines(
    mock_event_data: EventData,
    mock_render,
):
    handler = SeasonEventHandler()
    mock_event_data.board.calendar.season = Seasons.AUTUMN.value
    mock_render.reset_mock()

    handler.handle(SeasonEvent(), mock_event_data)

    mock_render.construct.assert_called()
    for shore in mock_event_data.board.shorelines():
        assert shore.state.season == Seasons.AUTUMN.value
        assert shore.state._keys is None