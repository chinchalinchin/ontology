"""
# Ontology: Engine

Package for core game loop.
"""
# Standard Library
import time
import logging

# Application Libraries
from app.config.enums import Devices
from app.game.board import Board

# Cython Libraries
from libs.core.models import Dimensions

logger = logging.getLogger(__name__)

class Engine:
    """
    ## Engine

    Class for running the game loop and performing framerate calculations.
    """

    board: Board
    @staticmethod
    def time() -> float:
        """
        """
        return time.perf_counter()
    
    def start(self, 
        screensize: Dimensions, 
        device: Devices
    ) -> None:
        self.orchestrate(screensize, device)
        
        logger.info("Entering Game Loop...")
        delta = 1.0 / 60.0
        accumulator = 0.0
        last_time = self.time()

        while self.board.loaded:
            current_time = self.time()
            frame_time = current_time - last_time
            last_time = current_time
            accumulator += frame_time
            
            while not self.board.paused:
                while accumulator >= delta:
                    self.board.play(delta)
                    accumulator -= delta

                player = self.board.player()

                self.screens[player.state.layer].draw(
                    self.board.assets(player.state.layer), 
                    player.state.position,
                    player.dimensions,
                    self.registry
                )

            while self.board.paused: 
                self.board.menu()