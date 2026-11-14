"""
@domain.test
@test.unit
@app.core
@app.mechanic
@app.menu

# Ontology: Tests - tests.unit.app.game.logic.mechanics.core.test_menu

Unit tests for the MenuMechanics implementation.
"""
# Standard Libraries
from collections import deque

# External Libraries
import pytest

# Application Libraries
from app.game.board import Board
from app.models.menus import (
    StateEvent,
    TerminalEvent,
)
from app.static.semantics import (
    DeviceContexts,
    Interactions,
    Mechanics,
    Menus,
    Statuses,
    Traversal,
    WeaponPalette,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_core,
    pytest.mark.app_mechanic,
    pytest.mark.app_menu,
]

# -----------------------------------------------------


def test_menu_mechanics_switches_device_context_to_world_when_empty(
    mock_mechanic,
    mock_board: Board,
    mock_bus: deque,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.MENU.value)
    mock_board.menus.clear()
    mock_board.device.context(DeviceContexts.MENU.value)

    mechanic.update(mock_board, 1.0 / 60.0, mock_bus, mock_payload())

    assert mock_board.device._context == DeviceContexts.WORLD.value
    assert len(mock_bus) == 0


@pytest.mark.workflow_traversal
def test_menu_mechanics_traverses_focus_statelessly(
    mock_mechanic,
    mock_board: Board,
    mock_bus: deque,
    mock_payload,
    mock_menu,
):
    mechanic = mock_mechanic(Mechanics.MENU.value)
    main_menu = mock_menu(Menus.MAIN.value)
    mock_board.menus = [main_menu]

    assert main_menu.focus == "new-game"
    assert main_menu.widgets["new-game"].state.status == Statuses.ACTIVE.value
    assert main_menu.widgets["load-game"].state.status == Statuses.IDLE.value

    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(traversal=Traversal.SOUTH.value),
    )

    assert mock_board.device._context == DeviceContexts.MENU.value
    assert main_menu.focus == "load-game"
    assert main_menu.widgets["new-game"].state.status == Statuses.IDLE.value
    assert main_menu.widgets["load-game"].state.status == Statuses.ACTIVE.value


@pytest.mark.workflow_traversal
def test_menu_mechanics_cancel_interaction_emits_terminal_event(
    mock_mechanic,
    mock_board: Board,
    mock_bus: deque,
    mock_payload,
    mock_menu,
):
    mechanic = mock_mechanic(Mechanics.MENU.value)
    mock_board.menus = [mock_menu(Menus.MAIN.value)]

    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(interaction=Interactions.CANCEL.value),
    )

    assert len(mock_bus) == 1
    assert isinstance(mock_bus.popleft(), TerminalEvent)


@pytest.mark.workflow_traversal
def test_menu_mechanics_select_interaction_delegates_to_controller(
    mock_mechanic,
    mock_board: Board,
    mock_bus: deque,
    mock_payload,
    mock_menu,
):
    mechanic = mock_mechanic(Mechanics.MENU.value)
    main_menu = mock_menu(Menus.MAIN.value)
    mock_board.menus = [main_menu]
    mock_board.overlays = [mock_menu(Menus.VIEW.value)]

    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(interaction=Interactions.SELECT.value),
    )

    assert len(mock_bus) == 2
    assert isinstance(mock_bus.popleft(), TerminalEvent)
    assert isinstance(mock_bus.popleft(), StateEvent)


