"""
# Ontology: app.game.logic.mechanics.intentional

Package for intentional Mechanic implementations, i.e. Sprite and Player logic.
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import AssetInstances
from app.game.logic.maps import AnimationMap
from app.game.logic.mechanics import Mechanic

class TransitionMechanics(Mechanic):
    """
    """
    
    def update(self, board: Board, delta: float) -> None:
        """
        Evaluates Intention condition lambdas for state transitions.
        """
        sprites = board.instances(AssetInstances.SPRITES)

        for sprite in sprites:
            # TODO (Phase V): Intention logic and DSL matrix compilation is pending.

            sprite.state.animation.action = AnimationMap.action(
                sprite.state,
                board.equipment
            )
            
            if sprite.state.goal:
                sprite.state.animation.direction = AnimationMap.direction(
                    sprite.state.position,
                    sprite.state.goal.position
                )

            # Query configuration Intentions using the Sprite's actual Intention State
            if sprite.state.intention not in board.configurations.intentions:
                continue

            transits = board.configurations.intentions[sprite.state.intention]
            
            # 2. Evaluate conditions
            for transit in transits:
                if transit.conditions:
                    for condition in transit.conditions:
                        if condition(sprite, board):
                            # 3. Transition the state
                            sprite.state.intention = transit.next
                            
                            # Break immediately to avoid evaluating the NEW state's 
                            # transitions in this same frame.
                            break