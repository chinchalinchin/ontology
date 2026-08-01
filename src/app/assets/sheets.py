"""
# Ontology: Sheet Assets

Package for Sheet Asset implementations.
"""
# Standard Libraries
from itertools import chain
# Application Libraries
import app.constants as constants
from app.assets.base import Animation, Frame, Mechanic
from app.game.board import Board
from app.models.properties import AssetProperties
from app.models.state import AssetState


# -------------------------------------- SHEET ANIMATION IMPLEMENTATIONS

class SpriteAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame += 1

        if state.animation.frame > properties.actions[state.animation.action].count:
            state.animation.frame = 0

        return state
    
# -------------------------------------- SHEET FRAME IMPLEMENTATIONS

class SpriteFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join([
            asset, 
            state.animation.action, 
            state.animation.direction,
            state.animation.frame
        ])

# -------------------------------------- SHEET MECHANIC IMPLEMENTATIONS

class CollisionMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for this in chain(board.sprites, board.pixies):
            for that in chain(board.sprites, board.pixies):
                if this.name != that.name and this.shape.intersects(that.shape):
                    # TODO: implement
                    pass