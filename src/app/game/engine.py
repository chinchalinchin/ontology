# /home/grant/Projects/ontology/src/app/game/engine.py

"""
# Ontology: app.game.engine

Package for core game loop.
"""
import time
import collections
from typing import List
import logging

import app.config.settings as settings
from app.game.board import Board
from app.game.logic.mechanics.core import Mechanic
from app.game.screen import Screen
from app.services.generators.provider import Provider
from app.game.menus.events import MenuEvent, TerminalEvent, UpdateEvent

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

    @staticmethod
    def time() -> float:
        return time.perf_counter()

    def _drain(self) -> None:
        """
        Process Events.
        """
        while self.bus:
            event = self.bus.popleft()

            if isinstance(event, MenuEvent):
                self.board.paused = True
                menu_cfg = self.board.configurations.menus.get(event.id)
                if menu_cfg:
                    player = self.board.player()
                    screen = self.screens[player.state.layer]
                    menu = self.provider.unpack(
                        event.id, 
                        menu_cfg, 
                        event.context, 
                        screen.screensize
                    )
                    self.board.menus.append(menu)

            elif isinstance(event, TerminalEvent):
                if self.board.menus:
                    self.board.menus.pop()
                if not self.board.menus:
                    self.board.paused = False
                    
            elif isinstance(event, UpdateEvent):
                player = self.board.player()
                screen = self.screens[player.state.layer]
                screen.stamp(event.widget, event.content)

    def _play(self, delta) -> None:
        """
        Apply Mechanics.
        """
        payload = self.board.device.poll()
        for mechanic in self.core:
            mechanic.update(self.board, delta, self.bus, payload)

        if not self.board.paused:
            for mechanic in self.world:
                mechanic.update(self.board, delta, self.bus, payload)

    def _render(self) -> None:
        """
        Render Assets.
        """
        player = self.board.player()
        
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

        while self.board.loaded:
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
                
                logger.info(f"[TELEMETRY] Avg FPS: {avg_fps:.1f} | Avg UPS (Ticks): {avg_ups:.1f}")
                
                telemetry_frames = 0
                telemetry_updates = 0
                telemetry_start_time = self.time()