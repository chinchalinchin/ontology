"""
# Ontology: tests.unit.test_app_game_menus_handlers

Test suite covering Event Routing Strategy implementations.
"""
import pytest
import collections
from unittest.mock import MagicMock

from app.config.enums import Menus
from app.game.menus.events import (
    MenuEvent,
    StateEvent,
    TerminalEvent,
    UpdateEvent,
    EventContext
)
from app.game.menus.contexts import MenuContext as BaseMenuContext, LoadContext, ViewContext
from app.game.menus.handlers import (
    MenuEventHandler,
    StateEventHandler,
    TerminalEventHandler,
    UpdateEventHandler
)

@pytest.fixture
def mock_event_context():
    context = EventContext(
        board=MagicMock(),
        screens={'0': MagicMock()},
        provider=MagicMock(),
        bus=collections.deque()
    )
    # Default common attributes
    context.board.configurations = MagicMock()
    context.board.player.return_value = MagicMock(state=MagicMock(layer='0'))
    context.board.loaded = True
    context.board.menus = []
    
    return context

def test_menu_event_handler(mock_event_context):
    handler = MenuEventHandler()
    event = MenuEvent(id="test_menu", context=BaseMenuContext())
    
    mock_event_context.board.configurations.menus.get.return_value = {"config": "mocked"}
    
    mock_menu = MagicMock()
    mock_menu.widgets = {
        'test_widget': MagicMock(state=MagicMock(canvas=True, current=MagicMock(return_value="text")))
    }
    mock_event_context.provider.unpack.return_value = mock_menu
    
    handler.handle(event, mock_event_context)
    
    assert mock_event_context.board.paused is True
    assert mock_menu in mock_event_context.board.menus
    mock_event_context.screens['0'].stamp.assert_called_once()

def test_state_event_handler(mock_event_context):
    handler = StateEventHandler()
    event = StateEvent(id="world-02")
    
    handler.handle(event, mock_event_context)
    
    assert mock_event_context.board.migrator.target == "world-02"
    assert len(mock_event_context.bus) == 1
    
    queued_event = mock_event_context.bus.popleft()
    assert isinstance(queued_event, MenuEvent)
    assert queued_event.id == Menus.LOAD.value
    assert isinstance(queued_event.context, LoadContext)

def test_terminal_event_handler_popping_standard_menu(mock_event_context):
    handler = TerminalEventHandler()
    mock_menu = MagicMock(id="standard_menu")
    mock_event_context.board.menus = [mock_menu]
    
    handler.handle(TerminalEvent(), mock_event_context)
    
    # Assert menu was popped and board was unpaused
    assert len(mock_event_context.board.menus) == 0
    assert mock_event_context.board.paused is False

def test_terminal_event_handler_popping_load_menu(mock_event_context):
    handler = TerminalEventHandler()
    mock_menu = MagicMock(id=Menus.LOAD.value)
    mock_event_context.board.menus = [mock_menu]
    
    mock_hud = MagicMock()
    mock_event_context.provider.unpack.return_value = mock_hud
    
    handler.handle(TerminalEvent(), mock_event_context)
    
    # Assert the HUD overlay was constructed and injected when Loading finishes
    mock_event_context.provider.unpack.assert_called_once()
    mock_event_context.board.set_overlays.assert_called_once_with([mock_hud])

def test_update_event_handler(mock_event_context):
    handler = UpdateEventHandler()
    mock_widget = MagicMock()
    event = UpdateEvent(widget=mock_widget, content="New Status!")
    
    handler.handle(event, mock_event_context)
    
    # Assert the VRAM stamp was directly executed against the correct screen
    mock_event_context.screens['0'].stamp.assert_called_once_with(mock_widget, "New Status!")