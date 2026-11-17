"""
@domain.concrete
@domain.logic
@app.mechanic
@physics.space
@category.sheets
@category.objects
@modality.intention
@workflow.interactions

# Ontology: Source - app.game.logic.mechanics.spatial.interaction

InteractionMechanics implementation.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

from app.static.semantics import (
    AssetInstances,
    Intentions,
    Menus
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic
from app.models.menus import (
    MenuEvent,
    DialogueContext
)
from app.models.state import DevicePayload

logger = logging.getLogger(__name__)

class InteractionMechanics(SpatialMechanic):
    def __init__(self):
        super().__init__(max_entities=2000)


    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        processed_sources = set()

        for layer in board.layers():
            sprites = board.instances(AssetInstances.SPRITES, layer)
            players = board.instances(AssetInstances.PLAYERS, layer)
            
            sources = [
                asset for asset in sprites + players
                if asset.state.intention == Intentions.INTERACT
                and asset.name not in processed_sources 
            ]
            
            if not sources:
                continue

            doors = board.instances(AssetInstances.DOORS, layer)
            chests = board.instances(AssetInstances.CHESTS, layer)
            signs = board.instances(AssetInstances.SIGNS, layer)
            reactables = [
                effect for effect in board.instances(AssetInstances.REACTABLES, layer)
                if effect.state.intention == Intentions.INTERACT
            ]
            targets = doors + chests + signs + reactables

            if not targets:
                continue

            colliding_pairs = self.intersections(sources + targets)

            for asset_a, asset_b in colliding_pairs:
                if asset_a in sources and asset_b in targets:
                    source, target = asset_a, asset_b
                elif asset_b in sources and asset_a in targets:
                    source, target = asset_b, asset_a
                else:
                    continue
                    
                if source.name in processed_sources:
                    continue

                if target.taxonomy.instance == AssetInstances.DOORS:
                    if source.taxonomy.instance == AssetInstances.SPRITES:
                        source.state.memory.doors[target.name] = target.state.outlayer
                        
                    board.relayer(source, target.state.outlayer)
                    source.state.position.x = target.state.out.x
                    source.state.position.y = target.state.out.y

                    if source.taxonomy.instance == AssetInstances.PLAYERS:
                        source.state.intention = Intentions.IDLE

                    processed_sources.add(source.name)

                elif target.taxonomy.instance == AssetInstances.CHESTS:
                    if source.taxonomy.instance == AssetInstances.SPRITES:
                        if target.state.content:
                            pass
                            # TODO: Inventory Management
                        processed_sources.add(source.name)

                elif target.taxonomy.instance == AssetInstances.SIGNS:
                    if source.taxonomy.instance == AssetInstances.PLAYERS:
                        bus.append(MenuEvent(
                            id=Menus.TEXT,
                            context=DialogueContext(
                                plot=board.plot, 
                                object=target.state
                            )
                        ))
                        processed_sources.add(source.name)

                elif target.taxonomy.instance == AssetInstances.REACTABLES:
                    target.state.active = True
                    processed_sources.add(source.name)