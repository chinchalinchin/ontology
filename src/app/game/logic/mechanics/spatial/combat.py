"""
@domain.logic
@app.mechanic
@category.sheets
@physics.space
@workflow.combat

# Ontology: Source - app.game.logic.mechanics.spatial.combat

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

from app.static.semantics import (
    AssetInstances,
    Intentions,
    Actions
)
from app.models.state import DevicePayload
from app.game.logic.mechanics.spatial import SpatialMechanic
from app.game.logic.modules.maps import CombatMap

# Cython Libraries
import libs.core.math.physics as physics

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
                in board.instances(AssetInstances.PLAYERS, layer) + \
                    board.instances(AssetInstances.SPRITES, layer)
                if asset.state.intention == Intentions.ATTACK
            ]
            
            if not attackers:
                continue

            melee_attackers = []
            
            for attacker in attackers:
                # ---------- RANGED COMBAT HANDLING
                # ---------- TODO: phase 03-04
                # ---------- ignore until then
                if attacker.state.animation.action in (
                    Actions.SHOOT, 
                    Actions.CAST,
                ):
                    continue

                # ---------- ATTACKBOX HANDLING
                attackboxes = CombatMap.attackboxes(
                    attacker.state,
                    board.equipment,
                    attacker.elevation
                )
                if attackboxes:
                    melee_attackers.append((attacker, attackboxes))

            if not melee_attackers:
                continue

            reactables = [
                effect for effect in board.instances(
                    AssetInstances.REACTABLES, layer)
                if effect.state.intention == Intentions.ATTACK
            ]
            targets = (
                board.instances(AssetInstances.SPRITES, layer) +
                board.instances(AssetInstances.PLAYERS, layer) +
                reactables
            )

            if not targets:
                continue

            # Construct indexed primitives: weapon reach for attackers, body hitboxes for targets
            attacker_map = {}
            target_map = {}
            primitives = []

            for i, (attacker, active_hitboxes) in enumerate(melee_attackers):
                attacker_map[i] = attacker
                primitives.append(attacker.primitive(i, hitboxes=active_hitboxes))

            target_offset = len(melee_attackers)
            for j, target in enumerate(targets):
                idx = target_offset + j
                target_map[idx] = target
                primitives.append(target.primitive(idx))

            # Query physics.collisions exclusively between active weapon primitives and targets
            self.grid.clear()
            colliding_indices = physics.collisions(primitives, self.grid)

            for id_a, id_b in colliding_indices:
                if id_a in attacker_map and id_b in target_map:
                    attacker, target = attacker_map[id_a], target_map[id_b]
                elif id_b in attacker_map and id_a in target_map:
                    attacker, target = attacker_map[id_b], target_map[id_a]
                else:
                    continue

                if (
                    attacker.name == target.name
                    or attacker.elevation != target.elevation
                    or target.state.mutators.triggers.dead
                ):
                    continue

                # Trigger reactable activation on confirmed attackbox intersection
                if target.instance == AssetInstances.REACTABLES:
                    target.state.active = True
                else:
                    # Calculate and apply damage
                    damage = attacker.state.character.strength - target.state.character.defense
                    damage = max(1, damage)  # Minimum 1 damage on hit

                    target.state.meters.health.current = max(
                        0, target.state.meters.health.current - damage
                    )

                    if target.state.meters.health.current == 0:
                        target.state.mutators.triggers.dead = True