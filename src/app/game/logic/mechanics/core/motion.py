"""
# Ontology: app.game.logic.mechanics.core.motion

Package for MotionMechanics
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
from app.config.enums import (
    AssetInstances, 
)
from app.game.logic.modules.motion import (
    motive,
    kinematic,
    frictive,
    fields
)
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.physics as physics

logger = logging.getLogger(__name__)

class MotionMechanics(Mechanic):
    """
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        players = board.instances(AssetInstances.PLAYERS.value)
        sprites = board.instances(AssetInstances.SPRITES.value)
        crates = board.instances(AssetInstances.CRATES.value)
        projectiles = board.instances(AssetInstances.PROJECTILES.value)
        rafts = board.instances(AssetInstances.RAFTS.value)

        kinematic.update(players, payload, delta)
        motive.update(sprites, board, delta)
        frictive.update(crates, board, delta)
        
        all_mutable = players + sprites + crates + projectiles + rafts
        fields.update(all_mutable, board, delta)
        physics.integrate(all_mutable, delta)