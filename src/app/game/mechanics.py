"""
# Ontology: Mechanics

Package for Asset Mechanic implementations.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from itertools import chain

# Application Libraries
from app.game.board import Board
from app.models.hierarchy import AssetCategories, AssetInstances

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
        """
        """
        for asset in chain(
            board.categories(AssetCategories.EFFECTS),
            board.categories(AssetCategories.SHEETS),
            board.instances(AssetInstances.CHESTS),
            board.instances(AssetInstances.GATES),
            board.instances(AssetInstances.PLATES)
        ):
            asset.animate(asset.state, asset.properties)

class CollisionMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            sheets = board.categories(AssetCategories.SHEETS, layer)

            for this in sheets:
                for that in sheets:
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
        temporary = board.instances(AssetInstances.TEMPORARY)

        for effect in temporary:
            if effect.state.animation.frame > effect.properties.count:
                # TODO: implementation
                pass

class ProjectileMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            sheets = board.categories(AssetCategories.SHEETS, layer)
            projectiles = board.instances(AssetInstances.PROJECTILES, layer)

            for proj in projectiles:
                for target in sheets:
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
        for layer in board.get_layers():
            plates = board.instances(AssetInstances.PLATES, layer)
            crates = board.instances(AssetInstances.CRATES, layer)
            gates = board.instances(AssetInstances.GATES, layer)
            sheets = board.categories(AssetCategories.SHEETS, layer)

            for plate in plates:
                for weight in chain(crates, sheets):
                    if plate.shape.intersects(weight.shape):
                        current_state = plate.state.switch
                        plate.state.switch = True
                        switched = not (current_state == plate.state.switch)
                        break 
                    
                if switched:
                    for gate in gates:
                        if plate.state.link == gate.state.link:
                            gate.state.switch = plate.state.switch

class BehaviorMechanics(Mechanic):
    """
    """
    
    def update(self, board: Board, delta: float) -> None:
        """
        Evaluates AST lambdas to transition Dispositions.
        """
        sprites = board.instances(AssetInstances.SPRITES)

        for sprite in sprites:
            # 1. Fetch the compiled AST transitions for the CURRENT disposition
            transits = sprite.intention.transitions()
            
            # 2. Evaluate conditions
            for transit in transits:
                if transit.conditions(sprite, board):
                    # 3. Transition the state
                    sprite.intention.disposition = transit.next
                    
                    # Break immediately to avoid evaluating the NEW state's 
                    # transitions in this same frame.
                    break