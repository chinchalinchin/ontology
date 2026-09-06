# /home/grant/Projects/ontology/src/app/game/engine.py

"""
# Ontology: app.game.engine

Package for core game loop.
"""
# Standard Libraries
import time
import collections
from typing import List
import logging

# Application Libraries
import app.config.settings as settings
from app.config.enums import Menus
from app.game.board import Board
from app.game.logic.mechanics.core import Mechanic
from app.game.screen import Screen
from app.services.generators.provider import Provider
from app.game.menus.events import (
    MenuEvent, 
    TerminalEvent, 
    UpdateEvent,
    StateEvent
)

logger = logging.getLogger(__name__)

class Engine:
    """
    ## Engine

    Class for running the game loop and performing framerate calculations.
    """
    board: Board
    screens: List[Screen]
    core: List[Mechanic]
    world: List[Mechanic]
    bus: collections.deque
    provider: Provider
    running: bool

    def __init__(self, 
        board: Board, 
        screens: List[Screen], 
        core: List[Mechanic],
        world: List[Mechanic],
        provider: Provider
    ):
        self.board = board
        self.screens = screens
        self.core = core
        self.world = world
        self.provider = provider
        self.bus = collections.deque()
        self.running = False

    @staticmethod
    def time() -> float:
        return time.perf_counter()

    def _drain(self) -> None:
        while self.bus:
            event = self.bus.popleft()

            if isinstance(event, MenuEvent):
                menu_cfg = self.board.configurations.menus.get(event.id)
                if menu_cfg:
                    self.board.paused = True
                    player = self.board.player()
                    # Handle screen targeting when no player is spawned yet
                    screen = self.screens[player.state.layer] \
                                if player and self.board.loaded \
                                    else next(iter(self.screens.values()))
                    
                    menu = self.provider.unpack(
                        event.id, 
                        menu_cfg, 
                        event.context, 
                        screen.screensize
                    )
                    self.board.menus.append(menu)

                    # BUGFIX: Force initial bake for all canvas-based widgets
                    for widget in menu.widgets.values():
                        if hasattr(widget.state, 'canvas') and widget.state.canvas is not None:
                            if hasattr(widget.state, 'current'):
                                screen.stamp(widget, widget.state.current())
                                
            elif isinstance(event, StateEvent):
                if hasattr(self.board, 'migrator') and self.board.migrator:
                    self.board.migrator.target = event.id
                    
                self.bus.append(MenuEvent(
                    id=Menus.LOAD.value, 
                    context={
                        'registry': next(iter(self.screens.values())).registry,
                        'screens': self.screens,
                        'screensize': next(iter(self.screens.values())).screensize
                    }
                ))

            elif isinstance(event, TerminalEvent):
                if self.board.menus:
                    popped_menu = self.board.menus.pop()
                    
                    # HUD INJECTION: Once the load screen finishes, bind the HUD to the live player
                    if popped_menu.id == Menus.LOAD.value:
                        view_cfg = self.board.configurations.menus.get(Menus.VIEW.value)
                        player = self.board.player()
                        if view_cfg and player:
                            screen = self.screens.get(
                                player.state.layer, 
                                next(iter(self.screens.values()))
                            )
                            hud_menu = self.provider.unpack(
                                Menus.VIEW.value, 
                                view_cfg, 
                                {'sprite': {'state': getattr(player, 'state', None)}}, 
                                screen.screensize
                            )
                            self.board.set_overlays([hud_menu])

                if not self.board.menus:
                    self.board.paused = False
                    
            elif isinstance(event, UpdateEvent):
                player = self.board.player()
                screen = self.screens[player.state.layer] \
                            if player and self.board.loaded \
                                else next(iter(self.screens.values()))
                screen.stamp(event.widget, event.content)

    def _play(self, delta) -> None:
        """
        Apply Mechanics.
        """
        payload = self.board.device.poll()
        for mechanic in self.core:
            mechanic.update(self.board, delta, self.bus, payload)

        if not self.board.paused and self.board.loaded:
            for mechanic in self.world:
                mechanic.update(self.board, delta, self.bus, payload)

    def _render(self) -> None:
        """
        Render Assets.
        """
        player = self.board.player()
        
        # Trap the rendering flow if we are in MainMenu or Loading mode
        if not self.board.loaded or not player:
            screen = next(iter(self.screens.values()))
            screen.clear()
            screen.interface(self.board.menus, self.board.overlays)
            screen.present()
            return
            
        screen = self.screens[player.state.layer]
        screen.clear()
        screen.draw(
            self.board.renderables(player.state.layer), 
            player.state.position,
            player.dimensions
        )
        screen.interface(
            self.board.menus, 
            self.board.overlays
        )
        screen.present()

    def start(self) -> None:        
        logger.info("Entering Game Loop...")

        delta = 1.0 / settings.TARGET_FPS
        accumulator = 0.0
        spin_threshold = 0.002 
        last_time = self.time()

        telemetry_frames = 0
        telemetry_updates = 0
        telemetry_start_time = last_time

        self.running = True
        while self.running:
            current_time = self.time()
            frame_time = current_time - last_time
            last_time = current_time
            accumulator += frame_time
            
            # Fixed-timestep Logic Updates
            while accumulator >= delta:
                self._play(delta)
                self._drain()

                accumulator -= delta
                telemetry_updates += 1

            self._render()
            telemetry_frames += 1

            #  Hybrid Pacing (Sleep + Spin)
            work_time = self.time() - current_time
            sleep_time = delta - work_time
            
            if sleep_time > 0:
                if sleep_time > spin_threshold:
                    time.sleep(sleep_time - spin_threshold)
                
                while (self.time() - current_time) < delta:
                    pass

            if telemetry_frames % 600 == 0:
                elapsed = self.time() - telemetry_start_time
                avg_fps = telemetry_frames / elapsed
                avg_ups = telemetry_updates / elapsed
                
                logger.info(f"[TELEMETRY] Avg FPS: {avg_fps:.1f} |"
                            f"Avg UPS (Ticks): {avg_ups:.1f}")
                
                telemetry_frames = 0
                telemetry_updates = 0
                telemetry_start_time = self.time()