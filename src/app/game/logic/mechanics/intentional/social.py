from __future__ import annotations
from typing import TYPE_CHECKING
import collections

if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    Intentions, 
    AssetInstances, 
    Goals, 
    Expressions,
    ExpressionsPalette
)
from app.game.logic.mechanics.core import Mechanic
from app.models.state import DevicePayload

class SocialMechanics(Mechanic):
    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        for sprite in board.instances(AssetInstances.SPRITES.value):
            if sprite.state.intention in [
                Intentions.SPEAK.value, 
                Intentions.BARTER.value, 
                Intentions.THREATEN.value
            ]:
                
                # Check lock: Only fire data transfer if expression doesn't exist
                if not sprite.state.psyche.expression:
                    goal = sprite.state.goal
                    if goal and goal.category == Goals.SUBJECT.value:

                        target = board.asset(goal.name, sprite.state.layer)
                        
                        if target:
                            # NPC-to-NPC
                            if target.instance == AssetInstances.SPRITES.value:
                                if sprite.state.psyche.dialogue:
                                    target.state.memory.rumors.append(sprite.state.psyche.dialogue)
                                
                            sprite.state.psyche.expression = board.cradle.spawn_expression(
                                ExpressionsPalette.BUBBLES.value, 
                                Expressions.LOQUACITY.value, 
                                sprite
                            )

                else:
                    sprite.state.psyche.dialogue = None