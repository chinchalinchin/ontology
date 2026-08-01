"""
Package for Cursor Asset implementations.
"""
# Standard Libraries 
from itertools import chain

# Application Libraries
from app.assets.base import Frame, Mechanic
from app.game.board import Board
from app.models.state import AssetState

# -------------------------------------- CURSOR FRAME IMPLEMENTATIONS

class CursorFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return asset

# -------------------------------------- CURSOR MECHANIC IMPLEMENTATIONS

class ProjectileMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for proj in board.projectiles:
            for target in chain(board.sprites, board.pixies):
                if proj.shape.intersects(target.shape):
                    # TODO: Resolve collision
                    pass
            if not proj.alive():
                # TODO: garbage collect
                pass