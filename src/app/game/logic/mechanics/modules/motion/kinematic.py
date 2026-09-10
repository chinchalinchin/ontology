"""
# Ontology: app.game.logic.mechanics.motion.kinematic
"""
# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.models.state.devices import DevicePayload
from app.config.enums import PlayerGoals

# Cython Libraries
import libs.core.math.physics as physics

def update(players: List[Asset], payload: DevicePayload, delta: float):
    """
    Snaps axis and applies velocity to kinematic player entities without generating impulses.
    """
    for player in players:
        ix, iy = 0.0, 0.0
        if PlayerGoals.UP in payload.world.goals: iy -= 1.0
        if PlayerGoals.DOWN in payload.world.goals: iy += 1.0
        if PlayerGoals.LEFT in payload.world.goals: ix -= 1.0
        if PlayerGoals.RIGHT in payload.world.goals: ix += 1.0

        physics.kinematics(player.state.velocity, ix, iy, player.state.character.speed)