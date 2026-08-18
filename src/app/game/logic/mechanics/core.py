"""
# Ontology: app.game.logic.mechanics.core

Package for core game Mechanic implementations.
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
    AssetInstances
)

from app.models.state import SpriteState

# Cython Libraries
from libs.core.math import Geometry

# ----------------------------------------------------------------------------------------

class Mechanic(ABC):
    """
    ## Mechanic

    Foundational class for game Mechanics. Defines the `update()` interface used by the Engine.
    """

    @abstractmethod 
    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Engine interface. Injects:

        - board: Game Board
        - delta: Time Delta
        """
        pass

# ----------------------------------------------------------------------------------------

class AnimationMechanics(Mechanic):
    """
    ## AnimationMechanics

    Mechanic responsible for animating Assets.
    """

    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Iterates over animate Asset and injects state and property data into their Animation interface.
        """
        for asset in board.categories(AssetCategories.EFFECTS):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.categories(AssetCategories.SHEETS):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.CHESTS):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.GATES):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.PLATES):
            asset.animation.animate(asset.state, asset.properties)

# ----------------------------------------------------------------------------------------

class RemoveMechanics(Mechanic):
    """
    ## RemoveMechanics

    Mechanic response for garbage collecting Assets.
    """

    def update(self, board: Board, delta_time: float) -> None: 
        """
        Garbage collection for expired temporary effects and dead sprites.
        """            
        removals = []

        # 1. Identify expired Temporary Effects
        for effect in board.instances(AssetInstances.TEMPORARY):
            if effect.state.animation.frame >= effect.properties.count:
                removals.append(effect)
                
        # 2. Identify Dead Sprites
        for sprite in board.instances(AssetInstances.SPRITES):
            if sprite.state.mutators.triggers.dead:
                removals.append(sprite)

        # 3. Identify expired Projectiles
        # TODO

        # 4. Safely evict from Board tracking caches
        board.remove(removals)

# ----------------------------------------------------------------------------------------

class MotionMechanics(Mechanic):
    """
    ## MotionMechanics

    Mechanic responsible for altering Asset position.
    """

    def update(self, board: Board, delta: float) -> None:
        """
        Iterates over mutable entities and applies vectors based on speed offsets to reach their goals.
        """
        sprites = board.instances(AssetInstances.SPRITES)
        players = board.instances(AssetInstances.PLAYERS)

        for asset in sprites + players:
            if not asset.state.goal:
                continue

            dx = asset.state.goal.position.x - asset.state.position.x
            dy = asset.state.goal.position.y - asset.state.position.y

            # Entity has reached its exact target coordinate destination
            if dx == 0 and dy == 0:
                continue

            speed = asset.state.character.speed
            speed_x = speed
            speed_y = speed

            # TODO: rip out and replace with velocity-impulse-friction calculations
            
            # Integer approximation for diagonal vector normalization (~0.707)
            if dx != 0 and dy != 0:
                # max(1, ...) prevents truncation paralysis for slow entities (speed < 2)
                diag_speed = max(1, (speed * 707) // 1000)
                speed_x = diag_speed
                speed_y = diag_speed

            # Apply X Vector offset 
            if dx > 0:
                asset.state.position.x += min(speed_x, dx)
            elif dx < 0:
                asset.state.position.x -= min(speed_x, abs(dx))

            # Apply Y Vector offset
            if dy > 0:
                asset.state.position.y += min(speed_y, dy)
            elif dy < 0:
                asset.state.position.y -= min(speed_y, abs(dy))

# ----------------------------------------------------------------------------------------

class MenuMechanics(Mechanic):
    """
    ## MenuMechanics

    Mechanic responsbile for handling menu interactions.
    """

    def equip(self, item: str, state: SpriteState, board: Board) -> None:
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