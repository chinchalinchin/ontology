"""
@domain.logic
@domain.concrete
@app.menu
@menu.controller
@workflow.traversal
@workflow.inventory

# Ontology: Source - app.game.menus.controllers.inventory

Implementation for the Inventory Menu Controller.
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING

# Application Libraries
from app.static.semantics import (
    ArmorPalette,
    ItemPalette,
    Menus,
    Selections,
    ShieldPalette,
    Statuses,
    ToolPalette,
    UtilityPalette,
    WeaponPalette
)
from app.game.menus.bindings import SelectBinding
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.models.menus import InventoryContext
from app.models.state import (
    CollectionState,
    Slots
)

if TYPE_CHECKING:
    from app.game.board import Board


_WEAPONS = frozenset(e.value for e in WeaponPalette)
_TOOLS = frozenset(e.value for e in ToolPalette)
_UTILITIES = frozenset(e.value for e in UtilityPalette)
_ARMOR = frozenset(e.value for e in ArmorPalette)
_SHIELDS = frozenset(e.value for e in ShieldPalette)
_ITEMS = frozenset(e.value for e in ItemPalette)


class InventoryController(MenuController):
    """
    ## InventoryController

    Manages equipment slotting and dual-grip selection latching.
    """

    @staticmethod
    def _sync_grips(menu: Menu) -> None:
        """
        Synchronizes grip target buttons in Menu: Pouch so the latched hand
        retains Statuses.SELECTED when unfocused and the unselected hand resets to IDLE.
        """
        if not isinstance(menu.context, InventoryContext):
            return

        active_grip = menu.context.active_grip
        for name, widget in menu.widgets.items():
            if not isinstance(widget.binding, SelectBinding):
                continue
            if widget.binding.selection != Selections.GRIP.value:
                continue

            if widget.binding.selector == active_grip:
                if name != menu.focus:
                    widget.state.status = Statuses.SELECTED.value
            elif name != menu.focus:
                widget.state.status = Statuses.IDLE.value

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self._sync_grips(menu)

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        widget = menu.widgets.get(name)
        if not widget or not isinstance(widget.binding, SelectBinding):
            return

        binding = widget.binding
        selection = binding.selection
        target_key = binding.selector

        if selection == Selections.GRIP.value:
            if isinstance(menu.context, InventoryContext) and target_key:
                menu.context.active_grip = target_key
                self._sync_grips(menu)
                widget.state.status = Statuses.SELECTED.value
            return

        if selection == Selections.SLOT.value:
            target_widget = menu.widgets.get(target_key)
            if not target_widget or not isinstance(target_widget.state, CollectionState):
                return

            item_key = target_widget.state.get_item(binding.index)
            if not item_key:
                return

            if isinstance(menu.context, InventoryContext):
                self._equip_item(
                    item_key,
                    menu.context.slots,
                    menu.context.active_grip,
                    menu.id,
                    board
                )

    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self._sync_grips(menu)

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def _equip_item(
        self,
        item: str,
        slots: Slots,
        active_grip: str,
        menu_id: str,
        board: Board
    ) -> None:
        """Equips an item into the matching equipment or grip slot."""
        if menu_id == Menus.POUCH.value or item in _ITEMS:
            setattr(slots.grip, active_grip, item)
            return

        if item in _WEAPONS or (board.equipment and item in board.equipment.weapons):
            slots.equipment.weapon = item
        elif item in _TOOLS or (board.equipment and item in board.equipment.tools):
            slots.equipment.tool = item
        elif item in _UTILITIES or (board.equipment and item in board.equipment.utilities):
            slots.equipment.utility = item
        elif item in _ARMOR or (board.equipment and item in board.equipment.armor):
            slots.equipment.armor = item
        elif item in _SHIELDS or (board.equipment and item in board.equipment.shields):
            slots.equipment.shield = item