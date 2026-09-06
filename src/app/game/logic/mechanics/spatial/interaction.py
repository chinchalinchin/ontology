"""
# Ontology: app.game.logic.mechanics.spatial.interaction

Package for InteractionMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING
import collections

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetInstances,
    Intentions,
    Menus
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic
from app.game.menus.events import MenuEvent
from app.models.state import DevicePayload

class InteractionMechanics(SpatialMechanic):
    """
    ## InteractionMechanics

    Mechanic responsible for resolving Asset interactions.
    """
    def __init__(self):
        super().__init__(max_entities=2000)

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Resolves interactions between Sprites/Players and Objects (e.g., Doors, Chests, Signs).
        """
        # Ensures an entity can only interact ONCE per frame, 
        # preventing same-frame teleport bounces across layers.
        processed_sources = set()

        for layer in board.layers():
            sprites = board.instances(AssetInstances.SPRITES.value, layer)
            players = board.instances(AssetInstances.PLAYERS.value, layer)
            
            # Filter sources with 'interact' intention
            sources = [
                asset for asset in sprites + players
                if asset.state.intention == Intentions.INTERACT.value
                and asset.name not in processed_sources 
            ]
            
            if not sources:
                continue

            doors = board.instances(AssetInstances.DOORS.value, layer)
            chests = board.instances(AssetInstances.CHESTS.value, layer)
            signs = board.instances(AssetInstances.SIGNS.value, layer)
            targets = doors + chests + signs

            if not targets:
                continue

            # Route through dimension-based intersection rather than physics collision
            colliding_pairs = self.intersections(sources + targets)

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

                # Check if the mutating Sprite's center point intersects the Target dimensions.
                cx, cy = self.center(source.state.position, source.dimensions)

                tx, ty = target.state.position.x, target.state.position.y
                tw, tl = target.dimensions.w, target.dimensions.l
                
                if not (tx <= cx <= tx + tw and ty <= cy <= ty + tl):
                    continue

                # -------------------------------- DOOR INTERACTIONS
                if target.taxonomy.instance == AssetInstances.DOORS:
                    board.relayer(source, target.state.outlayer)
                    source.state.position.x = target.state.out.x
                    source.state.position.y = target.state.out.y
                    processed_sources.add(source.name)

                # -------------------------------- CHEST INTERACTIONS
                elif target.taxonomy.instance == AssetInstances.CHESTS:
                    if source.taxonomy.instance == AssetInstances.SPRITES:
                        if hasattr(target.state, 'content') and target.state.content:
                            for item in target.state.content:
                                source.state.inventory.loot[item] = source.state.inventory.loot.get(item, 0) + 1
                            target.state.content = []
                        processed_sources.add(source.name)

                    elif source.taxonomy.instance == AssetInstances.PLAYERS:
                        pass
                        # TODO: ExchangeMenu and InventoryMenu routing

                # -------------------------------- SIGN INTERACTIONS
                elif target.taxonomy.instance == AssetInstances.SIGNS:
                    if source.taxonomy.instance == AssetInstances.PLAYERS:
                        plot_val = board.plot.current if hasattr(board.plot, 'current') else board.plot
                        bus.append(MenuEvent(
                            id=Menus.TEXT.value, context={
                                'plot': plot_val, 
                                'persona': target.state.persona,
                                'lexicon': target.state.lexicon 
                            }
                        ))
                        processed_sources.add(source.name)