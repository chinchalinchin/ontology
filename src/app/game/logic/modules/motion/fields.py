"""
@domain.logic
@app.module
@physics.fields
@workflow.fluids
@workflow.gravity

# Ontology: Source - app.game.logic.modules.motion.fields
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    List, 
    Tuple, 
    Dict,
    Optional,
    Any, 
    TYPE_CHECKING
)

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
    EffectsPalette
)
from app.game.logic.relations import MaterialIndex

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.geometry as geometry
import libs.core.math.physics as physics
from libs.core.math.space import Space
from libs.core.models import Position

logger = logging.getLogger(__name__)

DIRECTION_VECTORS = {
    Directions.UP.value: (0.0, -1.0),
    Directions.DOWN.value: (0.0, 1.0),
    Directions.LEFT.value: (-1.0, 0.0),
    Directions.RIGHT.value: (1.0, 0.0),
}

SHORELINE_NORMALS = {
    Directions.UP.value: (0.0, 1.0),     # Land North -> Inward water normal points South (+Y)
    Directions.DOWN.value: (0.0, -1.0),  # Land South -> Inward water normal points North (-Y)
    Directions.LEFT.value: (1.0, 0.0),   # Land West  -> Inward water normal points East (+X)
    Directions.RIGHT.value: (-1.0, 0.0), # Land East  -> Inward water normal points West (-X)
}


def _direction_vector(source: Any) -> Tuple[float, float]:
    direction = source.value if hasattr(source, "value") else str(source)
    return DIRECTION_VECTORS.get(direction, (0.0, 0.0))


def _shoreline_normal(orientation: Any) -> Tuple[float, float]:
    direction = orientation.value if hasattr(orientation, "value") else str(orientation)
    return SHORELINE_NORMALS.get(direction, (0.0, 0.0))


def _fluid_velocity(fluid: Asset) -> Tuple[float, float]:
    ux, uy = _direction_vector(fluid.state.source)
    speed = fluid.state.flow * settings.BASE_FLOW_SPEED
    return ux * speed, uy * speed


def _extract_compound_sensor_primitives(
    sensors: List[Asset]
) -> Tuple[List[Tuple], List[Asset]]:
    """
    Decomposes assets with compound hitboxes into discrete primitive tuples
    while maintaining a 1:1 lookup index to parent entities.
    """
    primitives: List[Tuple] = []
    lookup: List[Asset] = []
    idx = 0
    for sensor in sensors:
        sx = sensor.state.position.x
        sy = sensor.state.position.y
        for hb in sensor.hitboxes:
            primitives.append((
                idx,
                sx + hb.position.x,
                sy + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l,
                [hb]
            ))
            lookup.append(sensor)
            idx += 1
    return primitives, lookup


def _extract_tier_support_aabbs(
    board: Board,
    layer: str,
    elevation: int
) -> List[Tuple[int, int, int, int]]:
    """
    Extracts primitive (x, y, w, l) AABB tuples for all walkable substrates
    at discrete elevation tier E > 0.
    """
    aabbs: List[Tuple[int, int, int, int]] = []

    for craft in board.categories(AssetCategories.CRAFTS.value, layer):
        inst = craft.taxonomy.instance
        base_e = craft.elevation

        if inst == AssetInstances.STAIRS.value:
            # Use full stair tread bounds so ascending/descending entities remain supported
            if base_e < elevation <= base_e + craft.state.delta:
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

        elif inst == AssetInstances.BRIDGES.value:
            if base_e == elevation:
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

        elif inst == AssetInstances.STRUTS.value:
            # Support sensor struts (mass < 0) and passable surface blueprints at tier E
            if base_e == elevation and (
                craft.properties.mass < 0
                or not MaterialIndex().is_obstacle(craft.state.blueprint)
                or not craft.hitbox.elevations(craft.properties, craft.state)
            ):
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

    return aabbs


def _is_supported_at_tier(
    asset: Asset,
    elevation: int,
    support_cache: Dict[int, List[Tuple[int, int, int, int]]],
    board: Board,
    layer: str
) -> bool:
    """
    Returns True if any active hitbox (or bounding box) of the asset overlaps
    a walkable substrate AABB at the given elevation tier.
    Tier 0 (base terrain) is unconditionally supported.
    """
    if elevation <= 0:
        return True
    if elevation not in support_cache:
        support_cache[elevation] = _extract_tier_support_aabbs(board, layer, elevation)
    support_aabbs = support_cache[elevation]
    if not support_aabbs:
        return False

    ax = int(asset.state.position.x)
    ay = int(asset.state.position.y)
    hbs = (
        asset.hitbox.get(asset.properties, asset.state, elevation)
        if asset.hitbox is not None
        else []
    )
    if hbs:
        for hb in hbs:
            if geometry.occluded(
                ax + hb.position.x,
                ay + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l,
                support_aabbs
            ):
                return True
        return False

    return bool(
        geometry.occluded(ax, ay, asset.dimensions.w, asset.dimensions.l, support_aabbs)
    )


def _update_gravity(
    l_assets: List[Asset],
    board: Board,
    layer: str,
    delta: float
) -> set[int]:
    """
    Evaluates elevated support, accelerates unsupported entities downward (+Y),
    and decrements elevation E -> E - 1 per geometric TIER_DROP_DISTANCE.
    """
    falling_indices: set[int] = set()
    support_cache: Dict[int, List[Tuple[int, int, int, int]]] = {}

    for i, asset in enumerate(l_assets):
        if asset.elevation <= 0 and not asset.state.mutators.triggers.falling:
            continue

        if asset.elevation <= 0:
            asset.elevation = 0
            asset.state.mutators.triggers.falling = False
            asset.state.mutators.parameters.descension = 0.0
            continue

        is_falling = asset.state.mutators.triggers.falling

        # 1. Check if entity at E > 0 has stepped off its supporting substrate
        if not is_falling:
            if not _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer):
                asset.state.mutators.triggers.falling = True
                asset.state.mutators.parameters.descension = 0.0
                asset.state.position.ry = 0.0
                asset.state.velocity.vy = max(0.0, asset.state.velocity.vy)
                is_falling = True

        if not is_falling:
            continue

        # 2. Integrate constant gravitational acceleration (+Y) while preserving vx
        asset.state.velocity.vy = min(
            settings.TERMINAL_VELOCITY,
            asset.state.velocity.vy + (settings.GRAVITY_ACCELERATION * delta)
        )

        # Compute integer vertical step matching physics.integrate sub-pixel accumulation
        total_ry = asset.state.position.ry + (asset.state.velocity.vy * delta)
        step_y = int(total_ry)
        rem_to_tier = int(settings.TIER_DROP_DISTANCE - asset.state.mutators.parameters.descension)

        # 3. Evaluate discrete tier transitions (E -> E - 1)
        if step_y >= rem_to_tier and asset.elevation > 0:
            orig_y = asset.state.position.y
            rem_y = step_y
            advanced_y = 0
            landed = False

            while rem_y >= rem_to_tier and asset.elevation > 0:
                advanced_y += rem_to_tier
                rem_y -= rem_to_tier
                asset.state.position.y = orig_y + advanced_y
                asset.elevation -= 1

                if _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer):
                    # Landed on supported plane E - 1: clamp exact drop and zero velocity
                    asset.state.mutators.triggers.falling = False
                    asset.state.mutators.parameters.descension = 0.0
                    asset.state.position.ry = 0.0
                    asset.state.velocity.vy = 0.0
                    landed = True
                    break

                rem_to_tier = settings.TIER_DROP_DISTANCE

            if not landed:
                # Unsupported at intermediate plane: restore y for full physics.integrate step
                asset.state.position.y = orig_y
                asset.state.mutators.parameters.descension = float(rem_y)
                falling_indices.add(i)
        else:
            asset.state.mutators.parameters.descension += float(step_y)
            falling_indices.add(i)

    return falling_indices


def _update_rafts(rafts: List[Asset], board: Board, grid: Space) -> None:
    """
    Passively accelerates dynamic Rafts along intersecting fluid current vectors.
    """
    if not rafts:
        return

    layer_rafts: Dict[str, List[Asset]] = {}
    for raft in rafts:
        layer_rafts.setdefault(raft.state.layer, []).append(raft)

    for layer, l_rafts in layer_rafts.items():
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        if not fluids:
            for raft in l_rafts:
                raft.state.velocity.vx = 0.0
                raft.state.velocity.vy = 0.0
            continue

        raft_primitives = [r.primitive(i) for i, r in enumerate(l_rafts)]
        fluid_primitives, fluid_lookup = _extract_compound_sensor_primitives(fluids)

        if not fluid_primitives:
            for raft in l_rafts:
                raft.state.velocity.vx = 0.0
                raft.state.velocity.vy = 0.0
            continue

        matches = physics.environment(raft_primitives, fluid_primitives, grid)

        raft_flows: Dict[int, Tuple[float, float]] = {
            i: (0.0, 0.0) for i in range(len(l_rafts))
        }
        intersected: set[int] = set()

        for r_idx, f_prim_idx in matches:
            fluid = fluid_lookup[f_prim_idx]
            fvx, fvy = _fluid_velocity(fluid)
            cvx, cvy = raft_flows[r_idx]
            raft_flows[r_idx] = (cvx + fvx, cvy + fvy)
            intersected.add(r_idx)

        for i, raft in enumerate(l_rafts):
            if i in intersected:
                flow_vx, flow_vy = raft_flows[i]
                raft.state.velocity.vx = flow_vx
                raft.state.velocity.vy = flow_vy
            else:
                raft.state.velocity.vx = 0.0
                raft.state.velocity.vy = 0.0


def update(
    assets: List[Asset], 
    board: Board, 
    delta: float, 
    grid: Optional[Space] = None
) -> None:
    """
    Executes environmental field resolution pass across active mutable entities
    using bipartite C-grid space hashing:
    0. Geometric gravity evaluation and multi-tier freefall stepping.
    1. Passive hydrodynamic drift for Rafts.
    2. Surface Interception (Bridges & Rafts) suppressing submersion and shoreline edge checks.
    3. Virtual Edge Traversals (Shorelines) with drop nudges and splash particles.
    4. Direct Immersion (Fluids) with vector superposition and submerged activation.
    """
    if grid is None:
        grid = Space()

    rafts = [
        a for a in assets 
        if a.instance == AssetInstances.RAFTS.value
    ]
    _update_rafts(rafts, board, grid)

    target_assets = [
        a for a in assets 
        if a.instance not in (
            AssetInstances.RAFTS.value, 
            AssetInstances.PROJECTILES.value
        )
    ]

    if not target_assets:
        return

    # Partition targets by layer
    layer_assets: Dict[str, List[Asset]] = {}
    for asset in target_assets:
        layer_assets.setdefault(asset.state.layer, []).append(asset)

    for layer, l_assets in layer_assets.items():
        # -------------------------------------------------------------
        # 0. GRAVITY & ELEVATION TIER SUPPORT
        # -------------------------------------------------------------
        falling_indices = _update_gravity(l_assets, board, layer, delta)
        l_assets = [
            a for i, a in enumerate(l_assets)
            if i not in falling_indices
        ]
        if not l_assets:
            continue

        asset_primitives = [a.primitive(i) for i, a in enumerate(l_assets)]
        on_surface_indices: set[int] = set()

        # -------------------------------------------------------------
        # 1. SURFACE HIERARCHY INTERCEPTION (BRIDGES & RAFTS)
        # -------------------------------------------------------------
        layer_bridges = board.instances(AssetInstances.BRIDGES.value, layer)
        if layer_bridges:
            bridge_prims, _ = _extract_compound_sensor_primitives(layer_bridges)
            if bridge_prims:
                bridge_matches = physics.environment(asset_primitives, bridge_prims, grid)
                for a_idx, _ in bridge_matches:
                    on_surface_indices.add(a_idx)
                    asset = l_assets[a_idx]
                    asset.state.mutators.triggers.submerged = False

        layer_rafts = board.instances(AssetInstances.RAFTS.value, layer)
        if layer_rafts:
            raft_prims = [r.primitive(i) for i, r in enumerate(layer_rafts)]
            raft_matches = physics.environment(asset_primitives, raft_prims, grid)
            for a_idx, r_idx in raft_matches:
                if a_idx not in on_surface_indices:
                    on_surface_indices.add(a_idx)
                    asset = l_assets[a_idx]
                    raft = layer_rafts[r_idx]
                    asset.state.velocity.vx += raft.state.velocity.vx
                    asset.state.velocity.vy += raft.state.velocity.vy
                    asset.state.mutators.triggers.submerged = False

        # Filter out assets on surfaces for shoreline and fluid passes
        immersible_indices = [i for i in range(len(l_assets)) if i not in on_surface_indices]
        if not immersible_indices:
            continue

        sub_to_orig = {sub_i: orig_i for sub_i, orig_i in enumerate(immersible_indices)}
        immersible_primitives = [
            l_assets[orig_i].primitive(sub_i) 
            for sub_i, orig_i in enumerate(immersible_indices)
        ]
        # -------------------------------------------------------------
        # 2. VIRTUAL EDGE CROSSING (SHORELINES)
        # -------------------------------------------------------------
        in_shoreline_indices: set[int] = set()
        shorelines = board.instances(AssetInstances.SHORELINES.value, layer)
        if shorelines:
            shore_prims, shore_lookup = _extract_compound_sensor_primitives(shorelines)
            if shore_prims:
                shore_matches = physics.environment(immersible_primitives, shore_prims, grid)
                for sub_idx, s_prim_idx in shore_matches:
                    orig_idx = sub_to_orig[sub_idx]
                    in_shoreline_indices.add(orig_idx)
                    asset = l_assets[orig_idx]
                    shore = shore_lookup[s_prim_idx]

                    nx, ny = _shoreline_normal(shore.state.orientation)
                    vx = asset.state.velocity.vx
                    vy = asset.state.velocity.vy
                    v_dot = vx * nx + vy * ny

                    if v_dot > 0 and not asset.state.mutators.triggers.submerged:
                        t = shore.properties.thickness
                        step_x = int(nx * (t + (asset.dimensions.w // 2))) if nx != 0.0 else 0
                        step_y = int(ny * (t + (asset.dimensions.l // 2))) if ny != 0.0 else 0
                        asset.state.position.x += step_x
                        asset.state.position.y += step_y
                        asset.state.mutators.triggers.submerged = True

                        splash_pos = Position(
                            int(asset.state.position.x),
                            int(asset.state.position.y + (asset.dimensions.l // 2))
                        )
                        splash = board.cradle.spawn_passive(
                            EffectsPalette.SPLASH.value, 
                            layer, 
                            splash_pos
                        )
                        board.add([splash])

        # -------------------------------------------------------------
        # 3. DIRECT ENVIRONMENTAL FLUID IMMERSION
        # -------------------------------------------------------------
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        in_fluid_indices: set[int] = set()
        fluid_flows: Dict[int, Tuple[float, float]] = {orig_idx: (0.0, 0.0) for orig_idx in immersible_indices}

        if fluids:
            fluid_prims, fluid_lookup = _extract_compound_sensor_primitives(fluids)
            if fluid_prims:
                fluid_matches = physics.environment(immersible_primitives, fluid_prims, grid)
                for sub_idx, f_prim_idx in fluid_matches:
                    orig_idx = sub_to_orig[sub_idx]
                    in_fluid_indices.add(orig_idx)
                    fluid = fluid_lookup[f_prim_idx]
                    fvx, fvy = _fluid_velocity(fluid)
                    cvx, cvy = fluid_flows[orig_idx]
                    fluid_flows[orig_idx] = (cvx + fvx, cvy + fvy)

        for orig_idx in immersible_indices:
            asset = l_assets[orig_idx]
            if orig_idx in in_fluid_indices:
                flow_vx, flow_vy = fluid_flows[orig_idx]
                if asset.instance == AssetInstances.CRATES.value:
                    asset.state.velocity.vx = flow_vx
                    asset.state.velocity.vy = flow_vy
                else:
                    asset.state.velocity.vx += flow_vx
                    asset.state.velocity.vy += flow_vy

                was_submerged = asset.state.mutators.triggers.submerged
                asset.state.mutators.triggers.submerged = True

                if not was_submerged:
                    splash_pos = Position(
                        int(asset.state.position.x),
                        int(asset.state.position.y + (asset.dimensions.l // 2))
                    )
                    splash = board.cradle.spawn_passive(
                        EffectsPalette.SPLASH.value, 
                        layer, 
                        splash_pos
                    )
                    board.add([splash])
            else:
                if orig_idx not in in_shoreline_indices:
                    asset.state.mutators.triggers.submerged = False