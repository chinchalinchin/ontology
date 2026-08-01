"""
# Ontology: Object Assets

Package for Object Asset implementations.
"""
# Standard Libraries
from itertools import chain

# Application Libraries
import app.constants as constants

from app.assets.base import Animation, Frame, Mechanic
from app.game.board import Board
from app.models.state import AssetState
from app.models.properties import AssetProperties

# -------------------------------------- OBJECT ANIMATION IMPLEMENTATIONS


class BinaryAnimation(Animation):

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame = constants.ON if state.state.switch else constants.OFF
        return state
        
# -------------------------------------- OBJECT FRAME IMPLEMENTATIONS

class ObjectFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return asset
    
class BinaryFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join(
            asset, 
            state.animation.frame
        )

# -------------------------------------- OBJECT MECHANIC IMPLEMENTATIONS

class SwitchMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for plate in board.plates:
            for weight in chain(board.crates, board.sprites, board.pixies):
                 if plate.shape.intersects(weight.shape):
                    current_state = plate.state.switch
                    plate.state.switch = True
                    switched = not (current_state == plate.state.switch)
                    break 
                
            if switched:
                for gate in board.gates:
                    if plate.state.link == gate.state.link:
                        gate.state.switch = plate.state.switch