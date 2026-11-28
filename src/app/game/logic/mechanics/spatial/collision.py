"""
@domain.concrete
@domain.logic
@app.mechanic
@physics.space
@workflow.collisions

# Ontology: Source - app.game.logic.mechanics.spatial.collision

CollisionMechanics implementation.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
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

from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Directions
)
from app.game.logic.mechanics.spatial import SpatialMechanic
from app.models.state import (
    DevicePayload,
    MotiveState,
    SheetState
)

# Cython Libraries
import libs.core.math.physics as physics
import libs.core.math.geometry as geometry
from libs.core.math.space import Space
from libs.core.models import (
    Boundary,
    Hitbox,
    Position
)
# -----------------------------------------------

logger = logging.getLogger(__name__)

# Stair tread hysteresis thresholds preventing exact-boundary tier oscillation
STAIR_ASCENT_LOW: float = 0.15
STAIR_DESCENT_LOW: float = 0.10
STAIR_ASCENT_HIGH: float = 0.85
STAIR_DESCENT_HIGH: float = 0.90

# -----------------------------------------------


class CollisionMechanics(SpatialMechanic):
    """
    ## CollisionMechanics

    Mechanic responsible for resolving Asset collisions natively.
    """
    _board_ref: Optional[Board]
    _static_cache: Dict[Tuple[str, int], Tuple[int, List[Asset], List[Tuple], Space]]
    _perimeter_cache: Dict[str, Tuple[Optional[List[Boundary]], int, List[Tuple], Space]]

    @staticmethod
    def _stair_hitboxes(stairs: Asset) -> List[Hitbox]:
        """
        Resolves active blueprint hitboxes for a stair asset, falling back to full
        frame dimensions only when its HitboxSchema returns an empty list.
        """
        hitboxes = stairs.hitboxes
        if hitboxes:
            return hitboxes
        if stairs.dimensions:
            return [Hitbox(Position(0, 0), stairs.dimensions)]
        return []

    def __init__(self, cell_size: int = 64, max_entities: int = 2000):
        """Initializes the broad-phase spatial grid and versioned static caches."""
        super().__init__(cell_size=cell_size, max_entities=max_entities)
        self._board_ref = None
        self._static_cache = {}
        self._perimeter_cache = {}

    def _static_tier(
        self,
        board: Board,
        layer: str,
        elevation: int
    ) -> Tuple[List[Asset], List[Tuple], Space]:
        """
        Retrieves or builds the cached static asset list, Cython primitive buffer,
        and pre-populated Space grid for a (layer, elevation) tier keyed by
        Board.static_version(layer).
        """
        version = board.static_version(layer)
        key = (layer, elevation)
        cached = self._static_cache.get(key)
        if cached is not None and cached[0] == version:
            return cached[1], cached[2], cached[3]

        tier_statics = board.statics(layer, elevation)
        active_statics: List[Asset] = []
        static_primitives: List[Tuple] = []
        idx = 0
        for asset in tier_statics:
            hbs = asset.hitbox.get(asset.properties, asset.state, elevation)
            if not hbs:
                continue
            static_primitives.append(asset.primitive(idx, hbs))
            active_statics.append(asset)
            idx += 1

        static_grid = (
            cached[3]
            if cached is not None
            else Space(
                cell_size=self.grid.cell_size,
                max_entities=max(self.grid.max_entities, len(active_statics) + 64)
            )
        )
        physics.populate_statics(static_primitives, static_grid)
        self._static_cache[key] = (version, active_statics, static_primitives, static_grid)
        return active_statics, static_primitives, static_grid

    def _perimeter_tier(
        self,
        layer: str,
        perimeters: List[Boundary]
    ) -> Tuple[List[Tuple], Space]:
        """
        Retrieves or builds the cached perimeter primitive buffer and pre-populated
        Space grid for base terrain (elevation == 0) boundary constraints.
        """
        cached = self._perimeter_cache.get(layer)
        perim_len = len(perimeters)
        if cached is not None and cached[0] is perimeters and cached[1] == perim_len:
            return cached[2], cached[3]

        bound_primitives = [
            (i, b.position.x, b.position.y, b.dimensions.w, b.dimensions.l)
            for i, b in enumerate(perimeters)
        ]
        bound_grid = (
            cached[3]
            if cached is not None
            else Space(
                cell_size=self.grid.cell_size,
                max_entities=max(256, perim_len + 32)
            )
        )
        physics.populate_bounds(bound_primitives, bound_grid)
        self._perimeter_cache[layer] = (perimeters, perim_len, bound_primitives, bound_grid)
        return bound_primitives, bound_grid

    def _traverse_stairs(self, sprite: Asset, stairs: Asset) -> None:
        """
        Evaluates dynamic body progression across stair tread bounds and shifts elevation.
        Combines normalized sensory foot-anchor positioning with directional velocity
        gating to prevent premature tier transitions and boundary snapping.
        """
        e_base = stairs.elevation
        e_top = e_base + stairs.state.delta
        curr_e = sprite.elevation
        prev_e = sprite.elevation

        # Entity must be on either the base or summit tier of the stair incline
        if curr_e != e_base and curr_e != e_top:
            return

        direction = stairs.state.blueprint

        vel = (
            sprite.state.velocity
            if isinstance(sprite.state, (SheetState, MotiveState))
            else None
        )
        vx = vel.vx if vel is not None else 0.0
        vy = vel.vy if vel is not None else 0.0

        # Calculate sensory ground contact point (center-x, bottom-y) from active hitboxes
        mover_hbs = sprite.hitboxes
        if mover_hbs:
            hb_min_x = min(
                sprite.state.position.x + hb.position.x
                for hb in mover_hbs
            )
            hb_max_x = max(
                sprite.state.position.x + hb.position.x + hb.dimensions.w
                for hb in mover_hbs
            )
            hb_max_y = max(
                sprite.state.position.y + hb.position.y + hb.dimensions.l
                for hb in mover_hbs
            )
            foot_x = (hb_min_x + hb_max_x) // 2
            foot_y = hb_max_y
        else:
            dim_w = sprite.dimensions.w if sprite.dimensions else 0
            dim_l = sprite.dimensions.l if sprite.dimensions else 0
            foot_x = sprite.state.position.x + (dim_w // 2)
            foot_y = sprite.state.position.y + dim_l

        # Resolve active stair tread bounds from blueprint hitboxes (fallback to dimensions)
        stair_hbs = self._stair_hitboxes(stairs)
        if not stair_hbs:
            return

        min_x = min(stairs.state.position.x + hb.position.x for hb in stair_hbs)
        min_y = min(stairs.state.position.y + hb.position.y for hb in stair_hbs)
        max_x = max(
            stairs.state.position.x + hb.position.x + hb.dimensions.w
            for hb in stair_hbs
        )
        max_y = max(
            stairs.state.position.y + hb.position.y + hb.dimensions.l
            for hb in stair_hbs
        )
        stair_w = max_x - min_x
        stair_l = max_y - min_y

        # -----------------------------------------------------------------
        # VERTICAL STAIRS (UP)
        # -----------------------------------------------------------------
        # NOTE: DOWN is impossible due to LPC perspective specification.
        if direction == Directions.UP:
            if stair_l == 0:
                return

            tread_progress = (foot_y - min_y) / stair_l

            # Ascent moves North (vy < 0); Descent moves South (vy > 0)
            if tread_progress <= STAIR_ASCENT_HIGH and vy < 0:
                sprite.elevation = e_top
            elif tread_progress >= STAIR_DESCENT_HIGH and vy > 0:
                sprite.elevation = e_base

        # -----------------------------------------------------------------
        # HORIZONTAL STAIRS (LEFT / RIGHT)
        # -----------------------------------------------------------------
        elif direction in (
            Directions.LEFT,
            Directions.RIGHT
        ):
            if stair_w == 0:
                return

            tread_progress = (foot_x - min_x) / stair_w

            if direction == Directions.RIGHT:
                # Ascent moves East (vx > 0); Descent moves West (vx < 0)
                if tread_progress >= STAIR_ASCENT_LOW and vx > 0:
                    sprite.elevation = e_top
                elif tread_progress <= STAIR_DESCENT_LOW and vx < 0:
                    sprite.elevation = e_base

            elif direction == Directions.LEFT:
                # Ascent moves West (vx < 0); Descent moves East (vx > 0)
                if tread_progress <= STAIR_ASCENT_HIGH and vx < 0:
                    sprite.elevation = e_top
                elif tread_progress >= STAIR_DESCENT_HIGH and vx > 0:
                    sprite.elevation = e_base

        if sprite.elevation != prev_e:
            logger.info(
                f"Telemetry:Stairs:{sprite.name} traversed {stairs.name} "
                f"dir={direction} progress={tread_progress:.2f} "
                f"foot=({foot_x},{foot_y}) vel=({vx:.1f},{vy:.1f}) "
                f"elevation: {prev_e} -> {sprite.elevation}"
            )

    def _boundary(self, asset: Asset, boundary: Boundary, elevation: int) -> None:
        """
        Delegates Asset vs Boundary interaction to the specialized Cython constraint solver,
        evaluating hitboxes specific to the active elevation tier.
        """
        is_kinematic = asset.taxonomy.instance == AssetInstances.PLAYERS
        mass = asset.properties.mass

        # Static environment architecture (m == 0) cannot be shifted by boundary hulls
        if mass == 0 and not is_kinematic:
            return

        vel = (
            asset.state.velocity
            if isinstance(asset.state, (SheetState, MotiveState))
            else None
        )
        hitboxes = (
            asset.hitbox.get(asset.properties, asset.state, elevation)
            if elevation is not None
            else asset.hitboxes
        )

        intersection = geometry.bounded(
            int(asset.state.position.x),
            int(asset.state.position.y),
            hitboxes,
            boundary.position.x,
            boundary.position.y,
            boundary.dimensions.w,
            boundary.dimensions.l
        )

        if not intersection:
            return

        hb = intersection[0]
        physics.constrain(
            asset.state.position,
            hb,
            vel,
            is_kinematic,
            boundary.position.x,
            boundary.position.y,
            boundary.dimensions.w,
            boundary.dimensions.l
        )

    def _resolve(self, asset_a: Asset, asset_b: Asset, elevation: int) -> None:
        """
        Extract variables logically and defer matrix shifts to Cython,
        resolving all intersecting hitbox pairs at the active collision elevation
        tier so compound multi-hitbox obstacles resolve cleanly in a single tick.
        """
        m1 = asset_a.properties.mass
        m2 = asset_b.properties.mass

        is_kinematic1 = asset_a.taxonomy.instance == AssetInstances.PLAYERS
        is_kinematic2 = asset_b.taxonomy.instance == AssetInstances.PLAYERS

        vel1 = (
            asset_a.state.velocity
            if isinstance(asset_a.state, (SheetState, MotiveState))
            else None
        )
        vel2 = (
            asset_b.state.velocity
            if isinstance(asset_b.state, (SheetState, MotiveState))
            else None
        )

        hitboxes_a = (
            asset_a.hitbox.get(asset_a.properties, asset_a.state, elevation)
            if elevation is not None
            else asset_a.hitboxes
        )
        hitboxes_b = (
            asset_b.hitbox.get(asset_b.properties, asset_b.state, elevation)
            if elevation is not None
            else asset_b.hitboxes
        )

        pairs = geometry.intersections(
            asset_a.state.position,
            hitboxes_a,
            asset_b.state.position,
            hitboxes_b
        )

        if not pairs:
            return

        # Resolve deepest overlap area first to prevent internal-seam ghost nudges
        if len(pairs) > 1:
            pos_a = asset_a.state.position
            pos_b = asset_b.state.position
            pairs.sort(
                key=lambda pair: (
                    min(
                        pos_a.x + pair[0].position.x + pair[0].dimensions.w,
                        pos_b.x + pair[1].position.x + pair[1].dimensions.w
                    ) - max(
                        pos_a.x + pair[0].position.x,
                        pos_b.x + pair[1].position.x
                    )
                ) * (
                    min(
                        pos_a.y + pair[0].position.y + pair[0].dimensions.l,
                        pos_b.y + pair[1].position.y + pair[1].dimensions.l
                    ) - max(
                        pos_a.y + pair[0].position.y,
                        pos_b.y + pair[1].position.y
                    )
                ),
                reverse=True
            )

        for hb_a, hb_b in pairs:
            physics.collide(
                asset_a.state.position,
                hb_a,
                vel1,
                m1,
                is_kinematic1,
                asset_b.state.position,
                hb_b,
                vel2,
                m2,
                is_kinematic2
            )

    def update(self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Executes the physics loop partitioned by active dynamic elevation tiers,
        skipping layers and tiers without non-falling dynamic bodies and avoiding
        static-vs-static hashing or resolution.
        """
        if self._board_ref is not board:
            self._static_cache.clear()
            self._perimeter_cache.clear()
            self._board_ref = board

        for layer in board.layers():
            dynamics = [
                d for d in board.dynamics(layer)
                if not d.state.mutators.triggers.falling
            ]
            if not dynamics:
                continue

            # -------------------------------------------------------------
            # PHASE 0: Incline Traversal & Elevation State Mutation
            # -------------------------------------------------------------
            stairs = board.instances(AssetInstances.STAIRS, layer)
            if stairs:
                for stair in stairs:
                    stair_hbs = self._stair_hitboxes(stair)
                    if not stair_hbs:
                        continue
                    for mover in dynamics:
                        if geometry.intersects(
                            mover.state.position,
                            mover.hitboxes,
                            stair.state.position,
                            stair_hbs,
                        ):
                            self._traverse_stairs(mover, stair)

            # -------------------------------------------------------------
            # ACTIVE-TIER PARTITIONING (Dynamic Bodies Only)
            # -------------------------------------------------------------
            dynamics_by_elevation: Dict[int, List[Asset]] = collections.defaultdict(list)
            for dyn in dynamics:
                elevs = dyn.hitbox.elevations(dyn.properties, dyn.state)
                if len(elevs) == 1:
                    dynamics_by_elevation[max(0, elevs[0])].append(dyn)
                elif elevs:
                    # Deduplicate tiers that collapse to <= 0
                    for tier in {max(0, t) for t in elevs}:
                        dynamics_by_elevation[tier].append(dyn)

            for elevation, tier_dynamics in dynamics_by_elevation.items():
                tier_dyn_primitives = [
                    asset.primitive(
                        i,
                        asset.hitbox.get(asset.properties, asset.state, elevation)
                    )
                    for i, asset in enumerate(tier_dynamics)
                ]

                # Phase 1: Boundary Constraints (restricted to base terrain elevation == 0)
                if elevation == 0:
                    layer_perims = board.perimeters.get(layer)
                    perimeters = layer_perims.get(elevation) if layer_perims is not None else None
                    if perimeters:
                        bound_prims, bound_grid = self._perimeter_tier(layer, perimeters)
                        bound_hits = physics.query_bounds(
                            tier_dyn_primitives,
                            bound_prims,
                            bound_grid
                        )
                        if bound_hits:
                            shifted = set()
                            for dyn_idx, bound_idx in bound_hits:
                                self._boundary(
                                    tier_dynamics[dyn_idx],
                                    perimeters[bound_idx],
                                    elevation=elevation
                                )
                                shifted.add(dyn_idx)
                            for dyn_idx in shifted:
                                tier_dyn_primitives[dyn_idx] = tier_dynamics[dyn_idx].primitive(
                                    dyn_idx,
                                    tier_dyn_primitives[dyn_idx][5]
                                )

                # Phase 2A: Dynamic-vs-Dynamic Collisions
                if len(tier_dynamics) > 1:
                    dyn_hits = physics.collisions(tier_dyn_primitives, self.grid)
                    if dyn_hits:
                        shifted = set()
                        for id_a, id_b in dyn_hits:
                            self._resolve(
                                tier_dynamics[id_a],
                                tier_dynamics[id_b],
                                elevation=elevation
                            )
                            shifted.add(id_a)
                            shifted.add(id_b)
                        for dyn_idx in shifted:
                            tier_dyn_primitives[dyn_idx] = tier_dynamics[dyn_idx].primitive(
                                dyn_idx,
                                tier_dyn_primitives[dyn_idx][5]
                            )

                # Phase 2B: Dynamic-vs-Static Bipartite Collisions (persistent static Space)
                tier_statics, static_primitives, static_grid = self._static_tier(
                    board,
                    layer,
                    elevation
                )
                if tier_statics:
                    for dyn_idx, stat_idx in physics.query_statics(
                        tier_dyn_primitives,
                        static_primitives,
                        static_grid
                    ):
                        self._resolve(
                            tier_dynamics[dyn_idx],
                            tier_statics[stat_idx],
                            elevation=elevation
                        )