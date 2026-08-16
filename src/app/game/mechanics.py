"""
# Ontology: app.game.mechanics

Package for game mechanic implementations.
"""
# Standard Libraries
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Intentions,
    PlayerGoals,
    GoalCategories
)
from app.game.maps import (
    AnimationMap
)
from app.models.state import (
    Goal,
    SpriteState
)

# Cython Libraries
from libs.core.models import Position
from libs.core.math import Geometry

# ----------------------------------------------------------------------------------------

class Mechanic(ABC):
    """
    """

    @abstractmethod 
    def update(self, board: Board, delta: float) -> None:
        pass

# ----------------------------------------------------------------------------------------

class AnimationMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        for asset in board.categories(AssetCategories.EFFECTS):
            asset.animate(asset.state, asset.properties)
        for asset in board.categories(AssetCategories.SHEETS):
            asset.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.CHESTS):
            asset.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.GATES):
            asset.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.PLATES):
            asset.animate(asset.state, asset.properties)

# ----------------------------------------------------------------------------------------

class CollisionMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            sheets = board.categories(AssetCategories.SHEETS, layer)

            for this in sheets:
                for that in sheets:
                    if this.state.name != that.state.name:
                        if Geometry.intersects(
                            this.state.position, 
                            this.dimensions, 
                            this.hitboxes,
                            that.state.position, 
                            that.dimensions, 
                            that.hitboxes
                        ):
                            # Resolve collision
                            pass

# ----------------------------------------------------------------------------------------

class ProjectileMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            sheets = board.categories(AssetCategories.SHEETS, layer)
            projectiles = board.instances(AssetInstances.PROJECTILES, layer)

            for proj in projectiles:
                for target in sheets:
                    if Geometry.intersects(
                        proj.state.position,
                        proj.dimensions, 
                        proj.hitboxes,
                        target.state.position, 
                        target.dimensions, 
                        target.hitboxes
                    ):
                        # TODO: Resolve collision
                        pass

# ----------------------------------------------------------------------------------------

class RemoveMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None: 
        """
        """            
        temporary = board.instances(AssetInstances.TEMPORARY)
        projectiles = board.instances(AssetInstances.PROJECTILES)

        for effect in temporary:
            if effect.state.animation.frame > effect.properties.count:
                # TODO: implementation
                pass
            # TODO: projectile conditions

# ----------------------------------------------------------------------------------------

class SwitchMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            plates = board.instances(AssetInstances.PLATES, layer)
            crates = board.instances(AssetInstances.CRATES, layer)
            gates = board.instances(AssetInstances.GATES, layer)
            sheets = board.categories(AssetCategories.SHEETS, layer)

            for plate in plates:
                switched = False
                
                # Verify crate overlap independently
                for weight in crates:
                    if Geometry.intersects(
                        plate.state.position,
                        plate.dimensions, 
                        plate.hitboxes,
                        weight.state.position, 
                        weight.dimensions,
                        weight.hitboxes
                    ):
                        current_state = plate.state.switch
                        plate.state.switch = True
                        switched = not (current_state == plate.state.switch)
                        break 
                        
                # Verify sheet overlap independently
                if not switched:
                    for weight in sheets:
                        if Geometry.intersects(
                            plate.state.position,
                            plate.dimensions, 
                            plate.hitboxes,
                            weight.state.position, 
                            weight.dimensions,
                            weight.hitboxes
                        ):
                            current_state = plate.state.switch
                            plate.state.switch = True
                            switched = not (current_state == plate.state.switch)
                            break 
                
                # Notify linked gates 
                if switched:
                    for gate in gates:
                        if plate.state.link == gate.state.link:
                            gate.state.switch = plate.state.switch
                else:
                    plate.state.switch = switched

# ----------------------------------------------------------------------------------------

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
            sprite.state.animation.direction = AnimationMap.direction(
                sprite.state.position,
                sprite.state.goal.position
            )

            transits = sprite.transitions()
            
            # 2. Evaluate conditions
            for transit in transits:
                if transit.conditions:
                    for condition in transit.conditions:
                        if condition(sprite, board):
                            # 3. Transition the state
                            sprite.intention = transit.next
                            
                            # Break immediately to avoid evaluating the NEW state's 
                            # transitions in this same frame.
                            break

# ----------------------------------------------------------------------------------------

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
            player.state.intention = Intentions.IDLE
        
        speed = player.state.character.speed
        goal_x = player.state.position.x
        goal_y = player.state.position.y
        
        # Track movement so the player doesn't instantly snap back to 'UP' when inputs are released.
        has_movement = False

        if PlayerGoals.UP in poll.goals:
            goal_y -= speed
            has_movement = True
        if PlayerGoals.DOWN in poll.goals:
            goal_y += speed
            has_movement = True
        if PlayerGoals.LEFT in poll.goals:
            goal_x -= speed
            has_movement = True
        if PlayerGoals.RIGHT in poll.goals:
            goal_x += speed
            has_movement = True

        # UPDATE: Initialize missing goal tracking state
        if has_movement and not player.state.goal:
            player.state.goal = Goal(
                name=player.name, 
                category=GoalCategories.POSITION, 
                position=Position(goal_x, goal_y)
            )
        elif player.state.goal:
             player.state.goal.position.x = goal_x
             player.state.goal.position.y = goal_y

        player.state.animation.action = AnimationMap.action(
            player.state, 
            board.equipment
        )

        if player.state.goal and has_movement:
            player.state.animation.direction = AnimationMap.direction(
                player.state.position,
                player.state.goal.position
            )

# ----------------------------------------------------------------------------------------

class MotionMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass

# ----------------------------------------------------------------------------------------

class CommerceMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass

# ----------------------------------------------------------------------------------------

class CombatMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass

# ----------------------------------------------------------------------------------------

class SpeechMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass

# ----------------------------------------------------------------------------------------

class MenuMechanics(Mechanic):
    """
    """

    def equip(item: str, state: SpriteState, board: Board) -> None:
        """
        """

        if item in board.equipment.weapons.keys():
            state.inventory.equipment.weapon = item
            
        elif item in board.equipment.armor.keys():
            state.inventory.equipment.armor = item
            
        elif item in board.equipment.utilities.keys():
            state.inventory.equipment.utility = item
            
        elif item in board.equipment.tools.keys():
            state.inventory.equipment.tool = item
            
        elif item in board.equipment.shields.keys():
            state.inventory.equipment.shield = item


    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass