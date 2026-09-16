"""
# Ontology: app.game.logic.mechanics.spatial.combat

Package for CombatMechanics
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetInstances,
    Intentions,
    Actions
)
from app.models.state import DevicePayload
from app.game.logic.mechanics.spatial import SpatialMechanic
from app.game.logic.modules.maps import CombatMap

# Cython Libraries
import libs.core.math.geometry as geometry

logger = logging.getLogger(__name__)

class CombatMechanics(SpatialMechanic):
    """
    ## CombatMechanics
    """
    def __init__(self):
        super().__init__(max_entities=2000)

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Resolves attack overlaps, decrements health, and triggers mutators.
        """
        for layer in board.layers():
            # Gather all attacking entities
            attackers = [ asset 
                for asset 
                in board.instances(AssetInstances.PLAYERS.value, layer) + \
                    board.instances(AssetInstances.SPRITES.value, layer)
                if asset.state.intention == Intentions.ATTACK
            ]
            
            if not attackers:
                continue

            melee_attackers = []
            
            for attacker in attackers:
                # ---------- ATTACKBOX HANDLING
                if attacker.state.animation.action not in [Actions.SHOOT.value, Actions.CAST.value]:
                    attackboxes = CombatMap.attackboxes(attacker.state, board.equipment)
                    melee_attackers.append((attacker, attackboxes))
                    continue

                # ---------- RANGED COMBAT HANDLING
                if attacker.state.animation.frame == 0 and \
                    not attacker.state.mutators.triggers.executed:
                    proj_id = "TODO"
                    
                    proj = board.cradle.spawn_projectile(
                        id          = proj_id,
                        layer       = attacker.state.layer,
                        position    = attacker.state.position,
                        velocity    = "TODO"
                    )

                    board.add([proj])
                    attacker.state.mutators.triggers.executed = True

                elif attacker.state.animation.frame != 0:
                    attacker.state.mutators.triggers.executed = False

            logger.info(f"attackboxes: {attackboxes}")

            if not melee_attackers:
                continue

            reactables = [
                effect for effect in board.instances(
                    AssetInstances.REACTABLES.value, layer)
                if effect.state.intention == Intentions.ATTACK.value
            ]
            targets = board.instances(AssetInstances.SPRITES.value, layer) + \
                        board.instances(AssetInstances.PLAYERS.value, layer) + \
                        reactables
            
            # Unpack melee_attackers for collision querying
            melee_assets = [a for a, hb in melee_attackers]
            colliding_pairs = self.collisions(melee_assets + targets)
            
            for asset_a, asset_b in colliding_pairs:
                # Asset A: Attacker, Asset B: Target
                if asset_a in melee_assets and asset_b in targets:
                    attacker, target = asset_a, asset_b
                # Asset A: Target, Asset B: Attacker
                elif asset_b in melee_assets and asset_a in targets:
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
                if geometry.intersects(
                    attacker.state.position, 
                    attacker.dimensions, 
                    active_hitboxes,
                    target.state.position, 
                    target.dimensions, 
                    target.hitboxes
                ) is not None:
                    if target.instance != AssetInstances.REACTABLES.value:
                        # Calculate and apply damage
                        damage = attacker.state.character.strength - target.state.character.defense
                        damage = max(1, damage)  # Minimum 1 damage on hit
                        
                        target.state.meters.health.current = max(0, 
                            target.state.meters.health.current - damage)
                        
                        if target.state.meters.health.current == 0:
                            target.state.mutators.triggers.dead = True
                    else:
                        target.state.active = True