@pytest.mark.menu_gizmo
@pytest.mark.workflow_traversal
@pytest.mark.workflow_inventory
def test_menu_mechanics_1d_strip_gizmo_edge_scrolling_and_disabled_guard(
    mock_mechanic,
    mock_board: Board,
    mock_bus: deque,
    mock_payload,
    mock_menu,
):
    """
    Verifies 1D strip Gizmo in Menu: Equipment scrolls horizontally at EAST/WEST
    aperture boundaries and blocks traversal into DISABLED vacant slots.
    """
    mechanic = mock_mechanic(Mechanics.MENU.value)
    player = mock_board.player()
    player.state.inventory.sheathe = [
        WeaponPalette.SWORD.value,
        WeaponPalette.DAGGER.value,
        WeaponPalette.SPEAR.value,
        WeaponPalette.LONGBOW.value,
        WeaponPalette.CROSSBOW.value,
    ]
    player.state.inventory.belt = [WeaponPalette.SWORD.value]

    eq_menu = mock_menu(Menus.EQUIPMENT.value)
    mock_board.menus = [eq_menu]
    weapons_grid = eq_menu.widgets["equipment-weapons-grid"]

    # Place focus at the right boundary (slot 3) of the 1x4 strip
    eq_menu.widgets[eq_menu.focus].state.status = Statuses.IDLE.value
    eq_menu.focus = "equipment-weapons-grid-slot-3"
    eq_menu.widgets["equipment-weapons-grid-slot-3"].state.status = Statuses.ACTIVE.value

    # Pressing EAST at slot 3 scrolls offset 0 -> 1 and retains focus on slot 3
    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(traversal=Traversal.EAST.value),
    )
    assert weapons_grid.state.offset == 1
    assert eq_menu.focus == "equipment-weapons-grid-slot-3"
    assert weapons_grid.state.get_item(3) == WeaponPalette.CROSSBOW.value

    # Pressing SOUTH from slot 3 is blocked because tools-grid-slot-3 is DISABLED
    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(traversal=Traversal.SOUTH.value),
    )
    assert eq_menu.focus == "equipment-weapons-grid-slot-3"

    # Place focus at the left boundary (slot 0) while offset == 1 and press WEST -> offset 1 -> 0
    eq_menu.widgets["equipment-weapons-grid-slot-3"].state.status = Statuses.IDLE.value
    eq_menu.focus = "equipment-weapons-grid-slot-0"
    eq_menu.widgets["equipment-weapons-grid-slot-0"].state.status = Statuses.ACTIVE.value

    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(traversal=Traversal.WEST.value),
    )
    assert weapons_grid.state.offset == 0
    assert eq_menu.focus == "equipment-weapons-grid-slot-0"


@pytest.mark.menu_gizmo
@pytest.mark.workflow_traversal
@pytest.mark.workflow_inventory
def test_menu_mechanics_2d_grid_gizmo_edge_scrolling_and_focus_clamp(
    mock_mechanic,
    mock_board: Board,
    mock_bus: deque,
    mock_payload,
    mock_menu,
):
    """
    Verifies 2D grid Gizmo in Menu: Pouch scrolls by `columns` (4) on SOUTH/NORTH
    boundaries, synchronizes slot statuses, and clamps focus when the target slot becomes vacant.
    """
    mechanic = mock_mechanic(Mechanics.MENU.value)
    pouch_menu = mock_menu(Menus.POUCH.value)
    mock_board.menus = [pouch_menu]

    pouch_grid = pouch_menu.widgets["inventory-pouch-grid"]
    items = [f"item-{i}" for i in range(9)]
    pouch_grid.state.collection_function = lambda: items
    pouch_grid.state.offset = 0
    pouch_grid.state.sync("inventory-pouch-grid", pouch_menu.widgets)

    # Focus bottom-right slot (slot 7) at offset 0
    pouch_menu.widgets[pouch_menu.focus].state.status = Statuses.IDLE.value
    pouch_menu.focus = "inventory-pouch-grid-slot-7"
    pouch_menu.widgets["inventory-pouch-grid-slot-7"].state.status = Statuses.ACTIVE.value

    # Traverse SOUTH at bottom boundary -> offset advances 0 -> 4; only 5 items remain (slots 0..4),
    # so slot 7 becomes DISABLED and focus clamps to slot 4
    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(traversal=Traversal.SOUTH.value),
    )
    assert pouch_grid.state.offset == 4
    assert pouch_menu.focus == "inventory-pouch-grid-slot-4"
    assert pouch_menu.widgets["inventory-pouch-grid-slot-4"].state.status == Statuses.ACTIVE.value
    assert pouch_menu.widgets["inventory-pouch-grid-slot-7"].state.status == Statuses.DISABLED.value

    # Move focus to top row (slot 0) and traverse NORTH -> offset scrolls 4 -> 0
    pouch_menu.widgets["inventory-pouch-grid-slot-4"].state.status = Statuses.IDLE.value
    pouch_menu.focus = "inventory-pouch-grid-slot-0"
    pouch_menu.widgets["inventory-pouch-grid-slot-0"].state.status = Statuses.ACTIVE.value

    mechanic.update(
        mock_board,
        1.0 / 60.0,
        mock_bus,
        mock_payload(traversal=Traversal.NORTH.value),
    )
    assert pouch_grid.state.offset == 0
    assert pouch_menu.focus == "inventory-pouch-grid-slot-0"
    assert pouch_menu.widgets["inventory-pouch-grid-slot-7"].state.status == Statuses.IDLE.value