"""
# Ontology: app.game.logic.mechanics.motion.motive
"""
# Standard Libraries
import math
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.config.enums import NavigationIntentions

# Cython Libraries
import libs.core.math.physics as physics

def update(sprites: List[Asset], delta: float) -> None:
    """
    Evaluates pathfinding and translates distance to target into vector velocities with friction emulation.
    """
    for sprite in sprites:
        if not sprite.state.goal or sprite.state.intention not in NavigationIntentions:
            sprite.state.velocity.vx = 0.0
            sprite.state.velocity.vy = 0.0
            continue

        physics.dynamics(
            sprite.state.velocity, 
            sprite.state.position.x, 
            sprite.state.position.y, 
            sprite.state.goal.position.x, 
            sprite.state.goal.position.y, 
            sprite.state.character.speed, 
            sprite.state.character.impulse, 
            delta
        )