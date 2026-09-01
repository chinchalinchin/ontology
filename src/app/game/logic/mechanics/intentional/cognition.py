"""
# Ontology: app.game.logic.mechanics.intentional.cognition
"""
from __future__ import annotations

# Standard Libraries
import random
from typing import TYPE_CHECKING
import collections

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.config.enums import (
    Intentions, 
    AssetInstances, 
    Goals, 
    Motivations
)
from app.game.logic.mechanics.core import Mechanic
from app.models.state import DevicePayload, Goal

# Cython Libraries
from libs.core.models import Position

class CognitionMechanics(Mechanic):
    """
    Acts as the sensory input for Sprites, handling target acquisition, vision radiuses, and goal coordinate updates.
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        
        sprites = board.instances(AssetInstances.SPRITES)
        
        for sprite in sprites:
            # Skip the player, as PlayerMechanics handles their goals via device polling
            if sprite.name == board.player().name:
                continue

            # 1. Perception: Target Acquisition
            if not sprite.state.goal:
                self._acquire_target(sprite, board)

            # 2. Focus: Update Goal Coordinates
            if sprite.state.goal:
                self._track_target(sprite, board)

            # 3. Projection: Modify Coordinates Based on Intention
            self._project_intention(sprite)

    def _acquire_target(self, sprite, board: Board) -> None:
        """
        Scans the environment for targets matching the Sprite's motivation.
        """
        if sprite.state.mutators.parameters is None:
            return
            
        vision_radius_sq = sprite.state.mutators.parameters.vision.radius ** 2
        motivation = sprite.state.psyche.motivation
        
        # Example: Conquest motivation seeks out the Player
        if motivation == Motivations.CONQUEST:
            player = board.player()
            dx = player.state.position.x - sprite.state.position.x
            dy = player.state.position.y - sprite.state.position.y
            
            if (dx*dx + dy*dy) <= vision_radius_sq:
                sprite.state.goal = Goal(
                    name=player.name,
                    category='sprite',
                    position=Position(player.state.position.x, player.state.position.y)
                )

    def _track_target(self, sprite, board: Board) -> None:
        """
        Updates the goal position if the target is visible. Freezes it if not.
        """
        goal = sprite.state.goal
        target_asset = None

        if sprite.state.mutators.parameters is None:
            sprite.state.mutators.triggers.vision = False
            return

        # Retrieve the physical asset from the Board based on goal category
        if goal.category == Goals.ASSET:
            # Fast dictionary lookup via cached generator or Board map
            target_asset = next((s for s in board.renderables(sprite.state.layer) if s.name == goal.name), None)
            
        if not target_asset:
            sprite.state.mutators.triggers.vision = False
            return

        # Calculate squared distance
        dx = target_asset.state.position.x - sprite.state.position.x
        dy = target_asset.state.position.y - sprite.state.position.y
        dist_sq = dx*dx + dy*dy
        vision_radius_sq = sprite.state.mutators.parameters.vision.radius ** 2

        if dist_sq <= vision_radius_sq:
            # Target is visible: update coordinates to track movement
            sprite.state.mutators.triggers.vision = True
            sprite.state.goal.position.x = target_asset.state.position.x
            sprite.state.goal.position.y = target_asset.state.position.y
        else:
            # Target lost: freeze coordinates at last known position
            sprite.state.mutators.triggers.vision = False

    def _project_intention(self, sprite) -> None:
        """
        Alters the spatial coordinates of the Goal based on abstract Intentions.
        """
        intention = sprite.state.intention

        if intention == Intentions.ESCAPE and sprite.state.mutators.triggers.vision:
            # Invert the target vector to run away
            dx = sprite.state.position.x - sprite.state.goal.position.x
            dy = sprite.state.position.y - sprite.state.goal.position.y
            
            # Extrapolate a point far in the opposite direction
            sprite.state.goal.position.x = sprite.state.position.x + (dx * 10)
            sprite.state.goal.position.y = sprite.state.position.y + (dy * 10)

        elif intention == Intentions.WANDER:
            # If we reached our wander point (or don't have one), pick a new random nearby point
            if not sprite.state.goal or self._reached_goal(sprite):
                offset_x = random.randint(-50, 50)
                offset_y = random.randint(-50, 50)
                sprite.state.goal = Goal(
                    name="wander_point",
                    category=Goals.POSITION,
                    position=Position(sprite.state.position.x + offset_x, sprite.state.position.y + offset_y)
                )

    def _reached_goal(self, sprite) -> bool:
        if not sprite.state.goal:
            return True
        dx = sprite.state.goal.position.x - sprite.state.position.x
        dy = sprite.state.goal.position.y - sprite.state.position.y
        # Consider the goal "reached" if within 5 pixels
        return (dx*dx + dy*dy) < 25