"""
# Ontology: app.game.logic.mechanics.spatial.interaction

Package for InteractionMechanics
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetInstances,
    Intentions,
    Menus
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic
from app.game.menus.contexts import DialogueContext
from app.game.menus.events import MenuEvent
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
            sprites = board.instances(AssetInstances.SPRITES.value, layer)
            players = board.instances(AssetInstances.PLAYERS.value, layer)
            
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
            reactables = [
                effect for effect in board.instances(AssetInstances.REACTABLES.value, layer)
                if effect.state.intention == Intentions.INTERACT.value
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

                if target.taxonomy.instance == AssetInstances.DOORS.value:
                    if source.taxonomy.instance == AssetInstances.SPRITES.value:
                        source.state.memory.doors[target.name] = target.state.outlayer
                        
                    board.relayer(source, target.state.outlayer)
                    source.state.position.x = target.state.out.x
                    source.state.position.y = target.state.out.y

                    if source.taxonomy.instance == AssetInstances.PLAYERS.value:
                        source.state.intention = Intentions.IDLE.value

                    processed_sources.add(source.name)

                elif target.taxonomy.instance == AssetInstances.CHESTS.value:
                    if source.taxonomy.instance == AssetInstances.SPRITES.value:
                        if target.state.content:
                            for item in target.state.content:
                                source.state.inventory.loot[item] = (
                                    source.state.inventory.loot.get(item, 0) + 1
                                )
                            target.state.content = []
                        processed_sources.add(source.name)

                elif target.taxonomy.instance == AssetInstances.SIGNS.value:
                    if source.taxonomy.instance == AssetInstances.PLAYERS.value:
                        bus.append(MenuEvent(
                            id=Menus.TEXT.value,
                            context=DialogueContext(
                                plot=board.plot, 
                                object=target.state
                            )
                        ))
                        processed_sources.add(source.name)

                elif target.taxonomy.instance == AssetInstances.REACTABLES.value:
                    target.state.active = True
                    processed_sources.add(source.name)