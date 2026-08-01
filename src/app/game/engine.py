"""
# Ontology: Engine

"""
# NOTE: PSEUDCODE

from app.game.board import Board
from app.player import Player

class Engine:
    # Engine components
    board : Board 
    view : View
    player : Player
    # Framerate 
    rate: int 

    def __init__(self, 
        file: Path, 
        screen: Tuple[int, int]
    ):
        # Initialize engine components
        self.board = Board(file)
        self.views = [
            View(screen, self.board.tiles_by_layer(layer))
            for layer 
            in self.board.layers
        ]
        
    def _game(self) -> float:
        # TODO: start time 

        # 1. Update board
        self.board.play()

        # 2. Gather new state info
        layer = self.board.layer
        player = self.board.player
        assets = self.board.assets

        # 3. Draw pieces on Board
        self.views[layer].draw(assets, player)

        # TODO: end time
        # ETC: calculate frame rates, lag, buffer rates, skips, etc.
        differential = 0.25 # some number
        return differential

    def _menu(self) -> float:
        # TODO: start time 

        # 1. update menu
        self.board.menu()

        # TODO: end time
        # ETC: calculate frame rates, lag, buffer rates, skips, etc.
        differential = 0.25 # some number
        return differential

    def loop(self) -> None:
        while self.board.loaded:
            while not self.board.paused:
                delta = self._game()

            while self.board.paused: 
                delta = self._menu()

            # TODO: calculate pause from delta