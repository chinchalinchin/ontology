"""
# Ontology: app.game.logic.mechanics.intentional.player
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    Intentions,
    PlayerGoals,
    GoalCategories
)
from app.game.logic.maps import AnimationMap
from app.game.logic.mechanics import Mechanic
from app.models.state import Goal

# Cython Libraries
from libs.core.models import Position

class PlayerMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        player = board.player()
        poll = board.poll()
        
        if poll.intentions:
            player.state.intention = poll.intentions[0]
        else:
            player.state.intention = Intentions.IDLE.value
        
        speed = player.state.character.speed
        goal_x = player.state.position.x
        goal_y = player.state.position.y
        
        # Track movement so the player doesn't instantly snap back to 'UP' when inputs are released.
        has_movement = False

        if PlayerGoals.UP.value in poll.goals:
            goal_y -= speed
            has_movement = True
        if PlayerGoals.DOWN.value in poll.goals:
            goal_y += speed
            has_movement = True
        if PlayerGoals.LEFT.value in poll.goals:
            goal_x -= speed
            has_movement = True
        if PlayerGoals.RIGHT.value in poll.goals:
            goal_x += speed
            has_movement = True

        # Initialize missing goal tracking state
        if has_movement and not player.state.goal:
            player.state.goal = Goal(
                name=player.name, 
                category=GoalCategories.POSITION.value, 
                position=Position(goal_x, goal_y)
            )
        elif player.state.goal:
            player.state.goal.position.x = goal_x
            player.state.goal.position.y = goal_y

        if player.state.intention == Intentions.ATTACK.value:
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
