"""
# Ontology: tests.unit.test_app_game_menus_controllers
"""
# Standard Libraries
from unittest.mock import MagicMock
from collections import deque

# Application Libraries
from app.config.enums import (
    Selections,
    Statuses
)
from app.assets.base import Taxonomy
from app.game.menus.controllers import (
    InventoryController,
    MainController,
    LoadController,
    ScrollController
)
from app.game.menus.contexts import (
    MainContext, 
    LoadContext
)
from app.game.menus.core import (
    Menu, 
    Widget
)
from app.game.menus.events import (
    StateEvent, 
    TerminalEvent, 
    UpdateEvent
)
from app.game.menus.bindings import SelectBinding
from app.models.state.widgets import (
    CollectionState, 
    TraversalState
)
from app.models.properties import WidgetProperties

# Cython Libraries
from libs.core.models import Dimensions

def test_main_controller_select():
    ctrl = MainController()
    
    mock_widget_new = MagicMock(spec=Widget)
    mock_widget_new.binding = SelectBinding(target={'selection': Selections.NEW.value}, context={})
    
    mock_widget_load = MagicMock(spec=Widget)
    mock_widget_load.binding = SelectBinding(target={'selection': Selections.LOAD.value}, context={})
    
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
    menu.context = MainContext(registry=mock_registry)
    
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
    
    mock_menu.context = LoadContext(
        registry=mock_registry,
        screens=mock_screens,
        screensize=MagicMock()
    )
    
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
    mock_menu.context = LoadContext(
        registry=mock_registry,
        screens={"0": MagicMock()},
        screensize=MagicMock()
    )
    
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
    mock_btn_down.binding = SelectBinding(target={'selection': Selections.SCROLLDOWN.value, 'selector': "text_page"}, context={})
    
    mock_btn_up = MagicMock(spec=Widget)
    mock_btn_up.binding = SelectBinding(target={'selection': Selections.SCROLLUP.value, 'selector': "text_page"}, context={})
    
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

def test_inventory_controller_pagination():
    controller = InventoryController()
    bus = deque()

    col_state = CollectionState(
        collection_function=lambda: [f"item-{i}" for i in range(12)],
        capacity=8,
        columns=4,
        offset=0
    )
    grid_pane = Widget(
        taxonomy=Taxonomy("transparent-slot", "inventory-pack-grid", "widgets", "panes"),
        properties=WidgetProperties(dimensions=Dimensions(175, 85)),
        state=col_state,
        frame=None,
        animation=None,
        binding=None
    )

    btn_down = Widget(
        taxonomy=Taxonomy("arrow-down", "inventory-scroll-down", "widgets", "buttons"),
        properties=WidgetProperties(dimensions=Dimensions(24, 24)),
        state=TraversalState(id="arrow-down", status=Statuses.IDLE.value),
        frame=None,
        animation=None,
        binding=SelectBinding(
            target={'selection': Selections.SCROLLDOWN.value, 'selector': 'inventory-pack-grid'},
            context={}
        )
    )
    btn_up = Widget(
        taxonomy=Taxonomy("arrow-up", "inventory-scroll-up", "widgets", "buttons"),
        properties=WidgetProperties(dimensions=Dimensions(24, 24)),
        state=TraversalState(id="arrow-up", status=Statuses.IDLE.value),
        frame=None,
        animation=None,
        binding=SelectBinding(
            target={'selection': Selections.SCROLLUP.value, 'selector': 'inventory-pack-grid'},
            context={}
        )
    )

    menu = MagicMock(spec=Menu)
    menu.focus = "inventory-scroll-down"
    menu.widgets = {
        "inventory-pack-grid": grid_pane,
        "inventory-scroll-down": btn_down,
        "inventory-scroll-up": btn_up
    }

    controller.select("inventory-scroll-down", menu, MagicMock(), bus)
    assert col_state.offset == 4
    assert len(bus) == 1
    event = bus.popleft()
    assert isinstance(event, UpdateEvent)
    assert event.content == "4"

    controller.select("inventory-scroll-up", menu, MagicMock(), bus)
    assert col_state.offset == 0
    assert len(bus) == 1


