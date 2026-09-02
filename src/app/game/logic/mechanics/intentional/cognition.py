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
        
        sprites = board.instances(AssetInstances.SPRITES.value)
        
        for sprite in sprites:
            # Skip the player, as PlayerMechanics handles their goals via device polling
            if sprite.name == board.player().name:
                continue

            # Phase A: Resolution (Goal Clearing)
            if sprite.state.goal:
                self._resolve_goal(sprite, board)

            # Phase B: Memory Management
            if not sprite.state.goal and getattr(sprite.state, 'memory', None) and sprite.state.memory.goals:
                sprite.state.goal = sprite.state.memory.goals
                sprite.state.memory.goals = None

            # Phase C: Perception & Ideation (Target Acquisition)
            if not sprite.state.goal:
                self._acquire_target(sprite, board)

            # Phase D: Focus (Update Goal Coordinates)
            if sprite.state.goal:
                self._track_target(sprite, board)

            # Phase E: Projection (Modify Coordinates Based on Intention)
            self._project_intention(sprite)

    def _resolve_goal(self, sprite, board: Board) -> None:
        """
        Evaluates whether the current Goal has been satisfied or invalidated.
        """
        goal = sprite.state.goal

        if goal.category == Goals.SPRITE.value:
            target = getattr(board, '_cached_characters', {}).get(goal.name)
            if not target or target.mutators.triggers.dead:
                sprite.state.goal = None

        elif goal.category == Goals.LOOT.value:
            if getattr(sprite.state, 'inventory', None) and getattr(sprite.state.inventory, 'loot', None):
                if goal.name in sprite.state.inventory.loot:
                    sprite.state.goal = None

        elif goal.category == Goals.POSITION.value:
            dx = goal.position.x - sprite.state.position.x
            dy = goal.position.y - sprite.state.position.y
            if (dx*dx + dy*dy) <= 25:  # Within 5 pixels
                sprite.state.goal = None

        elif goal.category == Goals.ASSET.value:
            target = next((s for s in board.renderables(sprite.state.layer) if s.name == goal.name), None)
            if not target:
                sprite.state.goal = None
            elif target.taxonomy.instance == AssetInstances.CHESTS.value:
                if not getattr(target.state, 'content', None):
                    sprite.state.goal = None

    def _acquire_target(self, sprite, board: Board) -> None:
        """
        Scans the environment for targets matching the Sprite's motivation.
        """
        if getattr(sprite.state, 'psyche', None) is None or getattr(sprite.state, 'mutators', None) is None or sprite.state.mutators.parameters is None:
            return
            
        vision_radius_sq = sprite.state.mutators.parameters.vision.radius ** 2
        motivation = sprite.state.psyche.motivation
        
        if motivation == Motivations.CONQUEST.value:
            player = board.player()
            dx = player.state.position.x - sprite.state.position.x
            dy = player.state.position.y - sprite.state.position.y
            
            if (dx*dx + dy*dy) <= vision_radius_sq:
                sprite.state.goal = Goal(
                    name=player.name,
                    category=Goals.SPRITE.value,
                    position=Position(player.state.position.x, player.state.position.y)
                )

        elif motivation == Motivations.PROFIT.value:
            # TODO: Scan board.renderables for CHESTS or MineableAssets. Assign Goals.ASSET or Goals.LOOT.
            pass

        elif motivation == Motivations.SURVIVAL.value:
            # TODO: Scan environment for nearby health potions, food, or safe zones.
            pass

        elif motivation == Motivations.LOVE.value:
            # TODO: Identify and track Sprite linked via memory.relationships.
            pass

        elif motivation == Motivations.REVENGE.value:
            # TODO: Track targets that have recently struck this Sprite.
            pass

        elif motivation == Motivations.REBELLION.value:
            # TODO: Target town-hall Struts or town guards if taxed heavily.
            pass

        elif motivation == Motivations.SAFETY.value:
            # TODO: Pathfind back to owned property in memory.property.
            pass

    def _track_target(self, sprite, board: Board) -> None:
        """
        Updates the goal position if the target is visible. Freezes it if not.
        """
        goal = sprite.state.goal
        target_pos = None

        if getattr(sprite.state, 'mutators', None) is None or sprite.state.mutators.parameters is None:
            sprite.state.mutators.triggers.vision = False
            return

        # Dynamically route the lookup based on goal category
        if goal.category == Goals.SPRITE.value:
            # TODO: mechanic shouldn't be accessing hidden field
            target_state = getattr(board, '_cached_characters', {}).get(goal.name)
            if target_state:
                target_pos = target_state.position

        elif goal.category == Goals.ASSET.value:
            target_asset = next((s for s in board.renderables(sprite.state.layer) if s.name == goal.name), None)
            if target_asset:
                target_pos = target_asset.state.position

        elif goal.category == Goals.POSITION.value:
            sprite.state.mutators.triggers.vision = True
            return

        elif goal.category == Goals.LOOT.value:
            # Loot tracking freezes coordinates unless mapped to a specific dynamic drop instance
            pass

        if not target_pos:
            sprite.state.mutators.triggers.vision = False
            return

        # Calculate squared distance
        dx = target_pos.x - sprite.state.position.x
        dy = target_pos.y - sprite.state.position.y
        dist_sq = dx*dx + dy*dy
        vision_radius_sq = sprite.state.mutators.parameters.vision.radius ** 2

        if dist_sq <= vision_radius_sq:
            # Target is visible: update coordinates to track movement
            sprite.state.mutators.triggers.vision = True
            sprite.state.goal.position.x = target_pos.x
            sprite.state.goal.position.y = target_pos.y
        else:
            # Target lost: freeze coordinates at last known position
            sprite.state.mutators.triggers.vision = False

    def _project_intention(self, sprite) -> None:
        """
        Alters the spatial coordinates of the Goal based on abstract Intentions.
        """
        intention = sprite.state.intention

        if intention == Intentions.ESCAPE.value and sprite.state.mutators.triggers.vision:
            # Invert the target vector to run away
            dx = sprite.state.position.x - sprite.state.goal.position.x
            dy = sprite.state.position.y - sprite.state.goal.position.y
            
            # Extrapolate a point far in the opposite direction
            sprite.state.goal.position.x = sprite.state.position.x + (dx * 10)
            sprite.state.goal.position.y = sprite.state.position.y + (dy * 10)

        elif intention == Intentions.WANDER.value:
            # If we reached our wander point (or don't have one), pick a new random nearby point
            if not sprite.state.goal or self._reached_goal(sprite):
                offset_x = random.randint(-50, 50)
                offset_y = random.randint(-50, 50)
                sprite.state.goal = Goal(
                    name="wander_point",
                    category=Goals.POSITION.value,
                    position=Position(sprite.state.position.x + offset_x, sprite.state.position.y + offset_y)
                )

    def _reached_goal(self, sprite) -> bool:
        if not sprite.state.goal:
            return True
        dx = sprite.state.goal.position.x - sprite.state.position.x
        dy = sprite.state.goal.position.y - sprite.state.position.y
        # Consider the goal "reached" if within 5 pixels
        return (dx*dx + dy*dy) < 25