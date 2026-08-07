"""
# Ontology: Engine

"""
# NOTE: PSEUDCODE

# Standard Libraries
from typing import Tuple

# Application Libraries
from app.game.board import Board
from app.screen import Screen
from app.input.player import Player

class Engine:
    # Engine components
    board : Board 
    screen: Screen
    player : Player
    # Framerate 
    rate: int 

    def __init__(self, 
        root: Path, 
        screen: Tuple[int, int]
    ):
        # Initialize engine components
        self.board = Board(root)
        self.screens = [
            Screen(screen, self.board.tiles(layer))
            for layer 
            in self.board.layers
        ]

    @staticmethod
    def time(self) -> Time:
        return current_time 
    
    def loop(self) -> None:
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

                player = self.board.player
                assets = self.board.assets()
                self.screens[player.layer].draw(assets, player)

            while self.board.paused: 
                self.board.menu()
