"""
@draft
@domain.user
@domain.logic
@domain.concrete
@app.menu
@menu.controller
@workflow.traversal

# Ontology: Source - app.game.menus.controllers.inventory

Implementation for the Inventory Menu Controller
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING, Any

# Application Libraries
from app.static.semantics import (
    Selections,
    Statuses
)
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.models.menus import UpdateEvent
from app.models.state import CollectionState

if TYPE_CHECKING:
    from app.game.board import Board


class InventoryController(MenuController):
    """
    ## InventoryController

    Manages Gizmo pagination commands and slot equipment mutations.
    """

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        widget = menu.widgets.get(name)
        if not widget:
            return

        binding = widget.binding
        selection = binding.selection
        target_key = binding.selector

        if selection == Selections.SCROLLDOWN.value:
            target_widget = menu.widgets.get(target_key)
            if target_widget and isinstance(target_widget.state, CollectionState):
                target_widget.state.scrolldown()
                self._recover_focus(menu, target_widget)
                bus.append(UpdateEvent(
                    widget=target_widget, 
                    content=str(target_widget.state.offset)
                ))
            return

        if selection == Selections.SCROLLUP.value:
            target_widget = menu.widgets.get(target_key)
            if target_widget and isinstance(target_widget.state, CollectionState):
                target_widget.state.scrollup()
                self._recover_focus(menu, target_widget)
                bus.append(UpdateEvent(
                    widget=target_widget, 
                    content=str(target_widget.state.offset)
                ))
            return

        if selection == Selections.SLOT.value:
            target_widget = menu.widgets.get(target_key)
            if target_widget and isinstance(target_widget.state, CollectionState):
                slot_index = binding.target.index
                item_key = target_widget.state.get_item(slot_index)
                if item_key:
                    player = board.player()
                    if player:
                        self._equip_item(item_key, player.state, board)
                        bus.append(UpdateEvent(
                            widget=widget, 
                            content=item_key
                        ))

    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def _recover_focus(self, menu: Menu, gizmo_pane: Any) -> None:
        """
        Guarantees traversal integrity when the focused slot scrolls out of window bounds.
        Clamps focus to the first occupied slot, or defaults to the scroll-up button.
        """
        if not menu.focus:
            return

        focused_widget = menu.widgets.get(menu.focus)
        if not focused_widget or not focused_widget.binding:
            return

        # Focus recovery only triggers when focus resides on a slot button
        if focused_widget.binding.selection != Selections.SLOT.value:
            return

        slot_index = int(focused_widget.binding.target.index)
        if gizmo_pane.state.is_occupied(slot_index):
            return

        # Target slot is vacant; search for the first occupied slot aperture
        new_focus = None
        for i in range(gizmo_pane.state.capacity):
            if gizmo_pane.state.is_occupied(i):
                candidate_name = f"{gizmo_pane.name}-slot-{i}"
                if candidate_name in menu.widgets:
                    new_focus = candidate_name
                    break

        # Fallback to pagination controls
        if not new_focus:
            fallback = "inventory-scroll-up"
            if fallback in menu.widgets:
                new_focus = fallback

        if new_focus and new_focus != menu.focus:
            focused_widget.state.status = Statuses.IDLE.value
            menu.widgets[new_focus].state.status = Statuses.ACTIVE.value
            menu.focus = new_focus

    def _equip_item(self, item: str, state: Any, board: Board) -> None:
        """Equips an item into the matching slot on player inventory."""
        if board.equipment:
            if item in board.equipment.weapons:
                state.inventory.equipment.weapon = item
            elif item in board.equipment.armor:
                state.inventory.equipment.armor = item
            elif item in board.equipment.utilities:
                state.inventory.equipment.utility = item
            elif item in board.equipment.tools:
                state.inventory.equipment.tool = item
            elif item in board.equipment.shields:
                state.inventory.equipment.shield = item