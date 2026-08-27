"""
# Ontology: app.game.engine

Package for core game loop.
"""
# Standard Library
import time
from typing import List
import logging

# Application Libraries
import app.config.settings as settings
from app.game.board import Board
from app.game.logic.mechanics import Mechanic
from app.game.screen import Screen

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

    def __init__(self, 
        board: Board, 
        screens: List[Screen], 
        core: List[Mechanic],
        world: List[Mechanic]
    ):
        self.board = board
        self.screens = screens
        self.core = core
        self.world = world

    @staticmethod
    def time() -> float:
        """
        """
        return time.perf_counter()
    
    def start(self) -> None:        
        logger.info("Entering Game Loop...")

        delta = 1.0 / settings.TARGET_FPS
        accumulator = 0.0
        
        # 2ms buffer to account for OS thread-wake scheduling inaccuracy
        spin_threshold = 0.002 
        
        last_time = self.time()

        # Telemetry Trackers
        telemetry_frames = 0
        telemetry_updates = 0
        telemetry_start_time = last_time

        while self.board.loaded:
            current_time = self.time()
            frame_time = current_time - last_time
            last_time = current_time
            accumulator += frame_time
            
            # 1. Fixed-timestep Logic Updates
            while accumulator >= delta:
                for mechanic in self.core:
                    mechanic.update(self.board, delta)

                if not self.board.paused:
                    for mechanic in self.world:
                        mechanic.update(self.board, delta)

                accumulator -= delta
                telemetry_updates += 1

            player = self.board.player()

            # 2. Rendering
            screen = self.screens[player.state.layer]
            # TODO: screen.clear()
            screen.draw(
                self.board.renderables(player.state.layer), 
                player.state.position,
                player.dimensions
            )
            # TODO: screen.interface(self.board.menus, self.board.overlays)
            # TODO: screen.present()

            telemetry_frames += 1

            # 3. Hybrid Pacing (Sleep + Spin)
            work_time = self.time() - current_time
            sleep_time = delta - work_time
            
            if sleep_time > 0:
                # Yield to the OS scheduler if we have substantial time remaining
                if sleep_time > spin_threshold:
                    time.sleep(sleep_time - spin_threshold)
                
                # Spin-lock the final fraction of a millisecond for precise timing
                while (self.time() - current_time) < delta:
                    pass

            # Output Diagnostics every ~10 seconds
            if telemetry_frames % 600 == 0:
                elapsed = self.time() - telemetry_start_time
                avg_fps = telemetry_frames / elapsed
                avg_ups = telemetry_updates / elapsed
                
                logger.info(
                    f"[TELEMETRY] Avg FPS: {avg_fps:.1f} | Avg UPS (Ticks): {avg_ups:.1f} | "
                    f"Frame Time: {frame_time * 1000:.2f}ms | Render Queue: {len(self.board.renderables(player.state.layer))}"
                )
                
                telemetry_frames = 0
                telemetry_updates = 0
                telemetry_start_time = self.time()