def test_inventory_controller_slot_equip():
    controller = InventoryController()
    bus = deque()

    col_state = CollectionState(
        collection_function=lambda: ["shortsword"],
        capacity=8,
        columns=4,
        offset=0
    )
    grid_pane = Widget(
        taxonomy=Taxonomy("transparent-slot", "inventory-pack-grid", "widgets", "panes"),
        properties=WidgetProperties(dimensions=Dimensions(175, 85)),
        state=col_state,
        frame=None,
        animation=None,
        binding=None
    )

    slot_btn = Widget(
        taxonomy=Taxonomy("slot", "inventory-pack-grid-slot-0", "widgets", "buttons"),
        properties=WidgetProperties(dimensions=Dimensions(40, 40)),
        state=TraversalState(id="slot", status=Statuses.ACTIVE.value),
        frame=None,
        animation=None,
        binding=SelectBinding(
            target={'selection': Selections.SLOT.value, 'selector': 'inventory-pack-grid', 'index': '0'},
            context={}
        )
    )

    board = MagicMock()
    mock_player = MagicMock()
    board.player.return_value = mock_player
    board.equipment.weapons = {"shortsword": MagicMock()}

    menu = MagicMock(spec=Menu)
    menu.widgets = {
        "inventory-pack-grid": grid_pane,
        "inventory-pack-grid-slot-0": slot_btn
    }

    controller.select("inventory-pack-grid-slot-0", menu, board, bus)

    assert mock_player.state.inventory.equipment.weapon == "shortsword"
    assert len(bus) == 1
    event = bus.popleft()
    assert isinstance(event, UpdateEvent)
    assert event.content == "shortsword"


def test_inventory_controller_focus_recovery():
    controller = InventoryController()
    bus = deque()

    # 10 items: at offset 0, slot 7 (index 7) is occupied; at offset 4, slot 7 (index 11) is vacant
    col_state = CollectionState(
        collection_function=lambda: [f"item-{i}" for i in range(10)],
        capacity=8,
        columns=4,
        offset=0
    )
    grid_pane = Widget(
        taxonomy=Taxonomy("transparent-slot", "inventory-pack-grid", "widgets", "panes"),
        properties=WidgetProperties(dimensions=Dimensions(175, 85)),
        state=col_state,
        frame=None,
        animation=None,
        binding=None
    )

    btn_slot_7 = Widget(
        taxonomy=Taxonomy("slot", "inventory-pack-grid-slot-7", "widgets", "buttons"),
        properties=WidgetProperties(dimensions=Dimensions(40, 40)),
        state=TraversalState(id="slot", status=Statuses.ACTIVE.value),
        frame=None,
        animation=None,
        binding=SelectBinding(
            target={'selection': Selections.SLOT.value, 'selector': 'inventory-pack-grid', 'index': '7'},
            context={}
        )
    )
    btn_slot_0 = Widget(
        taxonomy=Taxonomy("slot", "inventory-pack-grid-slot-0", "widgets", "buttons"),
        properties=WidgetProperties(dimensions=Dimensions(40, 40)),
        state=TraversalState(id="slot", status=Statuses.IDLE.value),
        frame=None,
        animation=None,
        binding=SelectBinding(
            target={'selection': Selections.SLOT.value, 'selector': 'inventory-pack-grid', 'index': '0'},
            context={}
        )
    )
    btn_down = Widget(
        taxonomy=Taxonomy("arrow-down", "inventory-scroll-down", "widgets", "buttons"),
        properties=WidgetProperties(dimensions=Dimensions(24, 24)),
        state=TraversalState(id="arrow-down", status=Statuses.IDLE.value),
        frame=None,
        animation=None,
        binding=SelectBinding(
            target={'selection': Selections.SCROLLDOWN.value, 'selector': 'inventory-pack-grid'},
            context={}
        )
    )

    menu = MagicMock(spec=Menu)
    menu.focus = "inventory-pack-grid-slot-7"
    menu.widgets = {
        "inventory-pack-grid": grid_pane,
        "inventory-pack-grid-slot-7": btn_slot_7,
        "inventory-pack-grid-slot-0": btn_slot_0,
        "inventory-scroll-down": btn_down
    }

    controller.select("inventory-scroll-down", menu, MagicMock(), bus)

    assert col_state.offset == 4
    assert menu.focus == "inventory-pack-grid-slot-0"
    assert btn_slot_7.state.status == Statuses.IDLE.value
    assert btn_slot_0.state.status == Statuses.ACTIVE.value