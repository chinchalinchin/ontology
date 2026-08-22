"""
# Ontology: app.game.logic.mechanics.spatial.interaction

Package for InteractionMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetInstances,
    Intentions,
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic


class InteractionMechanics(SpatialMechanic):
    """
    ## InteractionMechanics

    Mechanic responsible for resolving Asset interactions.
    """
    def __init__(self):
        super().__init__(max_entities=2000)

    def update(self, board: Board, delta: float) -> None:
        """
        Resolves interactions between Sprites/Players and Objects (e.g., Doors, Chests).
        """
        # Ensures an entity can only interact ONCE per frame, 
        # preventing same-frame teleport bounces across layers.
        processed_sources = set()

        for layer in board.layers():
            sprites = board.instances(AssetInstances.SPRITES, layer)
            players = board.instances(AssetInstances.PLAYERS, layer)
            
            # Filter sources with 'interact' intention
            sources = [
                asset for asset in sprites + players
                if getattr(asset.state, 'intention', None) == Intentions.INTERACT.value
                and asset.name not in processed_sources 
                # Filter out already processed sources instantly
            ]
            
            if not sources:
                continue

            doors = board.instances(AssetInstances.DOORS, layer)
            chests = board.instances(AssetInstances.CHESTS, layer)
            targets = doors + chests

            if not targets:
                continue

            colliding_pairs = self.collisions(sources + targets)

            for asset_a, asset_b in colliding_pairs:
                is_a_source = asset_a in sources
                is_b_target = asset_b in targets
                
                is_b_source = asset_b in sources
                is_a_target = asset_a in targets
                
                if is_a_source and is_b_target:
                    source, target = asset_a, asset_b
                elif is_b_source and is_a_target:
                    source, target = asset_b, asset_a
                else:
                    continue
                    
                if source.name in processed_sources:
                    continue

                # Check if the mutating Sprite's center point intersects the Target.
                cx, cy = self.center(source.state.position, source.dimensions)

                tx, ty = target.state.position.x, target.state.position.y
                tw, tl = target.dimensions.w, target.dimensions.l
                
                if not (tx <= cx <= tx + tw and ty <= cy <= ty + tl):
                    continue
                    
                if target.taxonomy.instance == AssetInstances.DOORS:
                    board.relayer(source, target.state.outlayer)
                    source.state.position.x = target.state.out.x
                    source.state.position.y = target.state.out.y
                    processed_sources.add(source.name)
                    
                elif target.taxonomy.instance == AssetInstances.CHESTS:
                    if source.taxonomy.instance == AssetInstances.SPRITES:
                        if hasattr(target.state, 'content') and target.state.content:
                            for item in target.state.content:
                                source.state.inventory.loot[item] = source.state.inventory.loot.get(item, 0) + 1
                            target.state.content = []
                        processed_sources.add(source.name)
                    elif source.taxonomy.instance == AssetInstances.PLAYERS:
                        # TODO: Create conditional-stub for instantiating MenuEvents in the InteractionMechanics
                        pass