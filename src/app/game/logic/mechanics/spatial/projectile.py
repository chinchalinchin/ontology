"""
@domain.concrete
@domain.logic
@app.mechanic
@physics.space
@workflow.projectiles

# Ontology: Source - app.game.logic.mechanics.spatial.projectile

Package for ProjectileMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import (
    Dict,
    List,
    Set,
    Tuple,
    TYPE_CHECKING
)
import collections
import logging

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

import app.static.settings as settings
from app.assets.base import Asset
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Intentions
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.physics as physics

logger = logging.getLogger(__name__)


class ProjectileMechanics(SpatialMechanic):
    """
    ## ProjectileMechanics

    Mechanic responsible for evaluating projectile range/boundary expiration,
    elevation-partitioned impact resolution against obstacles and targets,
    and immediate garbage collection via Board.remove().
    """

    def __init__(self):
        super().__init__(max_entities=1000)

    @staticmethod
    def _layer_bounds(board: Board, layer: str) -> Tuple[int, int]:
        """
        Computes the static tile extent (width, length) of a layer without
        incorporating transient projectile positions.
        """
        max_w = 0
        max_l = 0
        for tile in board.categories(AssetCategories.TILES, layer):
            ext_w = int(tile.state.position.x) + (
                tile.state.multiple.nx * tile.properties.dimensions.w
            )
            ext_l = int(tile.state.position.y) + (
                tile.state.multiple.ny * tile.properties.dimensions.l
            )
            if ext_w > max_w:
                max_w = ext_w
            if ext_l > max_l:
                max_l = ext_l
        return (max_w, max_l)

    def _resolve_elevation(
        self,
        projectiles: List[Asset],
        elevation: int,
        layer: str,
        board: Board,
        impacted: Set[Asset]
    ) -> None:
        """
        Evaluates narrow-phase intersections between projectiles and obstacles,
        characters, and attack-keyed reactables on a single discrete elevation plane.
        """
        characters = [
            asset
            for asset in (
                board.instances(AssetInstances.SPRITES, layer, elevation) +
                board.instances(AssetInstances.PLAYERS, layer, elevation)
            )
            if not asset.state.mutators.triggers.dead
        ]
        reactables = [
            effect
            for effect in board.instances(AssetInstances.REACTABLES, layer, elevation)
            if effect.state.intention == Intentions.ATTACK
        ]
        obstacles = board.obstacles(layer, elevation)

        # Deduplicate target candidates while preserving characters/reactables first
        seen_ids: Set[int] = set()
        targets: List[Asset] = []
        for candidate in characters + reactables + obstacles:
            cid = id(candidate)
            if cid not in seen_ids:
                seen_ids.add(cid)
                targets.append(candidate)

        if not targets:
            return

        proj_map: Dict[int, Asset] = {}
        target_map: Dict[int, Asset] = {}
        primitives = []

        for proj in projectiles:
            proj_hbs = proj.hitbox.get(proj.properties, proj.state, elevation)
            if not proj_hbs:
                continue
            idx = len(primitives)
            proj_map[idx] = proj
            primitives.append(proj.primitive(idx, hitboxes=proj_hbs))

        if not proj_map:
            return

        for target in targets:
            target_hbs = target.hitbox.get(target.properties, target.state, elevation)
            if not target_hbs:
                continue
            idx = len(primitives)
            target_map[idx] = target
            primitives.append(target.primitive(idx, hitboxes=target_hbs))

        if not target_map:
            return

        self.grid.clear()
        colliding_indices = physics.collisions(primitives, self.grid)

        for id_a, id_b in colliding_indices:
            if id_a in proj_map and id_b in target_map:
                proj, target = proj_map[id_a], target_map[id_b]
            elif id_b in proj_map and id_a in target_map:
                proj, target = proj_map[id_b], target_map[id_a]
            else:
                continue

            if proj in impacted:
                continue

            # Exclude launching entity from self-impact
            if proj.state.owner and target.name == proj.state.owner:
                continue

            if target.instance in (AssetInstances.SPRITES, AssetInstances.PLAYERS):
                if target.state.mutators.triggers.dead:
                    continue

                raw_power = round(
                    proj.state.speed / settings.PROJECTILE_BASE_SPEED_FACTOR
                )
                defense = target.state.character.defense if target.state.character else 0
                damage = max(1, raw_power - defense)

                target.state.meters.health.current = max(
                    0, target.state.meters.health.current - damage
                )
                if target.state.meters.health.current == 0:
                    target.state.mutators.triggers.dead = True

                impacted.add(proj)

            elif target.instance == AssetInstances.REACTABLES:
                target.state.active = True
                impacted.add(proj)

            else:
                impacted.add(proj)

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Evaluates range/boundary expiration and elevation-partitioned impacts,
        removing expired or impacted projectiles immediately.
        """
        max_range_sq = settings.PROJECTILE_MAX_RANGE * settings.PROJECTILE_MAX_RANGE

        for layer in board.layers():
            projectiles = board.instances(AssetInstances.PROJECTILES, layer)
            if not projectiles:
                continue

            layer_w, layer_l = self._layer_bounds(board, layer)
            removals: Set[Asset] = set()
            by_elevation: Dict[int, List[Asset]] = {}

            # Phase 1: Range & Layer-Bound Expiration
            for proj in projectiles:
                px = proj.state.position.x
                py = proj.state.position.y
                dw = proj.dimensions.w if proj.dimensions else 0
                dl = proj.dimensions.l if proj.dimensions else 0

                dx = px - proj.state.initial.x
                dy = py - proj.state.initial.y

                out_of_range = (dx * dx + dy * dy) >= max_range_sq
                out_of_bounds = (
                    (px + dw) < 0
                    or (py + dl) < 0
                    or (layer_w > 0 and px > layer_w)
                    or (layer_l > 0 and py > layer_l)
                )

                if out_of_range or out_of_bounds:
                    removals.add(proj)
                    continue

                by_elevation.setdefault(proj.elevation, []).append(proj)

            # Phase 2: Ground-Tier Perimeter Boundary Expiration
            layer_perimeters = board.perimeters.get(layer)
            if layer_perimeters and 0 in by_elevation:
                ground_bounds = layer_perimeters.get(0)
                if ground_bounds:
                    ground_hits = self.constrain(
                        by_elevation[0],
                        ground_bounds,
                        elevation=0
                    )
                    for proj, _ in ground_hits:
                        removals.add(proj)
                    by_elevation[0] = [
                        p for p in by_elevation[0] if p not in removals
                    ]
                    
            # Phase 3: Elevation-Partitioned Obstacle & Target Impacts
            for elevation, elev_projectiles in by_elevation.items():
                if not elev_projectiles:
                    continue
                self._resolve_elevation(
                    elev_projectiles,
                    elevation,
                    layer,
                    board,
                    removals
                )

            if removals:
                board.remove(list(removals))