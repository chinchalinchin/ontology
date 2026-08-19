"""
# Ontology: app.game.logic.mechanics.spatial.combat

Package for CombatMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Intentions,
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic

# Cython Libraries
from libs.core.math import Geometry
from libs.core.models import Position

class CombatMechanics(SpatialMechanic):
    """
    ## CombatMechanics
    """
    def __init__(self):
        super().__init__(max_entities=2000)

    def update(self, board: Board, delta: float) -> None:
        """
        Resolves attack overlaps, decrements health, and triggers mutators.
        """
        for layer in board.layers():
            # Gather all attacking entities
            attackers = [
                asset 
                for asset 
                in board.instances(AssetInstances.PLAYERS, layer) + \
                    board.instances(AssetInstances.SPRITES, layer)
                if getattr(asset.state, 'intention', None) == Intentions.ATTACK.value
            ]
            
            if not attackers:
                continue

            melee_attackers = []
            
            for attacker in attackers:
                # Determine effective hitboxes (fallback to base asset hitboxes if unarmed)
                active_hitboxes = attacker.hitboxes
                weapon_key = None
                
                if getattr(attacker.state, 'inventory', None) and getattr(attacker.state.inventory, 'equipment', None):
                    weapon_key = attacker.state.inventory.equipment.weapon
                    if weapon_key and weapon_key in board.equipment.weapons:
                        weapon_props = board.equipment.weapons[weapon_key]
                        if weapon_props.hitboxes:
                            active_hitboxes = weapon_props.hitboxes

                action = attacker.state.animation.action

                # ---------------- TODO: Needs lots of work
                # Ranged Combat
                if action in ['shoot', 'cast']:
                    # Trigger projectile spawn on critical frame (frame 0) to guarantee it's fired exactly once per action loop.
                    # TODO: update frame calculation with configuration
                    if attacker.state.animation.frame == 0:
                        proj_id = "TODO"
                        
                        proj = board.cradle.spawn_projectile(
                            id          = proj_id,
                            layer       = attacker.state.layer,
                            position    = attacker.state.position,
                            velocity    = "TODO"
                        )

                        board.add([proj])
                else:
                    melee_attackers.append((attacker, active_hitboxes))

            if not melee_attackers:
                continue

            targets = board.instances(AssetInstances.SPRITES, layer) + \
                        board.instances(AssetInstances.PLAYERS, layer)
            
            # Unpack melee_attackers for collision querying
            melee_assets = [a for a, hb in melee_attackers]
            colliding_pairs = self.collisions(melee_assets + targets)
            
            for asset_a, asset_b in colliding_pairs:
                is_a_attacker = asset_a in melee_assets
                is_b_target = asset_b in targets
                is_b_attacker = asset_b in melee_assets
                is_a_target = asset_a in targets
                
                if is_a_attacker and is_b_target:
                    attacker, target = asset_a, asset_b
                elif is_b_attacker and is_a_target:
                    attacker, target = asset_b, asset_a
                else:
                    continue

                if attacker.name == target.name or target.state.mutators.triggers.dead:
                    continue
                    
                # Retrieve the active hitboxes we cached earlier
                active_hitboxes = next((
                    hb for a, hb in melee_attackers 
                    if a == attacker
                ), attacker.hitboxes)

                # The broad-phase checked the default hitboxes (because `primitive` uses `self.hitboxes`).
                # We need to narrow-phase check the specific weapon hitboxes against the target hitboxes.
                if Geometry.intersects(
                    attacker.state.position, 
                    attacker.dimensions, 
                    active_hitboxes,
                    target.state.position, 
                    target.dimensions, 
                    target.hitboxes
                ):
                    # Calculate and apply damage
                    damage = attacker.state.character.strength - target.state.character.defense
                    damage = max(1, damage)  # Minimum 1 damage on hit
                    
                    target.state.meters.health.current = max(0, 
                        target.state.meters.health.current - damage)
                    target.state.mutators.triggers.struck = True
                    
                    if target.state.meters.health.current == 0:
                        target.state.mutators.triggers.dead = True
