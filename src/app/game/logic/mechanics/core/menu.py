"""
# Ontology: app.game.logic.mechanics.core.menu

Package for MenuMechanics.
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
from app.config.enums import (
    Statuses, 
    Interactions,
    DeviceContexts
)
from app.game.logic.mechanics import Mechanic
from app.game.menus.events import TerminalEvent
from app.models.state import DevicePayload

if TYPE_CHECKING:
    from app.game.board import Board


logger = logging.getLogger(__name__)


class MenuMechanics(Mechanic):

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        # Animate Overlays (World-time)
        for overlay in board.overlays:
            for widget in overlay.widgets.values():
                widget.animation.animate(widget.state, widget.properties)

            if overlay.controller:
                overlay.controller.update(overlay, board, bus)

        # Context Control
        if not board.menus:
            board.device.context(DeviceContexts.WORLD.value)
            return

        board.device.context(DeviceContexts.MENU.value)

        active_menu = board.menus[-1]
        
        # Animate Active Menu (Menu-time)
        for widget in active_menu.widgets.values():
            widget.animation.animate(widget.state, widget.properties)
            
        active_menu.controller.update(active_menu, board, bus)

        # Input Interception
        traversal = payload.menu.traversal
        interaction = payload.menu.interaction

        if interaction == Interactions.CANCEL.value:
            bus.append(TerminalEvent())
            return

        if traversal and active_menu.focus:
            direction = traversal
            neighbors = active_menu.graph.get(active_menu.focus, {})
            if direction in neighbors:
                new_focus = neighbors[direction]
                active_menu.widgets[active_menu.focus].state.status = Statuses.IDLE.value
                active_menu.widgets[new_focus].state.status = Statuses.ACTIVE.value
                active_menu.focus = new_focus

        if interaction == Interactions.SELECT.value and active_menu.focus:
            active_menu.controller.select(active_menu.focus, active_menu, board, bus)