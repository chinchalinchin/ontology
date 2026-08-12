"""
# Ontology: Mechanics

Package for Asset Mechanic implementations.
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
    PlayerGoals
)
from app.game.maps import AnimationMap

# Cython Libraries
from libs.math import Geometry

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
                if not proj.alive():
                    # TODO: garbage collect
                    pass

# ----------------------------------------------------------------------------------------

class RemoveMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None: 
        """
        """            
        temporary = board.instances(AssetInstances.TEMPORARY)

        for effect in temporary:
            if effect.state.animation.frame > effect.properties.count:
                # TODO: implementation
                pass

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

class IntentionMechanics(Mechanic):
    """
    """
    
    def update(self, board: Board, delta: float) -> None:
        """
        Evaluates AST lambdas to transition Intentions.
        """
        sprites = board.instances(AssetInstances.SPRITES)

        for sprite in sprites:
            # TODO (Phase III): Intention logic and DSL matrix compilation is pending.

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

class PlayerMechanic(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        player = board.player()
        if not player or not board._device:
            return

        poll = board._device.poll()
        
        if poll.get("intentions"):
            player.state.intention = poll["intentions"][0]
        else:
            player.state.intention = Intentions.IDLE
        
        speed = player.state.character.speed
        goal_x = player.state.position.x
        goal_y = player.state.position.y

        if PlayerGoals.UP in poll.get("goals", []):
            goal_y -= speed
        if PlayerGoals.DOWN in poll.get("goals", []):
            goal_y += speed
        if PlayerGoals.LEFT in poll.get("goals", []):
            goal_x -= speed
        if PlayerGoals.RIGHT in poll.get("goals", []):
            goal_x += speed

        if player.state.goal:
            player.state.goal.position.x = goal_x
            player.state.goal.position.y = goal_y

        player.state.animation.action = AnimationMap.action(
            player.state, 
            board.equipment
        )

        if player.state.goal:
            player.state.animation.direction = AnimationMap.direction(
                player.state.position,
                player.state.goal.position
            )