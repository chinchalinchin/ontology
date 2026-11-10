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