"""
# Ontology: app.game.engine

Package for core game loop.
"""
# Standard Library
import time
from typing import List
import logging

# Application Libraries
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
    mechanics: List[Mechanic]

    def __init__(self, 
        board: Board, 
        screens: List[Screen], 
        mechanics: List[Mechanic]
    ):
        self.board = board
        self.screens = screens
        self.mechanics = mechanics

    @staticmethod
    def time() -> float:
        """
        """
        return time.perf_counter()
    
    def start(self) -> None:        
        logger.info("Entering Game Loop...")

        delta = 1.0 / 60.0
        accumulator = 0.0
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
            
            if not self.board.paused:
                while accumulator >= delta:
                    for this in self.mechanics:
                        this.update(self.board, delta)
                    accumulator -= delta
                    telemetry_updates += 1

                player = self.board.player()

                self.screens[player.state.layer].draw(
                    self.board.renderables(player.state.layer), 
                    player.state.position,
                    player.dimensions
                )
                telemetry_frames += 1

                # Output Diagnostics every ~10 seconds
                if telemetry_frames % 600 == 0:
                    elapsed = current_time - telemetry_start_time
                    avg_fps = telemetry_frames / elapsed
                    avg_ups = telemetry_updates / elapsed
                    
                    logger.info(
                        f"[TELEMETRY] Avg FPS: {avg_fps:.1f} | Avg UPS (Ticks): {avg_ups:.1f} | "
                        f"Frame Time: {frame_time * 1000:.2f}ms | Render Queue: {len(self.board.renderables(player.state.layer))}"
                    )
                    
                    # Reset trackers for the next 10-second window
                    telemetry_frames = 0
                    telemetry_updates = 0
                    telemetry_start_time = current_time