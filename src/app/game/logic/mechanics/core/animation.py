"""
@domain.graphics
@domain.concrete
@app.core
@app.mechanics
@asset.animation
@workflow.rendering

# Ontology: Source - app.game.logic.mechanics.core.animation

AnimationMechanics implementation.
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
from app.static.semantics import (
    AssetCategories, 
    AssetInstances
)
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload

if TYPE_CHECKING:
    from app.game.board import Board

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------

class AnimationMechanics(Mechanic):
    """
    ## AnimationMechanics
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        if not board.paused:
            # --------------------------------- CATEGORY ANIMATIONS
            for asset in board.categories(AssetCategories.EFFECTS):
                asset.animation.animate(asset.state, asset.properties)
            for asset in board.categories(AssetCategories.SHEETS):
                asset.animation.animate(asset.state, asset.properties)
            # --------------------------------- SPECIAL ANIMATIONS
            for effect in board.instances(AssetInstances.REACTABLES.value):
                if effect.state.active:
                    effect.animation.cooldown(effect.state, effect.properties)

