"""
# Ontology: app.game.logic.mechanics.core.remove

Package for RemoveMechanics
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
from app.config.enums import (
    AssetCategories, 
    AssetInstances, 
    Lifecycles,
)
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload

if TYPE_CHECKING:
    from app.game.board import Board


logger = logging.getLogger(__name__)


class RemoveMechanics(Mechanic):
    """
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:          
        removals = []
        for effect in board.categories(AssetCategories.EFFECTS):
            if effect.properties.lifecycle.persist or (
                effect.properties.lifecycle.type != Lifecycles.TEMPORARY.value
            ): continue

            if effect.state.animation.frame >= effect.properties.count:
                removals.append(effect)

        # TODO: delay corpse removal until no longer in camera      
        for sprite in board.instances(AssetInstances.SPRITES):
            if sprite.state.mutators.triggers.dead:
                removals.append(sprite)

        board.remove(removals)

