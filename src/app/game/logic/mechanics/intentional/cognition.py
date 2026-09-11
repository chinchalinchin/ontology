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
import app.config.settings as settings
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
from app.game.logic.mechanics.modules.paths.plan import Planner
from app.models.state import (
    DevicePayload, 
    Goal
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

logger = logging.getLogger(__name__)

WANDER = "wander"

class CognitionMechanics(Mechanic):
    """
    ## CognitionMechanics

    The central Mechanic for managing the lifecycle of Sprite Goals. Acts as the sensory input for Sprites, handling target acquisition, vision radiuses, and goal coordinate updates. 
    """

    @staticmethod
    def log_goal(sprite: Asset, verb: str = "transformed", level: str = "info"):
        if level == "info":
            logger.info(
                f"{sprite.name} {verb} Goal(" 
                f"category={sprite.state.goal.category}, "
                f"name = {sprite.state.goal.name}, "
                f"layer = {sprite.state.goal.layer}, "
                f"position=({sprite.state.goal.position.x}, {sprite.state.goal.position.y}))"
            )
        elif level == "debug":
            logger.debug(
                f"{sprite.name} {verb} Goal(" 
                f"category={sprite.state.goal.category}, "
                f"name = {sprite.state.goal.name}, "
                f"layer = {sprite.state.goal.layer}, "
                f"position=({sprite.state.goal.position.x}, {sprite.state.goal.position.y}))"
            )


    @staticmethod
    def nearby(p1: Position, p2: Position, radius: int) -> bool:
        """
        ### nearby(p1: Position, p2: Position, radius: int)

        Quick Euclidean check if two points are within radius of one another.
        """
        return geometry.nearby(p1.x, p1.y, p2.x, p2.y, radius)

    
    @staticmethod
    def complete(sprite: Asset, board: Board) -> bool:
        """
        ### complete(sprite: Asset, board: Board)

        Determines if a Sprite's goal is resolved without mutating state.
        """
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


    @staticmethod
    def door(sprite: Asset, board: Board) -> Asset:
        """
        """
        # 1. Search for a mapped door leading to target layer
        vision_radius = sprite.state.mutators.parameters.vision.radius
        target_door = None
        for door_name, outlayer in sprite.state.memory.doors.items():
            if outlayer == sprite.state.goal.layer:
                target_door = board.asset(door_name, sprite.state.layer)
                if target_door:
                    break
                        
        # 2. Explore unmapped doors if no mapped path exists
        if not target_door:

            target_door = next((
                d for d in board.instances(AssetInstances.DOORS.value, sprite.state.layer) 
                if d.name not in sprite.state.memory.doors 
                and CognitionMechanics.nearby(
                    d.state.position, 
                    sprite.state.position,
                    vision_radius
                )
            ), None)

        return target_door

    
    @staticmethod
    def obstacles(layer: str, board: Board, exclude: list) -> list:
        """
        ### obstacles(layer: str, board: Board, exclude: list)
        
        Transforms board weights and perimeters into flat C-primitive tuples.
        """
        obstacles = []
        
        for asset in board.instances(AssetInstances.CRATES.value, layer):

        # for asset in board.weights(layer):
            if asset.name in exclude:
                continue
            obstacles.append((
                asset.state.position.x,
                asset.state.position.y,
                asset.dimensions.w,
                asset.dimensions.l
            ))

        for bound in board.perimeters.get(layer, []):
            obstacles.append((
                bound.position.x,
                bound.position.y,
                bound.dimensions.w,
                bound.dimensions.l
            ))

        return obstacles


    @staticmethod
    def path(sprite: Asset, segments: list) -> None:
        """
        ### path(sprite: Asset, segments: list)

        Converts an RRT geometric path into intentional POSITION goals (FIFO).
        """        
        # 1. Clear existing waypoints in memory
        sprite.state.memory.goals = {
            k: v for k, v in sprite.state.memory.goals.items() 
            if not str(k).startswith(settings.RRT_PATH_PREFIX)
        }
        
        # 2. Inject new waypoints sequentially (dicts preserve insertion order)
        for i, wp in enumerate(segments):
            name = settings.SEPARATOR.join([
                settings.RRT_PATH_PREFIX, 
                str(i)
            ])
            sprite.state.memory.goals[name] = Goal(
                name=name,
                category=Goals.POSITION.value,
                layer=sprite.state.layer,
                position=Position(x=wp.x, y=wp.y)
            )
            CognitionMechanics.log_goal(sprite, verb="planned")

        sprite.state.memory.goals[sprite.state.goal.name] = sprite.state.goal

        sprite.state.goal = None


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


    def _plan(self, sprite: Asset, board: Board) -> bool:
        """

        Returns true is plan or goal was altered.
        """
        obstacles = self.obstacles(
            sprite.state.layer, 
            board, 
            exclude=[ sprite.name ]
        )
                
        # Check LOS and trigger planner if occluded
        if not geometry.los(
            sprite.state.position.x, 
            sprite.state.position.y, 
            sprite.state.goal.position.x, 
            sprite.state.goal.position.y, 
            obstacles
        ):
            logger.info(f"Line-of-sight blocked for {sprite.name}. Triggering RRT.")
            planner = Planner(
                start=sprite.state.position,
                target=sprite.state.goal.position,
                obstacles=obstacles,
                step_size=32.0,
                max_iter=300
            )
            path = planner.plan()
            if path:
                self.path(sprite, path)
            else:
                CognitionMechanics.log_goal(sprite, verb="abandoned")
                sprite.state.goal = None

            return True
        return False


    def _scrap(self, sprite: Asset, board: Board) -> None: 
        """
        Returns true is goal was scrapped.
        """
        obstacles = self.obstacles(
            sprite.state.layer, 
            board, 
            exclude=[sprite.name]
        )
        if not geometry.los(
            sprite.state.position.x, 
            sprite.state.position.y, 
            sprite.state.goal.position.x, 
            sprite.state.goal.position.y, 
            obstacles
        ):
            logger.info(f"Path invalidated for {sprite.name}.")
            sprite.state.memory.goals = {
                k: v for k, v in sprite.state.memory.goals.items() 
                if not str(k).startswith(settings.RRT_PATH_PREFIX)
            }
            CognitionMechanics.log_goal(sprite, verb="abandoned")
            sprite.state.goal = None
            return True
        return False


    def _resolve(self, sprite: Asset, board: Board) -> None:
        """
        ### _resolve(sprite: Asset, board: Board)

        Evaluates whether the current Goal has been satisfied or invalidated.
        """
        goal = sprite.state.goal
        action_radius = sprite.state.mutators.parameters.action.radius

        if not goal:
            return

        # Clear stale wander goal when TransitionMechanics switches intention
        if sprite.state.intention in (
            Intentions.FIND.value, 
            Intentions.HUNT.value
        ):
            if goal.name == WANDER:
                CognitionMechanics.log_goal(sprite, verb="dropped")
                sprite.state.goal = None
                return
            
        # ------------------------------------------------------------------------
        # ------------------------------------------------- TARGET GOAL RESOLUTION
        # ------------------------------------------------------------------------
        if goal.category == Goals.TARGET.value:
            target_state = board.character(goal.name)
            if target_state.mutators.triggers.dead:
                CognitionMechanics.log_goal(sprite, verb="resolved")
                sprite.state.goal = None
                if goal.name in sprite.state.memory.goals.keys():
                    sprite.state.memory.goals.pop(goal.name)

            # if goal is close but not visible give up
            elif self.nearby(
                goal.position, 
                sprite.state.position, 
                action_radius
            ) and not sprite.state.mutators.triggers.vision:
                CognitionMechanics.log_goal(sprite, verb="abandoned")
                sprite.state.memory.goals[goal.name] = goal
                sprite.state.goal = None

        # ------------------------------------------------------------------------
        # ------------------------------------------------ SUBJECT GOAL RESOLUTION
        # ------------------------------------------------------------------------
        elif goal.category == Goals.SUBJECT.value:
            if not sprite.state.psyche.dialogue:
                CognitionMechanics.log_goal(sprite, verb="resolved")
                sprite.state.goal = None
                if goal.name in sprite.state.memory.goals.keys():
                    sprite.state.memory.goals.pop(goal.name)

            # if goal is close but not visible give up
            elif self.nearby(
                goal.position, 
                sprite.state.position, 
                action_radius
            ) and not sprite.state.mutators.triggers.vision:
                CognitionMechanics.log_goal(sprite, verb="abandoned")
                sprite.state.goal = None
                sprite.state.memory.goals[goal.name] = goal
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
                CognitionMechanics.log_goal(sprite, verb="resolved")
                sprite.state.goal = None
                
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
                CognitionMechanics.log_goal(sprite, verb="resolved")
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

                if other_name in sprite.state.memory.goals:
                    mem_goal = sprite.state.memory.goals[other_name]
                    mem_goal.position.x = other_state.position.x
                    mem_goal.position.y = other_state.position.y
                    mem_goal.layer = other_state.layer


    def _remember(self, sprite, board: Board) -> None:
        """
        ### _remember(sprite: Asset, board: Board)

        Pops the remembered goals onto the stack.
        """
        if sprite.state.intention not in [
            Intentions.IDLE.value,
            Intentions.HUNT.value, 
            Intentions.FIND.value
        ]: 
            return
        
        if not sprite.state.goal and not sprite.state.memory.goals:
            return

        if not sprite.state.goal:
            action_radius = sprite.state.mutators.parameters.action.radius
            
            selected_key = None
            for key, candidate in sprite.state.memory.goals.items():
                # If we reached the target's last-known coordinates and found it empty,
                # leave it dormant in memory until any_memories_visible spots it.
                if candidate.category in (
                    Goals.TARGET.value, 
                    Goals.SUBJECT.value
                ):
                    if self.nearby(
                        candidate.position, 
                        sprite.state.position, 
                        action_radius
                    ) and not sprite.state.mutators.triggers.vision:
                        continue
                selected_key = key
                break

            if selected_key:
                sprite.state.goal = sprite.state.memory.goals.pop(selected_key)
                CognitionMechanics.log_goal(sprite, verb="remembered")


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
        if sprite.state.goal and ( 
            sprite.state.goal.category == Goals.SUBJECT.value
        ): return

        # Prevent ideation along Sprite path finding points
        if sprite.state.goal and (
            str(sprite.state.goal.name).startswith(settings.RRT_PATH_PREFIX)
        ): return

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
                    CognitionMechanics.log_goal(sprite, verb="ideated")
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


    def _track(self, sprite: Asset, board: Board) -> None:
        """
        ### _track(sprite: Asset, board: Board)

        Updates the goal position if the target is visible. Freezes it if not.
        """
        goal = sprite.state.goal

        if not goal:
            return

        vision_radius = sprite.state.mutators.parameters.vision.radius
        target_state = None

        prefix = settings.RRT_PATH_PREFIX
        is_path = goal.name and goal.name.startswith(prefix)

        if is_path and self._scrap(sprite, board):
            return

        # ------------------------------------------------------------------------ 
        if goal.category in [
            Goals.TARGET.value,
            Goals.SUBJECT.value
        ]:
            target_state = board.character(goal.name)
            if target_state:
                goal.layer = target_state.layer

        # ------------------------------------------------------------------------ 
        elif goal.category in [
            Goals.POSITION.value,
            Goals.OBJECT.value, 
            Goals.PROPERTY.value

        ]:
            sprite.state.mutators.triggers.vision = True
            self._plan(sprite, board)
            if sprite.state.goal:
                CognitionMechanics.log_goal(sprite, verb="tracked", level="debug")
            return

        # ------------------------------------------------------------------------ 
        # CROSS-LAYER GOAL MANAGEMENT
        # ------------------------------------------------------------------------ 
        if goal and goal.layer and goal.layer != sprite.state.layer: 
            # Search for a mapped door leading to target layer
            target_door = self.door(sprite, board)
                        
            # Subsumption Logic
            sprite.state.memory.goals[goal.name] = goal

            if target_door:
                # Path found. Inject prerequisite OBJECT goal.
                sprite.state.goal   = Goal(
                    name            = target_door.name,
                    category        = Goals.OBJECT.value,
                    layer           = sprite.state.layer,
                    position        = Position(
                        x           = target_door.state.position.x, 
                        y           = target_door.state.position.y
                    )
                )
                CognitionMechanics.log_goal(sprite, verb="tracked")
            else:
                CognitionMechanics.log_goal(sprite, verb="abandoned")
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
            # Target is visible: check LOS obscuration
            sprite.state.mutators.triggers.vision = True

            if self._plan(sprite, board): return

            sprite.state.goal.position.x = target_state.position.x
            sprite.state.goal.position.y = target_state.position.y

        elif target_state:
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
            path_pending = any(
                str(k).startswith(settings.RRT_PATH_PREFIX) 
                for k in sprite.state.memory.goals.keys()
            )
            
            if not path_pending and (not sprite.state.goal or self.complete(sprite, board)):
                offset_x = random.randint(-vision_radius, vision_radius)
                offset_y = random.randint(-vision_radius, vision_radius)

                # Query board boundaries for the sprite's active layer
                layer_sizes = board.size(sprite.state.layer)
                max_w = layer_sizes[0].w
                max_l = layer_sizes[0].l

                # Account for entity boundaries to avoid placing origin on map edge
                sprite_w = sprite.dimensions.w
                sprite_l = sprite.dimensions.l
                bound_w = max(0, max_w - sprite_w)
                bound_l = max(0, max_l - sprite_l)

                raw_x = sprite.state.position.x + offset_x
                raw_y = sprite.state.position.y + offset_y

                clamped_x = max(0, min(raw_x, bound_w if max_w > 0 else raw_x))
                clamped_y = max(0, min(raw_y, bound_l if max_l > 0 else raw_y))

                sprite.state.goal = Goal(
                    name=WANDER, # TODO: enumerate
                    category=Goals.POSITION.value,
                    layer=sprite.state.layer,
                    position=Position(x=int(clamped_x), y=int(clamped_y))
                )
                CognitionMechanics.log_goal(sprite, verb="randomized")