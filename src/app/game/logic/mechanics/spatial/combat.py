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
from typing import (
    List,
    Optional,
    Tuple,
    TYPE_CHECKING
)
import collections
import logging

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.logic.relations import ProjectileIndex

from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Intentions,
    Relations
)
from app.models.state import DevicePayload
from app.game.logic.mechanics.spatial import SpatialMechanic
from app.game.logic.modules.maps import CombatMap

# Cython Libraries
import libs.core.math.physics as physics
from libs.core.models import Hitbox

logger = logging.getLogger(__name__)


class CombatMechanics(SpatialMechanic):
    """
    ## CombatMechanics

    Dispatches attacking entities between ranged projectile emission (`_project`)
    and batched melee intersection resolution (`_melee`) via ProjectileIndex.
    """

    def __init__(self):
        super().__init__(max_entities=2000)

    @property
    def relation(self) -> Optional[ProjectileIndex]:
        return self.relations.get(Relations.PROJECTILES)

    @relation.setter
    def relation(self, relation: Optional[ProjectileIndex]) -> None:
        if relation is None:
            self.relations.pop(Relations.PROJECTILES, None)
        else:
            self.relations[Relations.PROJECTILES] = relation

    def _project(
        self,
        attacker: Asset,
        projectile_id: str,
        board: Board
    ) -> None:
        """
        Resolves ranged release frame geometry, charged launch speed, and
        projectile instantiation via Cradle.
        """
        release = CombatMap.release(
            attacker.state,
            board.equipment,
            attacker.elevation
        )
        if release is None:
            return

        spawn_pos, direction = release
        speed = CombatMap.speed(attacker.state, board.equipment)
        projectile = board.cradle.spawn_projectile(
            id=projectile_id,
            position=spawn_pos,
            layer=attacker.state.layer,
            direction=direction,
            speed=speed,
            elevation=attacker.elevation,
            owner=attacker.name
        )
        board.add([projectile])

        if attacker.state.mutators.parameters:
            attacker.state.mutators.parameters.charge = 0

    def _melee(
        self,
        melee_attackers: List[Tuple[Asset, List[Hitbox]]],
        layer: str,
        board: Board
    ) -> None:
        """
        Resolves batched narrow-phase melee attackbox overlaps, decrements health,
        and triggers reactables and death mutators.
        """
        reactables = [
            effect
            for effect in board.instances(AssetInstances.REACTABLES, layer)
            if effect.state.intention == Intentions.ATTACK
        ]
        targets = (
            board.instances(AssetInstances.SPRITES, layer) +
            board.instances(AssetInstances.PLAYERS, layer) +
            reactables
        )

        if not targets:
            return

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

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Forks attacking entities between ranged projectile emission and melee combat.
        """
        for layer in board.layers():
            # Gather all attacking entities
            attackers = [
                asset
                for asset in (
                    board.instances(AssetInstances.PLAYERS, layer) +
                    board.instances(AssetInstances.SPRITES, layer)
                )
                if asset.state.intention == Intentions.ATTACK
            ]

            if not attackers:
                continue

            melee_attackers: List[Tuple[Asset, List[Hitbox]]] = []

            for attacker in attackers:
                # ---------- RANGED COMBAT HANDLING
                projectile_id = CombatMap.projectile(attacker.state, self.relation)
                if projectile_id is not None:
                    self._project(attacker, projectile_id, board)
                    continue

                # ---------- ATTACKBOX HANDLING
                attackboxes = CombatMap.attackboxes(
                    attacker.state,
                    board.equipment,
                    attacker.elevation
                )
                if attackboxes:
                    melee_attackers.append((attacker, attackboxes))

            if melee_attackers:
                self._melee(melee_attackers, layer, board)