"""
# Ontology: app.game.menus.controllers.inventory

Package for managing the Player Inventory modal menu.
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING, Any

# Application Libraries
from app.config.enums import (
    Selections
)
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu, Widget
from app.game.menus.events import UpdateEvent

if TYPE_CHECKING:
    from app.game.board import Board


class InventoryController(MenuController):
    """
    ## InventoryController

    Manages Gizmo pagination offsets, item equipping/inspecting commands,
    and dispatching UpdateEvent payloads to refresh slot textures when the inventory mutates.
    """
    offset: int

    def __init__(self):
        self.offset = 0

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self.offset = 0
        self._sync_slots(menu)

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        widget = menu.widgets.get(name)
        if not widget:
            return

        binding = widget.binding
        selection = binding.selection

        if selection == Selections.SCROLLDOWN.value:
            self.offset += 1
            self._sync_slots(menu)
            bus.append(UpdateEvent(widget=widget, content=str(self.offset)))
            return

        if selection == Selections.SCROLLUP.value:
            if self.offset > 0:
                self.offset -= 1
                self._sync_slots(menu)
                bus.append(UpdateEvent(widget=widget, content=str(self.offset)))
            return

        if selection == Selections.SLOT.value:
            selector = binding.selector
            icon_widget = menu.widgets.get(selector)
            item_key = icon_widget.state.icon
            if item_key:
                player = board.player()
                self._equip_item(item_key, player.state, board)
                bus.append(UpdateEvent(widget=icon_widget, content=item_key))


    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self._sync_slots(menu)


    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self.offset = 0

    def _sync_slots(self, menu: Menu) -> None:
        """Updates slot offsets and synchronizes button statuses."""

        for widget in menu.widgets.values():
            if not isinstance(widget, Widget):
                continue

            binding = widget.binding

            if binding and hasattr(binding, "offset"):
                binding.offset = self.offset

                if hasattr(binding, "get_status") and hasattr(widget.state, "status"):
                    widget.state.status = binding.get_status()


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