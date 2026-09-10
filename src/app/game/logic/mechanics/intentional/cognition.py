"""
# Ontology: app.game.logic.mechanics.intentional.cognition

Package for handling the Sprite Goal lifecycle.
"""
from __future__ import annotations

# Standard Libraries
import random
from typing import TYPE_CHECKING
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    Intentions, 
    Goals, 
    Motivations,
    AssetInstances,
    ExpressionsPalette,
    Expressions
)
from app.game.logic.mechanics.core import Mechanic
from app.models.state import (
    DevicePayload, 
    Goal
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

logger = logging.getLogger(__name__)

class CognitionMechanics(Mechanic):
    """
    ## CognitionMechanics

    The central Mechanic for managing the lifecycle of Sprite Goals. Acts as the sensory input for Sprites, handling target acquisition, vision radiuses, and goal coordinate updates. 
    """

    @staticmethod
    def nearby(p1: Position, p2: Position, radius: int) -> bool:
        return geometry.nearby(p1.x, p1.y, p2.x, p2.y, radius)
    
    @staticmethod
    def complete(sprite: Asset, board: Board) -> bool:
        goal = sprite.state.goal

        if not goal:
            return True

        if goal.category == Goals.TARGET.value:
            return board.character(goal.name).mutators.triggers.dead

        elif goal.category == Goals.SUBJECT.value:
            return sprite.state.psyche.dialogue is None

        elif goal.category == Goals.POSITION.value:
            return CognitionMechanics.nearby(
                sprite.state.goal.position, 
                sprite.state.position,
                sprite.state.mutators.parameters.action.radius
            )
        
        elif goal.category == Goals.OBJECT.value:
            # TODO:
            pass

        elif goal.category == Goals.PROPERTY.value:
            # TODO:
            pass

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        """
        ### update(board: Board, delta: float, bus: collections.deque, payload: DevicePayload)

        Mechanic interface for receiving information from the Engine.
        """
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


    def _resolve(self, sprite: Asset, board: Board) -> None:
        """
        ### _resolve(sprite: Asset, board: Board)

        Evaluates whether the current Goal has been satisfied or invalidated.
        """
        goal = sprite.state.goal
        action_radius = sprite.state.mutators.parameters.action.radius

        if not goal:
            return
        
        # ------------------------------------------------------------------------
        # ------------------------------------------------- TARGET GOAL RESOLUTION
        # ------------------------------------------------------------------------
        if goal.category == Goals.TARGET.value:
            target_state = board.character(goal.name)
            if target_state.mutators.triggers.dead:
                sprite.state.goal = None
                if goal.name in sprite.state.memory.goals.keys():
                    sprite.state.memory.goals.pop(goal.name)

            # if goal is close but not visible give up
            elif self.nearby(
                goal.position, 
                sprite.state.position, 
                action_radius
            ) and not sprite.state.mutators.triggers.vision:
                sprite.state.goal = None

        # ------------------------------------------------------------------------
        # ------------------------------------------------ SUBJECT GOAL RESOLUTION
        # ------------------------------------------------------------------------
        elif goal.category == Goals.SUBJECT.value:
            if not sprite.state.psyche.dialogue:
                sprite.state.goal = None
                logger.info(f"{sprite.name} cleared SUBJECT Goal.")
                if goal.name in sprite.state.memory.goals.keys():
                    sprite.state.memory.goals.pop(goal.name)

            # if goal is close but not visible give up
            elif self.nearby(
                goal.position, 
                sprite.state.position, 
                action_radius
            ) and not sprite.state.mutators.triggers.vision:
                sprite.state.goal = None
                logger.info(f"{sprite.name} lost SUBJECT Goal.")
                sprite.state.psyche.expression = board.cradle.spawn_expression(
                    ExpressionsPalette.BUBBLES.value, 
                    Expressions.CONFUSION.value, 
                    sprite
                )

        # ------------------------------------------------------------------------
        # ----------------------------------------------- POSITION GOAL RESOLUTION
        # ------------------------------------------------------------------------
        elif goal.category == Goals.POSITION.value:
            if self.nearby(
                goal.position, 
                sprite.state.position, 
                action_radius
            ):
                sprite.state.goal = None
                logger.info(f"{sprite.name} cleared POSITION Goal.")
        # ------------------------------------------------------------------------
        # ------------------------------------------------- OBJECT GOAL RESOLUTION
        # ------------------------------------------------------------------------
        elif goal.category == Goals.OBJECT.value:
            # If the Sprite's layer no longer matches the door's layer, 
            # InteractionMechanics successfully pushed them through.
            # TODO: what if the sprite is seeking a Chest on a different layer?
            #       this resolution is dependent on the goal being a Door Object.
            #       may need to differentiate Goal Categories between Doors and Chest...s
            if sprite.state.layer != goal.layer:
                sprite.state.goal = None
                sprite.state.memory.goals.pop(goal.name, None)

        # ------------------------------------------------------------------------
        # ---------------------------------------------- PROPERTY GOAL RESOLUTION
        # ------------------------------------------------------------------------
        elif goal.category == Goals.PROPERTY.value:
            # TODO:
            pass


    def _scan(self, sprite: Asset, board: Board) -> None:
        """
        ### _scan(sprite: Asset, board: Board)

        Scan the board and update memory.
        """
        if sprite.state.mutators.parameters is None:
            return
        
        vision_radius = sprite.state.mutators.parameters.vision.radius

        for other_name, other_state in board.characters().items():
            if other_name == sprite.name: 
                continue

            # STRICT LAYER CHECK: Cannot see across dimensions
            if other_state.layer != sprite.state.layer:
                continue

            # ------------------------------------------------------------------------
            # ------------------------------------------------- SPRITE LOCATION MEMORY
            # ------------------------------------------------------------------------
            if self.nearby(
                other_state.position, 
                sprite.state.position, 
                vision_radius
            ):
                sprite.state.memory.sprites[other_name] = other_state.position


    def _remember(self, sprite, board: Board) -> None:
        """
        ### _remember(sprite: Asset, board: Board)

        Pops the remembered goals onto the stack.
        """
        if sprite.state.intention != Intentions.IDLE.value:
            return
        
        if not sprite.state.goal and not sprite.state.memory.goals:
            return

        # ------------------------------------------------------------------------
        # ----------------------------------------------------- SPRITE GOAL RECALL
        # ------------------------------------------------------------------------
        if not sprite.state.goal:
            first = next(iter(sprite.state.memory.goals))
            sprite.state.goal = sprite.state.memory.goals.pop(first)
            logger.info(
                f"{sprite.name} remembered Goal(" 
                f"category={sprite.state.goal.category}, "
                f"name = {sprite.state.goal.name}, "
                f"layer = {sprite.state.goal.layer}"
            )


    def _ideate(self, sprite: Asset, board: Board) -> None:
        """
        ### _ideate(sprite: Asset, board: Board)

        Spontaneously generates goals for a Sprite. Initializes the conditions for the Sprite to transition through different loops of the Intention Transition Matrix.

        #### Speak Loops

        1. `idle:find`:
            - sprite.goal
            - sprite.goal.category == constants.Goals.SUBJECT.value
        2. `find:speak`:
            - sprite.state.psyche.dialogue
            - sprite.goal.category == constants.Goals.SUBJECT.value
        3. `speak:idle`:
            - not sprite.psyche.expression

        !!! note
            sprite.psyche.expression = f(sprite.state.intention)

            In other words, sprite.psyche.expression is a *side effect* of `speak`.

        !!! todo
            There is a clear "accumulation"-cycle here. 

            1. (**ACQUISITION**) Sprite has goal in `idle` (self._remember, self._ideate). 
            2. Sprite transitions into `find`. (TransitionMechanics)
            3. (**IDEATION**) Sprite acquires state field (self._ideate).\
            4. Sprite transitions into `speak` (TransitionMechanics)
            5. (**TRANSMISSION**) Sprite transmits state field (Mechanic implementations).
                - Side Effects (Mechanics implementations)
            6. Sprite transitions into `idle` (TransitionMechanics).

        """
        if sprite.state.intention != Intentions.IDLE.value:
            return
        
        # Prevent endless targeting and memory leaks if we already have a dialogue goal
        if sprite.state.goal and sprite.state.goal.category == Goals.SUBJECT.value:
            return

        if sprite.state.mutators.parameters is None:
            return
        
        vision_radius = sprite.state.mutators.parameters.vision.radius

        # ------------------------------------------------------------------------
        # -------------------------------------------------- SPEAK LOOP GENERATION
        # ------------------------------------------------------------------------ 
        if sprite.state.psyche.dialogue:
            for other_name, other_state in board.characters().items():
                if other_name == sprite.name: 
                    continue

                if other_state.layer != sprite.state.layer:
                    continue

                if self.nearby(
                    other_state.position, 
                    sprite.state.position, 
                    vision_radius
                ):
                    if sprite.state.goal and (
                        sprite.state.goal.name 
                        not in sprite.state.memory.goals.keys()
                    ):
                        sprite.state.memory.goals[sprite.state.goal.name] = sprite.state.goal
                    
                    sprite.state.goal = Goal(
                        name=other_name, 
                        category=Goals.SUBJECT.value, 
                        layer=other_state.layer,
                        position=Position(x=other_state.position.x, y=other_state.position.y)
                    )
                    logger.info(
                        f"{sprite.name} ideated Goal(" 
                        f"category={sprite.state.goal.category}, "
                        f"name = {sprite.state.goal.name}, "
                        f"layer = {sprite.state.goal.layer}"
                    )
                    return


    def _motivate(self, sprite: Asset, board: Board) -> None:
        """
        ### _motivate(sprite: Asset, board: Board)

        Scans the environment for targets matching the Sprite's motivation.
        """
        if sprite.state.intention != Intentions.IDLE.value:
            return
        
        if sprite.state.mutators.parameters is None:
            return

        if sprite.state.goal:
            return

        motivation = sprite.state.psyche.motivation

        # ------------------------------------------------------------------------
        if motivation == Motivations.CONQUEST.value:
            # TODO
            pass

        # ------------------------------------------------------------------------ 
        elif motivation == Motivations.PROFIT.value:
            # TODO
            pass

        # ------------------------------------------------------------------------ 
        elif motivation == Motivations.SURVIVAL.value:
            # TODO
            pass

        # ------------------------------------------------------------------------ 
        elif motivation == Motivations.LOVE.value:
            # TODO
            pass

        # ------------------------------------------------------------------------ 
        elif motivation == Motivations.REVENGE.value:
            # TODO
            pass

        # ------------------------------------------------------------------------ 
        elif motivation == Motivations.REBELLION.value:
            # TODO
            pass

        # ------------------------------------------------------------------------ 
        elif motivation == Motivations.SAFETY.value:
            # TODO
            pass


    def _track(self, sprite, board: Board) -> None:
        """
        ### _track(sprite: Asset, board: Board)

        Updates the goal position if the target is visible. Freezes it if not.
        """
        goal = sprite.state.goal
        vision_radius = sprite.state.mutators.parameters.vision.radius

        if not goal:
            return
        
        target_state = None

        # ------------------------------------------------------------------------ 
        if goal.category in [
            Goals.TARGET.value,
            Goals.SUBJECT.value
        ]:
            target_state = board.character(goal.name)

            if target_state:
                goal.layer = target_state.layer

        # ------------------------------------------------------------------------ 
        elif goal.category == Goals.OBJECT.value:
            # TODO
            pass
        # ------------------------------------------------------------------------ 
        elif goal.category == Goals.POSITION.value:
            sprite.state.mutators.triggers.vision = True
            return
        # ------------------------------------------------------------------------ 
        elif goal.category == Goals.PROPERTY.value:
            # TODO
            pass

        # ------------------------------------------------------------------------ 
        # CROSS-LAYER GOAL MANAGEMENT
        # ------------------------------------------------------------------------ 
        if goal.layer and goal.layer != sprite.state.layer: 
            # 1. Search for a mapped door leading to target layer
            target_door = None
            for door_name, outlayer in sprite.state.memory.doors.items():
                if outlayer == goal.layer:
                    target_door = board.asset(door_name, sprite.state.layer)
                    if target_door:
                        break
                        
            # 2. Explore unmapped doors if no mapped path exists
            if not target_door:
                # FIX: Use a generator expression with a default None fallback 
                # to prevent TypeError and StopIteration crashes.
                target_door = next((
                    d for d in board.instances(AssetInstances.DOORS.value, sprite.state.layer) 
                    if d.name not in sprite.state.memory.doors 
                    and self.nearby(
                        d.state.position, 
                        sprite.state.position,
                        vision_radius
                    )
                ), None)
                        
            # 3. Subsumption Logic
            sprite.state.memory.goals[goal.name] = goal

            if target_door:
                # Path found. Inject prerequisite OBJECT goal.
                sprite.state.goal = Goal(
                    name=target_door.name,
                    category=Goals.OBJECT.value,
                    layer=sprite.state.layer,
                    position=Position(x=target_door.state.position.x, y=target_door.state.position.y)
                )
                logger.info(
                    f"{sprite.name} tracked Goal(" 
                    f"category={sprite.state.goal.category}, "
                    f"name = {sprite.state.goal.name}, "
                    f"layer = {sprite.state.goal.layer}"
                )
            else:
                # Unattainable. Clear the goal to force a transition to `wander`.
                sprite.state.goal = None
            return
        
        # ------------------------------------------------------------------------ 
        # SAME-LAYER GOAL TRACKING
        # ------------------------------------------------------------------------
        if target_state and self.nearby(
            target_state.position, 
            sprite.state.position, 
            vision_radius
        ):
            # Target is visible: update coordinates to track movement
            sprite.state.mutators.triggers.vision = True
            sprite.state.goal.position.x = target_state.position.x
            sprite.state.goal.position.y = target_state.position.y
        else:
            # Target lost: freeze coordinates at last known position
            sprite.state.mutators.triggers.vision = False

    def _project(self, sprite, board: Board) -> None:
        """
        ### _project(sprite: Asset, board: Board)

        Alters the spatial coordinates of the Goal based on abstract Intentions.
        """
        intention = sprite.state.intention
        vision_radius = sprite.state.mutators.parameters.vision.radius

        if intention == Intentions.ESCAPE.value and sprite.state.mutators.triggers.vision:
            # Invert the target vector to run away
            dx = sprite.state.position.x - sprite.state.goal.position.x
            dy = sprite.state.position.y - sprite.state.goal.position.y
            
            # Extrapolate a point far in the opposite direction
            sprite.state.goal.position.x = sprite.state.position.x + (dx * 10)
            sprite.state.goal.position.y = sprite.state.position.y + (dy * 10)

        elif intention == Intentions.WANDER.value:
            # If generatrate a randomized goal
            
            if not sprite.state.goal or self.complete(sprite, board):
                offset_x = random.randint(-vision_radius, vision_radius)
                offset_y = random.randint(-vision_radius, vision_radius)
                sprite.state.goal = Goal(
                    # TODO: generate name somehow
                    name="wander_point",
                    category=Goals.POSITION.value,
                    layer=sprite.state.layer, # Inject strict layer tracking
                    position=Position(sprite.state.position.x + offset_x, sprite.state.position.y + offset_y)
                )
                logger.info(
                    f"{sprite.name} generated random Goal at "
                    f"({sprite.state.goal.position.x}, {sprite.state.goal.position.y})"
                )