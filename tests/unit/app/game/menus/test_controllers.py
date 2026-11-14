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
from app.game.menus.controllers import (
    DisplayController,
    InventoryController,
    LoadController,
    MainController,
    OptionsController,
    PauseController,
    ScrollController,
)
from app.models.menus import (
    MenuEvent,
    StateEvent,
    TerminalEvent,
    UpdateEvent,
)
from app.models.state import PaneState
from app.static.semantics import (
    Hands,
    ItemPalette,
    Menus,
    Statuses,
    ToolPalette,
    UtilityPalette,
    WeaponPalette,
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
def test_inventory_controller_equipment_slotting(
    mock_menu,
    mock_board,
    mock_bus: deque,
):
    """
    Verifies selecting occupied weapon, tool, and utility Gizmo slots in Menu: Equipment
    mutates player.state.slots.equipment in-place without emitting UpdateEvents (Bug B019).
    """
    player = mock_board.player()
    player.state.inventory.sheathe = [WeaponPalette.SPEAR.value]
    player.state.inventory.belt = [ToolPalette.PICKAXE.value]
    player.state.inventory.bag = [UtilityPalette.LANTERN.value]
    player.state.slots.equipment.weapon = None
    player.state.slots.equipment.tool = None
    player.state.slots.equipment.utility = None

    eq_menu = mock_menu(Menus.EQUIPMENT.value)
    ctrl = eq_menu.controller
    assert isinstance(ctrl, InventoryController)

    ctrl.select("equipment-weapons-grid-slot-0", eq_menu, mock_board, mock_bus)
    assert player.state.slots.equipment.weapon == WeaponPalette.SPEAR.value
    assert eq_menu.widgets["equipment-weapon-icon"].state.icon == WeaponPalette.SPEAR.value

    ctrl.select("equipment-tools-grid-slot-0", eq_menu, mock_board, mock_bus)
    assert player.state.slots.equipment.tool == ToolPalette.PICKAXE.value
    assert eq_menu.widgets["equipment-tool-icon"].state.icon == ToolPalette.PICKAXE.value

    ctrl.select("equipment-utilities-grid-slot-0", eq_menu, mock_board, mock_bus)
    assert player.state.slots.equipment.utility == UtilityPalette.LANTERN.value
    assert eq_menu.widgets["equipment-utility-icon"].state.icon == UtilityPalette.LANTERN.value

    assert len(mock_bus) == 0


@pytest.mark.workflow_traversal
@pytest.mark.workflow_inventory
def test_inventory_controller_pouch_dual_grip_selection(
    mock_menu,
    mock_board,
    mock_bus: deque,
):
    """
    Verifies dual-grip target latching and item assignment in Menu: Pouch.
    """
    player = mock_board.player()
    player.state.inventory.pouch = {
        ItemPalette.BOMB.value: 5,
        ItemPalette.ARROW.value: 20,
    }
    player.state.slots.grip.right = None
    player.state.slots.grip.left = None

    pouch_menu = mock_menu(Menus.POUCH.value)
    ctrl = pouch_menu.controller
    assert isinstance(ctrl, InventoryController)

    # 1. Default active_grip is 'right'; selecting slot 0 equips to right grip
    assert pouch_menu.context.active_grip == Hands.RIGHT.value
    ctrl.select("inventory-pouch-grid-slot-0", pouch_menu, mock_board, mock_bus)
    assert player.state.slots.grip.right == ItemPalette.BOMB.value
    assert pouch_menu.widgets["pouch-grip-right-icon"].state.icon == ItemPalette.BOMB.value

    # 2. Selecting left grip button switches active_grip to 'left' and updates button statuses
    pouch_menu.focus = "pouch-grip-left-slot"
    ctrl.select("pouch-grip-left-slot", pouch_menu, mock_board, mock_bus)
    assert pouch_menu.context.active_grip == Hands.LEFT.value
    assert pouch_menu.widgets["pouch-grip-left-slot"].state.status == Statuses.SELECTED.value
    assert pouch_menu.widgets["pouch-grip-right-slot"].state.status == Statuses.IDLE.value

    # 3. Selecting slot 1 equips to left grip while preserving right grip
    pouch_menu.focus = "inventory-pouch-grid-slot-1"
    ctrl.select("inventory-pouch-grid-slot-1", pouch_menu, mock_board, mock_bus)
    assert player.state.slots.grip.left == ItemPalette.ARROW.value
    assert player.state.slots.grip.right == ItemPalette.BOMB.value
    assert pouch_menu.widgets["pouch-grip-left-icon"].state.icon == ItemPalette.ARROW.value
    assert len(mock_bus) == 0


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