"""
# Ontology: Mechanics

Package for Asset Mechanic implementations.
"""
# Standard Libraries
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board
from app.config.hierarchy import AssetCategories, AssetInstances

# Cython Libraries
from libs.math import Geometry

class Mechanic(ABC):
    """
    """

    @abstractmethod 
    def update(self, board: Board, delta: float) -> None:
        pass

# ----------------------------------------------------------------------------------------

class AnimationMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        for asset in board.categories(AssetCategories.EFFECTS):
            asset.animate(asset.state, asset.properties)
        for asset in board.categories(AssetCategories.SHEETS):
            asset.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.CHESTS):
            asset.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.GATES):
            asset.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.PLATES):
            asset.animate(asset.state, asset.properties)

# ----------------------------------------------------------------------------------------

class CollisionMechanics(Mechanic):
    def update(self, board: Board, delta_time: float) -> None:
        for layer in board.layers():
            sheets = board.categories(AssetCategories.SHEETS, layer)

            for this in sheets:
                for that in sheets:
                    if this.state.name != that.state.name:
                        # Pass the raw components to your Cython math library
                        if Geometry.intersects(
                            this.state.position, this.properties.dimensions, this.properties.hitboxes,
                            that.state.position, that.properties.dimensions, that.properties.hitboxes
                        ):
                            # Resolve collision
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
                    if Geometry.intersects(
                        proj.state.position, proj.properties.dimensions, getattr(proj.properties, 'hitboxes', []),
                        target.state.position, target.properties.dimensions, getattr(target.properties, 'hitboxes', [])
                    ):
                        # TODO: Resolve collision
                        pass
                if not proj.alive():
                    # TODO: garbage collect
                    pass

# ----------------------------------------------------------------------------------------

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

class SwitchMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            plates = board.instances(AssetInstances.PLATES, layer)
            crates = board.instances(AssetInstances.CRATES, layer)
            gates = board.instances(AssetInstances.GATES, layer)
            sheets = board.categories(AssetCategories.SHEETS, layer)

            for plate in plates:
                switched = False
                
                # Verify crate overlap independently
                for weight in crates:
                    if Geometry.intersects(
                        plate.state.position,
                        plate.properties.dimensions, 
                        getattr(plate.properties, 'hitboxes', []),
                        weight.state.position, 
                        weight.properties.dimensions,
                        getattr(weight.properties, 'hitboxes', [])
                    ):
                        current_state = plate.state.switch
                        plate.state.switch = True
                        switched = not (current_state == plate.state.switch)
                        break 
                        
                # Verify sheet overlap independently
                if not switched:
                    for weight in sheets:
                        if Geometry.intersects(
                            plate.state.position,
                            plate.properties.dimensions, 
                            getattr(plate.properties, 'hitboxes', []),
                            weight.state.position, 
                            weight.properties.dimensions,
                            getattr(weight.properties, 'hitboxes', [])
                        ):
                            current_state = plate.state.switch
                            plate.state.switch = True
                            switched = not (current_state == plate.state.switch)
                            break 
                
                # Notify linked gates 
                if switched:
                    for gate in gates:
                        if plate.state.link == gate.state.link:
                            gate.state.switch = plate.state.switch

# ----------------------------------------------------------------------------------------

class IntentionMechanics(Mechanic):
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