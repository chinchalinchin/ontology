"""
# Ontology: Mechanics

Package for Asset Mechanic implementations.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from itertools import chain

# Application Libraries
from app.game.board import Board

class Mechanic(ABC):
    """
    """

    @abstractmethod 
    def update(self, board: Board, delta: float) -> None:
        pass

class AnimationMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        for asset in chain(
            board.permanent, 
            board.temporary,
            board.chests, 
            board.gates, 
            board.plates,
            board.pixies, 
            board.sprites
        ):
            asset.animate(asset.state, asset.properties)

class CollisionMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for this in chain(board.sprites, board.pixies):
            for that in chain(board.sprites, board.pixies):
                if this.name != that.name and this.shape.intersects(
                    this.state.position,
                    this.shape,
                    that.state.position,
                    that.shape
                ):
                    # TODO: implement
                    pass
                
class RemoveMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None: 
        """
        """           

        for effect in board.temporary:
            if not effect.alive():
                # TODO: implementation
                pass

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