"""
@domain.test
@test.unit
@app.menu
@menu.controller

# Ontology: Tests - tests.unit.app.game.menus.test_controllers

Unit tests for MenuController implementations.
"""
# Standard Libraries
from collections import deque

# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.game.menus.bindings import SelectBinding
from app.game.menus.controllers import (
    DisplayController,
    InventoryController,
    LoadController,
    MainController,
    OptionsController,
    PauseController,
    ScrollController,
)
from app.models.config.menus import SelectTarget
from app.models.menus import (
    MenuEvent,
    StateEvent,
    TerminalEvent,
    UpdateEvent,
)
from app.models.state import PaneState
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Menus,
    Selections,
    Statuses,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_menu,
    pytest.mark.menu_controller,
]

# ---------------------------------------------------------------------------


@pytest.mark.workflow_traversal
def test_main_controller_select_new_load_and_submenu(
    mock_menu,
    mock_board,
    mock_bus: deque,
):
    menu = mock_menu(Menus.MAIN.value)
    ctrl = menu.controller
    assert isinstance(ctrl, MainController)

    ctrl.select("new-game", menu, mock_board, mock_bus)
    assert len(mock_bus) == 2
    assert isinstance(mock_bus.popleft(), TerminalEvent)
    state_ev = mock_bus.popleft()
    assert isinstance(state_ev, StateEvent)
    assert state_ev.id == settings.NEW_BOARD

    ctrl.select("load-game", menu, mock_board, mock_bus)
    assert len(mock_bus) == 2
    assert isinstance(mock_bus.popleft(), TerminalEvent)
    state_ev = mock_bus.popleft()
    assert isinstance(state_ev, StateEvent)
    assert state_ev.id == settings.NEW_BOARD

    ctrl.select("options-menu", menu, mock_board, mock_bus)
    assert len(mock_bus) == 1
    menu_ev = mock_bus.popleft()
    assert isinstance(menu_ev, MenuEvent)
    assert menu_ev.id == Menus.OPTIONS.value


@pytest.mark.workflow_hydration
def test_main_controller_update_prewarms_registry(
    mock_menu,
    mock_board,
    mock_bus: deque,
):
    menu = mock_menu(Menus.MAIN.value)
    menu.controller.update(menu, mock_board, mock_bus)
    assert menu.context.registry is not None


@pytest.mark.workflow_hydration
def test_load_controller_update_lifecycle(
    mock_menu,
    mock_board,
    mock_migrator,
    mock_bus: deque,
):
    load_menu = mock_menu(Menus.LOAD.value)
    ctrl = load_menu.controller
    assert isinstance(ctrl, LoadController)

    # Guard clause when board is already marked loaded
    mock_board.loaded = True
    ctrl.update(load_menu, mock_board, mock_bus)
    assert len(mock_bus) == 0

    # Active hydration step through completion
    mock_board.loaded = False
    mock_migrator.target = settings.NEW_BOARD
    while not mock_board.loaded:
        ctrl.update(load_menu, mock_board, mock_bus)

    assert mock_board.loaded is True
    assert len(mock_bus) == 1
    assert isinstance(mock_bus.popleft(), TerminalEvent)


@pytest.mark.workflow_traversal
def test_scroll_controller_open_and_select(
    mock_menu,
    mock_board,
    mock_bus: deque,
):
    dialogue_menu = mock_menu(Menus.DIALOGUE.value)
    ctrl = dialogue_menu.controller
    assert isinstance(ctrl, ScrollController)

    speech_pane = dialogue_menu.widgets["character-speech"]
    assert isinstance(speech_pane.state, PaneState)
    speech_pane.state.content_function = lambda: ["Page 1", "Page 2"]
    speech_pane.state.pageindex = 0

    ctrl.open(dialogue_menu, mock_board, mock_bus)
    assert len(mock_bus) >= 1
    open_ev = mock_bus.popleft()
    assert isinstance(open_ev, UpdateEvent)
    mock_bus.clear()

    ctrl.select("text-scroll-down", dialogue_menu, mock_board, mock_bus)
    assert speech_pane.state.pageindex == 1
    down_ev = mock_bus.popleft()
    assert isinstance(down_ev, UpdateEvent)
    assert down_ev.content == "Page 2"

    ctrl.select("text-scroll-up", dialogue_menu, mock_board, mock_bus)
    assert speech_pane.state.pageindex == 0
    up_ev = mock_bus.popleft()
    assert isinstance(up_ev, UpdateEvent)
    assert up_ev.content == "Page 1"


