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
# Standard Libraries
from typing import (
    List,
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
        """Initializes the broad-phase spatial grid for collision resolution."""
        super().__init__(cell_size=cell_size, max_entities=max_entities)

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
        resolving hitboxes matching the active collision elevation tier.
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

        intersection = geometry.intersects(
            asset_a.state.position,
            hitboxes_a,
            asset_b.state.position,
            hitboxes_b
        )

        if not intersection:
            return

        hb_a, hb_b = intersection

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
        Executes the physics loop partitioned by discrete elevation tiers.
        """
        for layer in board.layers():
            # -------------------------------------------------------------
            # PHASE 0: Incline Traversal & Elevation State Mutation
            # -------------------------------------------------------------
            stairs = board.instances(AssetInstances.STAIRS, layer)
            if stairs:
                movers = [
                    w for w in board.weights(layer)
                    if w.properties.mass > 0
                    and not w.state.mutators.triggers.falling
                ]
                for stair in stairs:
                    stair_hbs = self._stair_hitboxes(stair)
                    if not stair_hbs:
                        continue
                    for mover in movers:
                        if geometry.intersects(
                            mover.state.position,
                            mover.hitboxes,
                            stair.state.position,
                            stair_hbs,
                        ):
                            self._traverse_stairs(mover, stair)

            # -------------------------------------------------------------
            # TIER PARTITIONING
            # -------------------------------------------------------------
            weights = [
                w for w in board.weights(layer)
                if not w.state.mutators.triggers.falling
            ]
            weights_by_elevation = collections.defaultdict(list)
            for w in weights:
                # Deduplicate tiers that collapse to <= 0
                for tier in {max(0, t) for t in w.hitbox.elevations(w.properties, w.state)}:
                    weights_by_elevation[tier].append(w)

            for elevation, tier_weights in weights_by_elevation.items():
                # Phase 1: Boundary Constraints (restricted to base terrain elevation == 0)
                if elevation == 0:
                    perimeters = board.perimeters.get(layer, {}).get(elevation, [])
                    if perimeters:
                        dynamics = [
                            w for w in tier_weights
                            if w.properties.mass > 0
                        ]
                        for asset, boundary in self.constrain(dynamics, perimeters, elevation=elevation):
                            self._boundary(asset, boundary, elevation=elevation)

                # Phase 2: Dynamic Collisions
                for asset_a, asset_b in self.collisions(tier_weights, elevation=elevation):
                    self._resolve(asset_a, asset_b, elevation=elevation)