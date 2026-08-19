"""
# Ontology: app.game.logic.mechanics.core

Package for core game Mechanic implementations.
"""
# Standard Libraries
from __future__ import annotations
import math
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
from libs.core.models import Position

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

    Mechanic responsible for altering Asset position using Symplectic Euler Integration.
    """

    def update(self, board: Board, delta: float) -> None:
        """
        Applies impulses to modify velocity, then uses the resulting velocity to translate position.
        """
        players = board.instances(AssetInstances.PLAYERS)
        sprites = board.instances(AssetInstances.SPRITES)
        crates = board.instances(AssetInstances.CRATES)
        projectiles = board.instances(AssetInstances.PROJECTILES)

        # 1. Velocity Update (Player)
        mapping = board.poll()
        for player in players:
            ix, iy = 0.0, 0.0
            if 'up' in mapping.goals: iy -= 1.0
            if 'down' in mapping.goals: iy += 1.0
            if 'left' in mapping.goals: ix -= 1.0
            if 'right' in mapping.goals: ix += 1.0

            if ix != 0.0 or iy != 0.0:
                mag = math.sqrt(ix*ix + iy*iy)
                ux, uy = ix / mag, iy / mag

                impulse = getattr(player.state.character, 'impulse', 0)
                speed = player.state.character.speed

                player.state.velocity.vx += ux * impulse * delta
                player.state.velocity.vy += uy * impulse * delta

                vmag = math.sqrt(player.state.velocity.vx**2 + player.state.velocity.vy**2)
                if vmag > speed:
                    player.state.velocity.vx = (player.state.velocity.vx / vmag) * speed
                    player.state.velocity.vy = (player.state.velocity.vy / vmag) * speed
            else:
                player.state.velocity.vx = 0.0
                player.state.velocity.vy = 0.0

        # 2. Velocity Update (Sprites)
        for sprite in sprites:
            if not getattr(sprite.state, 'goal', None) or not sprite.state.goal:
                sprite.state.velocity.vx = 0.0
                sprite.state.velocity.vy = 0.0
                continue

            dx = sprite.state.goal.position.x - sprite.state.position.x
            dy = sprite.state.goal.position.y - sprite.state.position.y

            if dx == 0 and dy == 0:
                sprite.state.velocity.vx = 0.0
                sprite.state.velocity.vy = 0.0
                continue

            mag = math.sqrt(dx*dx + dy*dy)
            ux, uy = dx / mag, dy / mag

            impulse = getattr(sprite.state.character, 'impulse', 0)
            speed = sprite.state.character.speed

            sprite.state.velocity.vx += ux * impulse * delta
            sprite.state.velocity.vy += uy * impulse * delta

            vmag = math.sqrt(sprite.state.velocity.vx**2 + sprite.state.velocity.vy**2)
            if vmag > speed:
                sprite.state.velocity.vx = (sprite.state.velocity.vx / vmag) * speed
                sprite.state.velocity.vy = (sprite.state.velocity.vy / vmag) * speed

        # 3. Velocity Update (Frictive)
        for crate in crates:
            w = crate.dimensions.w if crate.dimensions else 0
            l = crate.dimensions.l if crate.dimensions else 0
            cx = crate.state.position.x + (w / 2.0)
            cy = crate.state.position.y + (l / 2.0)
            
            center_pos = Position(int(cx), int(cy))
            tile = board.tile(crate.state.layer, center_pos)

            if tile and hasattr(tile.properties, 'friction'):
                friction = tile.properties.friction
                dv = friction * delta

                vx = crate.state.velocity.vx
                vy = crate.state.velocity.vy
                vmag = math.sqrt(vx*vx + vy*vy)

                if vmag > 0:
                    if dv >= vmag:
                        crate.state.velocity.vx = 0.0
                        crate.state.velocity.vy = 0.0
                    else:
                        ux, uy = vx / vmag, vy / vmag
                        crate.state.velocity.vx -= ux * dv
                        crate.state.velocity.vy -= uy * dv

        # 4. Position Update (All Mutable Assets)
        all_mutable = players + sprites + crates + projectiles
        for asset in all_mutable:
            if not hasattr(asset.state, 'velocity') or asset.state.velocity is None:
                continue

            asset.state.position.rx += asset.state.velocity.vx * delta
            asset.state.position.ry += asset.state.velocity.vy * delta

            # When accumulators break the 1.0 | -1.0 threshold, shift absolute position
            if asset.state.position.rx >= 1.0 or asset.state.position.rx <= -1.0:
                shift = int(asset.state.position.rx)
                asset.state.position.x += shift
                asset.state.position.rx -= shift

            if asset.state.position.ry >= 1.0 or asset.state.position.ry <= -1.0:
                shift = int(asset.state.position.ry)
                asset.state.position.y += shift
                asset.state.position.ry -= shift

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