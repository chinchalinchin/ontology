"""
# Ontology: app.game.logic.mechanics.core.motion

Package for MotionMechanics
"""
from __future__ import annotations

# Standard Libraries
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
from app.config.enums import (
    AssetCategories, 
    AssetInstances, 
    Lifecycles,
)
from app.game.logic.modules.motion import (
    motive,
    kinematic,
    frictive
)

from app.models.state import DevicePayload

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.physics as physics


logger = logging.getLogger(__name__)


class Mechanic(ABC):
    """
    """

    @abstractmethod 
    def update(self, 
        board: Board, 
        delta: float,
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass

class AnimationMechanics(Mechanic):
    """
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        if not board.paused:
            for asset in board.categories(AssetCategories.EFFECTS):
                asset.animation.animate(asset.state, asset.properties)
            for asset in board.categories(AssetCategories.SHEETS):
                asset.animation.animate(asset.state, asset.properties)
            for asset in board.instances(AssetInstances.CHESTS):
                asset.animation.animate(asset.state, asset.properties)
            for asset in board.instances(AssetInstances.GATES):
                asset.animation.animate(asset.state, asset.properties)
            for asset in board.instances(AssetInstances.PLATES):
                asset.animation.animate(asset.state, asset.properties)

            for effect in board.instances(AssetInstances.REACTABLES.value):
                if effect.state.active:
                    effect.animation.cooldown(effect.state, effect.properties)



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


class MotionMechanics(Mechanic):
    """
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        players = board.instances(AssetInstances.PLAYERS)
        sprites = board.instances(AssetInstances.SPRITES)
        crates = board.instances(AssetInstances.CRATES)
        projectiles = board.instances(AssetInstances.PROJECTILES)

        kinematic.update(players, payload, delta)
        motive.update(sprites, board, delta)
        frictive.update(crates, board, delta)
        
        all_mutable = players + sprites + crates + projectiles
        physics.integrate(all_mutable, delta)