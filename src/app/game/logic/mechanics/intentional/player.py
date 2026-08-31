"""
# Ontology: app.game.logic.mechanics.intentional.player
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import collections

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    Intentions,
    PlayerGoals,
    GoalCategories,
    BlockingIntentions
)
from app.game.logic.maps import AnimationMap
from app.game.logic.mechanics import Mechanic
from app.models.state import (
    Goal, 
    DevicePayload
)

# Cython Libraries
from libs.core.models import Position

logger = logging.getLogger(__name__)

class PlayerMechanics(Mechanic):
    """
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        """
        player = board.player()
        
        # Define intentions that lock the player until their animation completes
        blocking_intentions = {
            Intentions.ATTACK, 
            Intentions.MINE, 
            Intentions.BUILD, 
            Intentions.SPEAK
        }
        
        if payload.world.intention:
            # Only assign and reset the frame if the intention is new
            if player.state.intention != payload.world.intention:
                player.state.intention = payload.world.intention
                player.state.animation.frame = 0
        else:
            # Fallback to IDLE only if the player is not currently trapped in a blocking frame cycle
            is_blocking = player.state.intention in blocking_intentions
            is_animating = player.state.animation.frame > 0
            
            if not (is_blocking and is_animating):
                player.state.intention = Intentions.IDLE
        
        speed = player.state.character.speed
        goal_x = player.state.position.x
        goal_y = player.state.position.y
        
        # Track movement so the player doesn't instantly snap back to 'UP' when inputs are released.
        has_movement = False

        if PlayerGoals.UP in payload.world.goals:
            goal_y -= speed
            has_movement = True
        if PlayerGoals.DOWN in payload.world.goals:
            goal_y += speed
            has_movement = True
        if PlayerGoals.LEFT in payload.world.goals:
            goal_x -= speed
            has_movement = True
        if PlayerGoals.RIGHT in payload.world.goals:
            goal_x += speed
            has_movement = True

        # Initialize missing goal tracking state
        if has_movement and not player.state.goal:
            player.state.goal = Goal(
                name=player.name, 
                category=GoalCategories.POSITION, 
                position=Position(goal_x, goal_y)
            )
        elif player.state.goal:
            player.state.goal.position.x = goal_x
            player.state.goal.position.y = goal_y

        if player.state.intention in [
            Intentions.ATTACK,
            # TODO: add animated Intentions here
        ]:
            player.state.mutators.triggers.animated = True
        else:
            player.state.mutators.triggers.animated = has_movement

        player.state.animation.action = AnimationMap.action(
            player.state, 
            board.equipment
        )

        if player.state.goal and has_movement:
            player.state.animation.direction = AnimationMap.direction(
                player.state.position,
                player.state.goal.position
            )

        if player.state.intention == Intentions.ATTACK:
            logger.info(f"[TELEMETRY] Intention: ATTACK | "
                        f"Resolved Action: {player.state.animation.action}")
            if getattr(player.state.inventory, 'equipment', None):
                eq = player.state.inventory.equipment
                logger.info(f"[TELEMETRY] Equipment State: "
                             f"Weapon: {eq.weapon} | "
                             f"Armor: {eq.armor} | "
                             f"Shield: {eq.shield} | "
                             f"Tool: {eq.tool}"
                )