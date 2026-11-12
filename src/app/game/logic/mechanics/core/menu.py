"""
@domain.concrete
@domain.user
@app.mechanic
@app.menu
@category.widgets
@workflow.traversal

# Ontology: Source - app.game.logic.mechanics.core.menu

Core Mechanic for Menu traversal and interaction routing.
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import (
    Optional,
    TYPE_CHECKING
)

# Application Libraries
import app.static.settings as settings
from app.game.logic.mechanics import Mechanic
from app.game.menus.core import (
    Menu,
    Widget
)
from app.game.menus.bindings import SelectBinding
from app.models.menus import TerminalEvent
from app.models.state import (
    CollectionState,
    DevicePayload
)
from app.static.semantics import (
    DeviceContexts,
    Interactions,
    Selections,
    Statuses
)

if TYPE_CHECKING:
    from app.game.board import Board


class MenuMechanics(Mechanic):
    """
    ## MenuMechanics

    Manages the active modal menu stack, delegating directional focus traversal,
    edge-triggered Gizmo pagination, and controller selection commands.
    """

    @staticmethod
    def _scroll_gizmo(direction: str, focused: Widget, menu: Menu) -> bool:
        """
        Intercepts cardinal traversal on a focused Gizmo aperture slot.
        Mutates CollectionState.offset when at the scroll boundary, refreshes
        slot statuses, and clamps focus to the highest occupied slot.
        """
        if not isinstance(focused.binding, SelectBinding):
            return False

        if focused.binding.selection != Selections.SLOT.value:
            return False

        gizmo_name = focused.binding.selector
        slot_index = focused.binding.index
        gizmo_pane = menu.widgets.get(gizmo_name)

        if not gizmo_pane or not isinstance(gizmo_pane.state, CollectionState):
            return False

        if not gizmo_pane.state.scroll(direction, slot_index):
            return False

        gizmo_pane.state.sync(gizmo_name, menu.widgets)

        clamped_idx = gizmo_pane.state.clamp_slot(slot_index)
        if clamped_idx is not None:
            target_name = settings.SEPARATOR.join([gizmo_name, Selections.SLOT.value, str(clamped_idx)])
            menu.focus = target_name
            menu.widgets[target_name].state.status = Statuses.ACTIVE.value

        return True

    @staticmethod
    def _resolve_neighbor(direction: str, focused: Widget, menu: Menu) -> Optional[str]:
        """
        Resolves the next enabled neighbor along direction in menu.graph.
        Enforces target.state.status != Statuses.DISABLED at runtime.
        """
        neighbor_name = menu.graph.get(menu.focus, {}).get(direction)
        if not neighbor_name:
            return None

        neighbor = menu.widgets.get(neighbor_name)
        if not neighbor:
            return None

        if neighbor.state.status != Statuses.DISABLED.value:
            return neighbor_name

        return None

    def _traverse(self, direction: str, menu: Menu) -> None:
        if not menu.focus:
            return

        focused = menu.widgets.get(menu.focus)
        if not focused:
            return

        if self._scroll_gizmo(direction, focused, menu):
            return

        neighbor_name = self._resolve_neighbor(direction, focused, menu)
        if not neighbor_name:
            return

        focused.state.status = Statuses.IDLE.value
        menu.focus = neighbor_name
        menu.widgets[neighbor_name].state.status = Statuses.ACTIVE.value

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        for overlay in board.overlays:
            if overlay.controller:
                overlay.controller.update(overlay, board, bus)

        if not board.menus:
            board.device.context(DeviceContexts.WORLD.value)
            return

        board.device.context(DeviceContexts.MENU.value)
        menu = board.menus[-1]

        if payload.menu.interaction == Interactions.CANCEL.value:
            bus.append(TerminalEvent())
            return

        if payload.menu.interaction == Interactions.SELECT.value:
            if menu.focus:
                menu.controller.select(menu.focus, menu, board, bus)
            menu.controller.update(menu, board, bus)
            return

        if payload.menu.traversal:
            self._traverse(payload.menu.traversal, menu)

        menu.controller.update(menu, board, bus)