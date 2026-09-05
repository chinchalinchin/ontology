"""
# Ontology: tests.unit.test_app_game_menus_controllers
"""
from unittest.mock import MagicMock
from collections import deque

from app.game.menus.controllers.main import MainController
from app.game.menus.controllers.load import LoadController
from app.game.menus.controllers.scroll import ScrollController
from app.game.menus.core import Menu, Widget, Binding
from app.game.menus.events import StateEvent, TerminalEvent, UpdateEvent
from app.config.enums import Selections

def test_main_controller_select():
    ctrl = MainController()
    
    mock_widget_new = MagicMock(spec=Widget)
    mock_widget_new.binding = Binding(selection=Selections.NEW.value)
    
    mock_widget_load = MagicMock(spec=Widget)
    mock_widget_load.binding = Binding(selection=Selections.LOAD.value)
    
    menu = MagicMock(spec=Menu)
    menu.widgets = {"btn-new": mock_widget_new, "btn-load": mock_widget_load}
    
    bus = deque()
    board = MagicMock()
    
    ctrl.select("btn-new", menu, board, bus)
    
    assert len(bus) == 2
    event1 = bus.popleft()
    event2 = bus.popleft()
    assert isinstance(event1, TerminalEvent)
    assert isinstance(event2, StateEvent)
    assert event2.id == 'world-01'
    
    ctrl.select("btn-load", menu, board, bus)
    
    assert len(bus) == 2
    event1 = bus.popleft()
    event2 = bus.popleft()
    assert isinstance(event1, TerminalEvent)
    assert isinstance(event2, StateEvent)
    assert event2.id == 'world-01'

def test_main_controller_update():
    ctrl = MainController()
    menu = MagicMock(spec=Menu)
    mock_registry = MagicMock()
    menu.context = {'registry': mock_registry}
    
    ctrl.update(menu, MagicMock(), deque())
    
    # Main menu idle loop should prewarm the registry textures
    mock_registry.prewarm.assert_called_once_with(budget_ms=1)

def test_load_controller_update():
    ctrl = LoadController()
    
    mock_board = MagicMock()
    mock_board.loaded = False  # Explicitly set to False to bypass the new guard clause
    mock_migrator = MagicMock()
    mock_migrator.target = "world-01"
    mock_migrator.step.return_value = True # Migrator is fully hydrated
    mock_board.migrator = mock_migrator
    mock_board.layers.return_value = ["0"]
    mock_board.size.return_value = [MagicMock()]
    
    mock_menu = MagicMock(spec=Menu)
    mock_registry = MagicMock()
    mock_registry.prewarm.return_value = True # Registry is fully loaded
    
    mock_screen = MagicMock()
    mock_screens = {"0": mock_screen}
    
    mock_menu.context = {
        'registry': mock_registry,
        'screens': mock_screens,
        'screensize': MagicMock()
    }
    
    bus = deque()
    
    ctrl.update(mock_menu, mock_board, bus)
    
    mock_migrator.step.assert_called_once()
    mock_registry.prewarm.assert_called_once()
    
    # 100% hydration should trigger a full canvas reallocation
    mock_screen.rebake.assert_called_once()
    assert mock_board.loaded is True
    
    assert len(bus) == 1
    assert isinstance(bus[0], TerminalEvent)

def test_load_controller_update_not_done():
    ctrl = LoadController()
    
    mock_board = MagicMock()
    mock_migrator = MagicMock()
    mock_migrator.target = "world-01"
    mock_migrator.step.return_value = False # Migrator still time-slicing
    mock_board.migrator = mock_migrator
    
    mock_menu = MagicMock(spec=Menu)
    mock_registry = MagicMock()
    mock_registry.prewarm.return_value = False # Registry still parsing
    mock_menu.context = {
        'registry': mock_registry,
        'screens': {"0": MagicMock()}
    }
    
    bus = deque()
    
    ctrl.update(mock_menu, mock_board, bus)
    
    # Should not push terminal event or flip board state
    assert len(bus) == 0

def test_scroll_controller_select():
    ctrl = ScrollController()
    menu = MagicMock(spec=Menu)
    bus = deque()
    board = MagicMock()
    
    mock_page = MagicMock(spec=Widget)
    mock_page.state = MagicMock()
    mock_page.state.current.return_value = ["line 1", "line 2"]
    
    mock_btn_down = MagicMock(spec=Widget)
    mock_btn_down.binding = Binding(selection=Selections.SCROLLDOWN.value, selector="text_page")
    
    mock_btn_up = MagicMock(spec=Widget)
    mock_btn_up.binding = Binding(selection=Selections.SCROLLUP.value, selector="text_page")
    
    menu.widgets = {
        "text_page": mock_page,
        "btn_down": mock_btn_down,
        "btn_up": mock_btn_up
    }
    
    ctrl.select("btn_down", menu, board, bus)
    mock_page.state.scrolldown.assert_called_once()
    assert len(bus) == 1
    event = bus.popleft()
    assert isinstance(event, UpdateEvent)
    
    ctrl.select("btn_up", menu, board, bus)
    mock_page.state.scrollup.assert_called_once()
    assert len(bus) == 1
    event = bus.popleft()
    assert isinstance(event, UpdateEvent)