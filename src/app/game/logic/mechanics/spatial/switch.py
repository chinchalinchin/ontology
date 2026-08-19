"""
# Ontology: app.game.logic.mechanics.spatial.switch

Package for SwitchMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetCategories, 
    AssetInstances
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic


class SwitchMechanics(SpatialMechanic):
    """
    ## SwitchMechanics

    Mechanic responsible for triggering plates and linking their states to gates.
    """

    def __init__(self):
        super().__init__(max_entities=1000)


    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            plates = board.instances(AssetInstances.PLATES, layer)
            if not plates:
                continue
                
            crates = board.instances(AssetInstances.CRATES, layer)
            gates = board.instances(AssetInstances.GATES, layer)
            sheets = board.categories(AssetCategories.SHEETS, layer)

            colliding_pairs = self.collisions(plates + crates + sheets)

            pressed_plates = set()

            for asset_a, asset_b in colliding_pairs:
                is_a_plate = asset_a.taxonomy.instance == AssetInstances.PLATES
                is_b_plate = asset_b.taxonomy.instance == AssetInstances.PLATES

                # Filter: Only care if exactly one is a plate
                if is_a_plate and not is_b_plate:
                    plate, weight = asset_a, asset_b
                elif is_b_plate and not is_a_plate:
                    plate, weight = asset_b, asset_a
                else:
                    continue

                # Validate the overlapping entity is a valid weight
                if (weight.taxonomy.instance == AssetInstances.CRATES or 
                    weight.taxonomy.category == AssetCategories.SHEETS):
                    pressed_plates.add(plate)

            # Apply State and Notify Gates
            for plate in plates:
                is_pressed = plate in pressed_plates
                
                # Check if the state has mutated this frame
                if plate.state.switch != is_pressed:
                    plate.state.switch = is_pressed
                    
                    # Synchronize linked gates
                    for gate in gates:
                        if gate.state.link == plate.state.link:
                            gate.state.switch = plate.state.switch
   