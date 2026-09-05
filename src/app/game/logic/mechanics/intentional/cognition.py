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
            # Skip the player
            if sprite.name == board.player().name:
                continue

            # Phase A: Resolution
            self._resolve(sprite, board)
            # Phase B: Scan
            self._scan(sprite, board)
            # Phase B: Memory
            self._remember(sprite, board)
            # Phase C: Ideate
            self._ideate(sprite, board)
            # Phase D: Acquistion
            self._motivate(sprite, board)
            # Phase E: Tracking
            self._track(sprite, board)
            # Phase F: Projection
            self._project(sprite, board)


    def _completed(self, sprite, board: Board) -> bool:
        goal = sprite.state.goal

        if not goal:
            return True

        if goal.category == Goals.TARGET.value:
            return board.character(goal.name).mutators.triggers.dead

        elif goal.category == Goals.SUBJECT.value:
            return sprite.state.psyche.dialogue is None

        elif goal.category == Goals.POSITION.value:
            dx = sprite.state.goal.position.x - sprite.state.position.x
            dy = sprite.state.goal.position.y - sprite.state.position.y
            return (dx*dx + dy*dy) < (sprite.state.mutators.parameters.action.radius ** 2)

        elif goal.category == Goals.OBJECT.value:
            # TODO:
            pass

        elif goal.category == Goals.PROPERTY.value:
            # TODO:
            pass


    def _resolve(self, sprite, board: Board) -> None:
        """
        Evaluates whether the current Goal has been satisfied or invalidated.
        """
        goal = sprite.state.goal

        if not goal:
            return
        
        if goal.category == Goals.TARGET.value:
            target_state = board.character(goal.name)

            if target_state.mutators.triggers.dead:
                sprite.state.goal = None

            if goal.name in sprite.state.memory.goals.keys():
                sprite.state.memory.goals.pop(goal.name)

        elif goal.category == Goals.SUBJECT.value:
            if not sprite.state.psyche.dialogue:
                sprite.state.goal = None

            if goal.name in sprite.state.memory.goals.keys():
                sprite.state.memory.goals.pop(goal.name)

        elif goal.category == Goals.POSITION.value:
            dx = goal.position.x - sprite.state.position.x
            dy = goal.position.y - sprite.state.position.y

            if (dx*dx + dy*dy) < (sprite.state.mutators.parameters.action.radius ** 2):
                sprite.state.goal = None

        elif goal.category == Goals.OBJECT.value:
            # TODO:
            pass

        elif goal.category == Goals.PROPERTY.value:
            # TODO:
            pass


    def _scan(self, sprite, board: Board) -> None:
        if sprite.state.mutators.parameters is None:
            return
        
        vision_radius = sprite.state.mutators.parameters.vision.radius

        for other_name, other_state in board.characters().items():
            if other_name == sprite.name: 
                continue
                
            dx = other_state.position.x - sprite.state.position.x
            dy = other_state.position.y - sprite.state.position.y
            
            if (dx*dx + dy*dy) <= (vision_radius ** 2):
                sprite.state.memory.sprites[other_name] = other_state.position


    def _remember(self, sprite, Board: Board) -> None:
        """
        Pops the remembered goals onto the stack.
        """
        if sprite.state.intention != Intentions.IDLE.value:
            return
        
        if not sprite.state.goal and not sprite.state.memory.goals:
            return
        if not sprite.state.goal:
            first = next(iter(sprite.state.memory.goals))
            sprite.state.goal = sprite.state.memory.goals.pop(first)
        

    def _ideate(self, sprite, board: Board) -> None:
        # Prevent endless targeting and memory leaks if we already have a dialogue goal
        if sprite.state.goal and sprite.state.goal.category == Goals.SUBJECT.value:
            return
            
        if sprite.state.psyche.dialogue:
            if sprite.state.mutators.parameters is None:
                return
                
            vision_radius = sprite.state.mutators.parameters.vision.radius
                
            for other_name, other_state in board.characters().items():
                if other_name == sprite.name: 
                    continue
                    
                dx = other_state.position.x - sprite.state.position.x
                dy = other_state.position.y - sprite.state.position.y
                
                if (dx*dx + dy*dy) <= (vision_radius ** 2):
                    if sprite.state.goal and \
                        sprite.state.goal.name not in sprite.state.memory.goals.keys():

                        sprite.state.memory.goals[sprite.state.goal.name] = sprite.state.goal
                    
                    sprite.state.goal = Goal(
                        name=other_name, 
                        category=Goals.SUBJECT.value, 
                        position=Position(x=other_state.position.x, y=other_state.position.y)
                    )
                    break


    def _motivate(self, sprite, board: Board) -> None:
        """
        Scans the environment for targets matching the Sprite's motivation.
        """
        if sprite.state.mutators.parameters is None:
            return

        if sprite.state.goal:
            return

        motivation = sprite.state.psyche.motivation
        
        if motivation == Motivations.CONQUEST.value:
            # TODO
            pass

        elif motivation == Motivations.PROFIT.value:
            # TODO
            pass

        elif motivation == Motivations.SURVIVAL.value:
            # TODO
            pass

        elif motivation == Motivations.LOVE.value:
            # TODO
            pass

        elif motivation == Motivations.REVENGE.value:
            # TODO
            pass

        elif motivation == Motivations.REBELLION.value:
            # TODO
            pass

        elif motivation == Motivations.SAFETY.value:
            # TODO
            pass


    def _track(self, sprite, board: Board) -> None:
        """
        Updates the goal position if the target is visible. Freezes it if not.
        """
        goal = sprite.state.goal

        if not goal:
            return
        
        target_pos = None

        if sprite.state.mutators.parameters is None:
            sprite.state.mutators.triggers.vision = False
            return

        if goal.category in [
            Goals.TARGET.value,
            Goals.SUBJECT.value
        ]:
            # TODO: hamdle dead sprites - future phase
            if sprite.state.memory.sprites and sprite.state.memory.sprites.get(goal.name):
                target_pos = sprite.state.memory.sprites[goal.name]

        elif goal.category == Goals.OBJECT.value:
            # TODO
            pass

        elif goal.category == Goals.POSITION.value:
            sprite.state.mutators.triggers.vision = True
            return

        elif goal.category == Goals.PROPERTY.value:
            # TODO
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


    def _project(self, sprite, board: Board) -> None:
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
            # If we reached our wander point (or don't have one), 
            #   pick a new random nearby point
            if not sprite.state.goal or self._completed(sprite, board):
                offset_x = random.randint(-50, 50)
                offset_y = random.randint(-50, 50)
                sprite.state.goal = Goal(
                    # TODO: generate name somehow
                    name="wander_point",
                    category=Goals.POSITION.value,
                    position=Position(sprite.state.position.x + offset_x, sprite.state.position.y + offset_y)
                )