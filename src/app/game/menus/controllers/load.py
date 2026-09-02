"""
# Ontology: app.game.menus.controllers.load
"""
# Standard Libraries
import collections
import logging
from typing import TYPE_CHECKING

# Application Libraries
from app.config.enums import AssetCategories
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.game.menus.events import TerminalEvent

if TYPE_CHECKING:
    from app.game.screen import Screen
    from app.game.board import Board

# Cython Libraries
import libs.graphics.render as render

logger = logging.getLogger(__name__)

class LoadController(MenuController):
    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        # GUARD: Prevent transition loop while waiting for Engine to drain the TerminalEvent
        if board.loaded:
            return

        # 1. Process Migrator Data Construction
        migrator_done = True
        if board.migrator and board.migrator.target:
            migrator_done = board.migrator.step(budget_ms=16)

        # 2. Process Registry Texture Prewarming
        registry = menu.context.get('registry')
        registry_done = True
        if registry:
            registry_done = registry.prewarm(budget_ms=16)

        # 3. Handle Transitions
        if migrator_done and registry_done:
            logger.info("Hydration complete. Reallocating rendering canvases...")
            screens = menu.context.get('screens', {})
            screensize = menu.context.get('screensize')
            
            old_screens = list(screens.values())
            screens.clear()
            
            for i, layer in enumerate(board.layers()):
                tiles = board.categories(AssetCategories.TILES.value, layer)
                layer_sizes = board.size(layer)
                size = layer_sizes[0] if layer_sizes else screensize
                
                # Check for existing hardware canvases we can salvage
                if i < len(old_screens):
                    screen = old_screens[i]
                    screen.rebake(tiles, size, screensize)
                    screens[layer] = screen
                else:
                    screens[layer] = Screen(screensize, size, tiles, registry)
                    
            # Explicitly force Cython VRAM deletion on discarded Screens
            for j in range(len(board.layers()), len(old_screens)):
                screen = old_screens[j]
                if hasattr(screen, 'bg_canvas') and screen.bg_canvas:
                    render.destroy(screen.bg_canvas)
                if hasattr(screen, 'fg_canvas') and screen.fg_canvas:
                    render.destroy(screen.fg_canvas)
            
            # Set the flag to trip the guard clause on the next tick
            board.loaded = True
            bus.append(TerminalEvent())