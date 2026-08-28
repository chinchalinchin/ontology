# /home/grant/Projects/ontology/src/app/game/logic/mechanics/core.py

"""
# Ontology: app.game.logic.mechanics.core

Package for core game Mechanic implementations.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import collections

if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import AssetCategories, AssetInstances, Statuses, Intentions
from app.models.state import SpriteState
from app.game.menus.events import MenuEvent, TerminalEvent

from libs.core.math import Physics
from app.game.logic.mechanics.motion import kinematic, motive, frictive

class Mechanic(ABC):
    @abstractmethod 
    def update(self, board: Board, delta: float, bus: collections.deque) -> None:
        pass

class AnimationMechanics(Mechanic):
    def update(self, board: Board, delta: float, bus: collections.deque) -> None:
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
    def update(self, board: Board, delta_time: float, bus: collections.deque) -> None:          
        removals = []
        for effect in board.instances(AssetInstances.TEMPORARY):
            if effect.state.animation.frame >= effect.properties.count:
                removals.append(effect)
                
        for sprite in board.instances(AssetInstances.SPRITES):
            if sprite.state.mutators.triggers.dead:
                removals.append(sprite)

        board.remove(removals)

class MotionMechanics(Mechanic):
    def update(self, board: Board, delta: float, bus: collections.deque) -> None:
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

    def update(self, board: Board, delta: float, bus: collections.deque) -> None:
        # Animate Overlays (World-time)
        for overlay in board.overlays:
            for widget in overlay.widgets.values():
                widget.animation.animate(widget.state, widget.properties)
            if overlay.controller:
                overlay.controller.update(overlay, board, bus)

        # Context Control
        if not board.menus:
            if hasattr(board._device, 'context'):
                board._device.context('world')
            return

        if hasattr(board._device, 'context'):
            board._device.context('menu')
            
        active_menu = board.menus[-1]
        
        # Animate Active Menu (Menu-time)
        for widget in active_menu.widgets.values():
            widget.animation.animate(widget.state, widget.properties)
            
        active_menu.controller.update(active_menu, board, bus)

        # Input Interception
        mapping = board.poll()
        traversal = mapping.get("traversal", [])
        interactions = mapping.get("interactions", [])

        if "cancel" in interactions or "pause" in interactions:
            bus.append(TerminalEvent())
            return

        if traversal and active_menu.focus:
            direction = traversal[0]
            neighbors = active_menu.graph.get(active_menu.focus, {})
            if direction in neighbors:
                new_focus = neighbors[direction]
                active_menu.widgets[active_menu.focus].state.status = Statuses.IDLE
                active_menu.widgets[new_focus].state.status = Statuses.ACTIVE
                active_menu.focus = new_focus

        if "select" in interactions and active_menu.focus:
            active_menu.controller.select(active_menu.focus, active_menu, board, bus)