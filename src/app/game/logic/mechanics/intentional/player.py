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
    Goals,
    AnimatedIntentions,
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
        
        is_blocking = player.state.intention in BlockingIntentions
        is_animating = player.state.animation.frame > 0 or player.state.animation.tick > 0
        is_locked = is_blocking and is_animating

        if payload.world.intention:
            # 2. Reject new intentions if the player is locked
            if not is_locked and player.state.intention != payload.world.intention:
                player.state.intention = payload.world.intention
                player.state.animation.frame = 0
                player.state.animation.tick = 0
        else:
            # 3. Cleanly fallback to IDLE if no input is provided and we aren't locked
            if not is_locked:
                player.state.intention = Intentions.IDLE
        
        speed = player.state.character.speed
        goal_x = player.state.position.x
        goal_y = player.state.position.y
        
        # Track movement so the player doesn't instantly snap back to 'UP'
        #   when inputs are released.
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
                category=Goals.POSITION, 
                position=Position(goal_x, goal_y)
            )
        elif player.state.goal:
            player.state.goal.position.x = goal_x
            player.state.goal.position.y = goal_y

        if player.state.intention in AnimatedIntentions:
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
            eq = player.state.inventory.equipment
            logger.info(f"[TELEMETRY] Equipment State: "
                            f"Weapon: {eq.weapon} | "
                            f"Armor: {eq.armor} | "
                            f"Shield: {eq.shield} | "
                            f"Tool: {eq.tool}"
            )