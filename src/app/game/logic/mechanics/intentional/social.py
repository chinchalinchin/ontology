from __future__ import annotations
from typing import TYPE_CHECKING
import collections

if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    Intentions, 
    AssetInstances, 
    Goals, 
    Menus,
    Expressions,
    ExpressionsPalette
)
from app.game.logic.mechanics.core import Mechanic
from app.models.state import DevicePayload
from app.game.menus.events import MenuEvent

class SocialMechanics(Mechanic):
    def update(self, board: Board, delta: float, bus: collections.deque, payload: DevicePayload) -> None:
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

                            # Player-to-NPC
                            elif target.instance == AssetInstances.PLAYERS.value:
                                pass
                                # TODO: this should be initiated by player, not sprite.
                                # bus.append(MenuEvent(
                                #     Menus.DIALOGUE.value, 
                                #     context={'sprite': sprite}
                                # ))
                                sprite.state.psyche.expression = board.cradle.spawn_expression(
                                    ExpressionsPalette.BUBBLES.value, 
                                    Expressions.LOQUACITY.value, 
                                    sprite
                                )
                else:
                    # Decay
                    sprite.state.psyche.expression.ttl -= 1
                    if sprite.state.psyche.expression.ttl <= 0:
                        sprite.state.psyche.expression = None
                        sprite.state.psyche.dialogue = None