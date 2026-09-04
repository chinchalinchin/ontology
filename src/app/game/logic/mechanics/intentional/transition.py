"""
# Ontology: app.game.logic.mechanics.intentional.transition
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetInstances,
    Intentions
)
from app.game.logic.maps import AnimationMap
from app.game.logic.mechanics.core import Mechanic
from app.models.state import DevicePayload
from app.services.translators.base import Executor

logger = logging.getLogger(__name__)

class TransitionMechanics(Mechanic):
    """
    Evaluates Intention transition criteria and resolves the Sprite's intended
    goals to animation Actions and spatial Directions.
    """
    
    # Injected dynamically during engine construction
    executor: Executor = None 
    
    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        
        sprites = board.instances(AssetInstances.SPRITES.value)
        sprites_dict = board.characters()  

        for sprite in sprites:
            # 1. Evaluate State ISL Conditions
            if self.executor:
                next_intent = self.executor.evaluate(sprite.state, sprites_dict)
                current_intent = sprite.state.intention

                if next_intent:
                    if next_intent != current_intent:
                        logger.info(f"Transitioning {sprite.name} from {sprite.state.intention} to "
                                    f"{next_intent}")
                        
                    sprite.state.intention = next_intent

            # 2. Resolve Action
            sprite.state.animation.action = AnimationMap.action(
                sprite.state, board.equipment
            )
            
            # 3. Resolve Direction
            if sprite.state.goal:
                sprite.state.animation.direction = AnimationMap.direction(
                    sprite.state.position, sprite.state.goal.position
                )

            # 4. Update Animation Trigger
            if sprite.name != board.player().name:
                # Animate if doing an action OR if moving towards a goal
                is_active_intention = sprite.state.intention not in (
                    Intentions.IDLE.value, 
                    Intentions.WANDER.value
                )
                has_active_velocity = (sprite.state.velocity.vx != 0 or sprite.state.velocity.vy != 0)
                
                sprite.state.mutators.triggers.animated = is_active_intention or has_active_velocity