@pytest.mark.workflow_traversal
@pytest.mark.workflow_inventory
def test_inventory_controller_pagination_and_equip(
    mock_menu,
    mock_asset,
    mock_board,
    mock_bus: deque,
):
    inv_menu = mock_menu(Menus.INVENTORY.value)
    ctrl = inv_menu.controller
    assert isinstance(ctrl, InventoryController)

    grid_pane = inv_menu.widgets["inventory-pack-grid"]
    capacity = grid_pane.state.capacity
    columns = grid_pane.state.columns

    # Configure collection with (capacity + 1) items so the last slot is occupied at offset=0
    # and vacant after scrolling down by `columns`
    items = ["shortsword", "buckler", *[f"item-{i}" for i in range(capacity - 1)]]
    grid_pane.state.collection_function = lambda: items
    grid_pane.state.offset = 0

    # Ensure scroll-down and scroll-up control buttons targeting `inventory-pack-grid` exist
    if "inventory-scroll-down" not in inv_menu.widgets:
        btn_down = mock_asset(
            AssetCategories.WIDGETS.value,
            AssetInstances.BUTTONS.value,
            id="arrow-down",
        )
        btn_down.taxonomy.name = "inventory-scroll-down"
        inv_menu.widgets["inventory-scroll-down"] = btn_down
    inv_menu.widgets["inventory-scroll-down"].binding = SelectBinding(
        target=SelectTarget(
            selection=Selections.SCROLLDOWN.value,
            selector="inventory-pack-grid",
        ),
        context=inv_menu.context,
    )

    if "inventory-scroll-up" not in inv_menu.widgets:
        btn_up = mock_asset(
            AssetCategories.WIDGETS.value,
            AssetInstances.BUTTONS.value,
            id="arrow-up",
        )
        btn_up.taxonomy.name = "inventory-scroll-up"
        inv_menu.widgets["inventory-scroll-up"] = btn_up
    inv_menu.widgets["inventory-scroll-up"].binding = SelectBinding(
        target=SelectTarget(
            selection=Selections.SCROLLUP.value,
            selector="inventory-pack-grid",
        ),
        context=inv_menu.context,
    )

    # 1. Slot selection equips matching weapon onto player state
    player = mock_board.player()
    ctrl.select("inventory-pack-grid-slot-0", inv_menu, mock_board, mock_bus)
    assert player.state.inventory.equipment.weapon == "shortsword"
    equip_ev = mock_bus.popleft()
    assert isinstance(equip_ev, UpdateEvent)
    assert equip_ev.content == "shortsword"

    # 2. Focus on last slot, then scroll down: offset advances by `columns` and focus recovers to slot 0
    last_slot_name = f"inventory-pack-grid-slot-{capacity - 1}"
    inv_menu.focus = last_slot_name
    inv_menu.widgets[last_slot_name].state.status = Statuses.ACTIVE.value
    inv_menu.widgets["inventory-pack-grid-slot-0"].state.status = Statuses.IDLE.value

    ctrl.select("inventory-scroll-down", inv_menu, mock_board, mock_bus)
    assert grid_pane.state.offset == columns
    assert inv_menu.focus == "inventory-pack-grid-slot-0"
    assert inv_menu.widgets[last_slot_name].state.status == Statuses.IDLE.value
    assert inv_menu.widgets["inventory-pack-grid-slot-0"].state.status == Statuses.ACTIVE.value
    scroll_down_ev = mock_bus.popleft()
    assert isinstance(scroll_down_ev, UpdateEvent)
    assert scroll_down_ev.content == str(columns)

    # 3. Scroll up restores collection window offset back to 0
    ctrl.select("inventory-scroll-up", inv_menu, mock_board, mock_bus)
    assert grid_pane.state.offset == 0
    scroll_up_ev = mock_bus.popleft()
    assert isinstance(scroll_up_ev, UpdateEvent)
    assert scroll_up_ev.content == "0"

@pytest.mark.workflow_traversal
def test_pause_controller_save_load_submenu_and_quit(
    mock_menu,
    mock_board,
    mock_bus: deque,
):
    pause_menu = mock_menu(Menus.PAUSE.value)
    ctrl = pause_menu.controller
    assert isinstance(ctrl, PauseController)

    ctrl.open(pause_menu, mock_board, mock_bus)

    by_selection = {
        w.binding.selection: name
        for name, w in pause_menu.widgets.items()
        if w.binding and hasattr(w.binding, "selection")
    }

    if "save" in by_selection:
        ctrl.select(by_selection["save"], pause_menu, mock_board, mock_bus)

    if "menu" in by_selection:
        ctrl.select(by_selection["menu"], pause_menu, mock_board, mock_bus)
        ev = mock_bus.popleft()
        assert isinstance(ev, MenuEvent)

    if "load" in by_selection:
        ctrl.select(by_selection["load"], pause_menu, mock_board, mock_bus)
        assert isinstance(mock_bus.popleft(), TerminalEvent)
        assert isinstance(mock_bus.popleft(), StateEvent)

    if "quit" in by_selection:
        ctrl.select(by_selection["quit"], pause_menu, mock_board, mock_bus)
        ev = mock_bus.popleft()
        assert isinstance(ev, MenuEvent)
        assert ev.id == Menus.MAIN.value

    ctrl.close(pause_menu, mock_board, mock_bus)


def test_display_controller_noop_lifecycle(mock_menu, mock_board, mock_bus: deque):
    view_menu = mock_menu(Menus.VIEW.value)
    ctrl = view_menu.controller
    assert isinstance(ctrl, DisplayController)

    ctrl.open(view_menu, mock_board, mock_bus)
    ctrl.update(view_menu, mock_board, mock_bus)
    ctrl.select("weapon-slot", view_menu, mock_board, mock_bus)
    ctrl.close(view_menu, mock_board, mock_bus)
    assert len(mock_bus) == 0