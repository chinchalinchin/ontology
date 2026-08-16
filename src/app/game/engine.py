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
from app.game.mechanics import Mechanic
from app.game.screen import Screen

# Cython Libraries
from libs.core.models import Dimensions

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

        while self.board.loaded:
            current_time = self.time()
            frame_time = current_time - last_time
            last_time = current_time
            accumulator += frame_time
            
            while not self.board.paused:
                while accumulator >= delta:
                    for this in self.mechanics:
                        this.update(self.board, delta)
                        accumulator -= delta

                player = self.board.player()

                self.screens[player.state.layer].draw(
                    self.board.renderables(player.state.layer), 
                    player.state.position,
                    player.dimensions
                )