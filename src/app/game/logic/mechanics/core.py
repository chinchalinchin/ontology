"""
# Ontology: app.game.logic.mechanics.core

Package for core game Mechanic implementations.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import AssetCategories, AssetInstances
from app.models.state import SpriteState

# Cython Libraries
from libs.core.math import Physics

# Motion Strategies
from app.game.logic.mechanics.motion import kinematic, motive, frictive

class Mechanic(ABC):

    @abstractmethod 
    def update(self, board: Board, delta: float) -> None:
        pass

class AnimationMechanics(Mechanic):
    def update(self, board: Board, delta: float) -> None:
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

class RemoveMechanics(Mechanic):
    def update(self, board: Board, delta_time: float) -> None:          
        removals = []
        for effect in board.instances(AssetInstances.TEMPORARY):
            if effect.state.animation.frame >= effect.properties.count:
                removals.append(effect)
                
        for sprite in board.instances(AssetInstances.SPRITES):
            if sprite.state.mutators.triggers.dead:
                removals.append(sprite)

        board.remove(removals)

class MotionMechanics(Mechanic):
    """
    ## MotionMechanics

    Mechanic responsible for mapping internal states to strategic integrators.
    """
    def update(self, board: Board, delta: float) -> None:
        players = board.instances(AssetInstances.PLAYERS)
        sprites = board.instances(AssetInstances.SPRITES)
        crates = board.instances(AssetInstances.CRATES)
        projectiles = board.instances(AssetInstances.PROJECTILES)
        mapping = board.poll()

        kinematic.update(players, mapping, delta)
        motive.update(sprites, delta)
        frictive.update(crates, board, delta)
        
        all_mutable = players + sprites + crates + projectiles
        Physics.integrate_kinematics(all_mutable, delta)

class MenuMechanics(Mechanic):
    def equip(self, item: str, state: SpriteState, board: Board) -> None:
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
        pass