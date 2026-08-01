"""
# Ontology: Engine

"""
# NOTE: PSEUDCODE

# Standard Libraries
from typing import Tuple

# Application Libraries
from app.game.board import Board
from app.screen import Screen
from app.player import Player

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
            Screen(screen, self.board.tiles_by_layer(layer))
            for layer 
            in self.board.layers
        ]

    def _menu(self) -> float:
        # TODO: start time 

        # 1. update menu
        self.board.menu()

        # TODO: end time
        # ETC: calculate frame rates, lag, buffer rates, skips, etc.
        differential = 0.25 # some number
        return differential

    def loop(self) -> None:
        delta = 1.0 / 60.0
        accumulator = 0.0
        last_time = get_time()

        while self.board.loaded:
            current_time = get_time()
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
