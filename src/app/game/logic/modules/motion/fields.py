"""
# Ontology: app.game.logic.modules.motion.fields

Module for evaluating environmental vector fields (fluids, currents) and applying
superposition and surface interception onto active mutable assets.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    List, 
    Tuple, 
    Any, 
    TYPE_CHECKING
)

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetInstances,
    Directions,
    EffectsPalette
)

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.geometry as geometry
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
    Directions.DOWN.value: (0.0, -1.0),   # Land South -> Inward water normal points North (-Y)
    Directions.LEFT.value: (1.0, 0.0),    # Land West  -> Inward water normal points East (+X)
    Directions.RIGHT.value: (-1.0, 0.0),  # Land East  -> Inward water normal points West (-X)
}


def _direction_vector(source: Any) -> Tuple[float, float]:
    """
    Extracts normalized 2D direction components from a source property.
    """
    direction = source.value if hasattr(source, "value") else str(source)
    return DIRECTION_VECTORS.get(direction, (0.0, 0.0))


def _shoreline_normal(orientation: Any) -> Tuple[float, float]:
    """
    Extracts normalized 2D inward water normal vector from shoreline orientation.
    """
    direction = orientation.value if hasattr(orientation, "value") else str(orientation)
    return SHORELINE_NORMALS.get(direction, (0.0, 0.0))


def _fluid_velocity(fluid: Asset) -> Tuple[float, float]:
    """
    Calculates environmental current velocity from fluid emitter source and flow intensity.
    """
    ux, uy = _direction_vector(fluid.state.source)
    speed = fluid.state.flow * settings.BASE_FLOW_SPEED
    return ux * speed, uy * speed


def _intersects(asset1: Asset, asset2: Asset) -> bool:
    """
    Evaluates Axis-Aligned Bounding Box (AABB) intersection between two assets.
    """
    return geometry.intersects(
        asset1.state.position,
        asset1.dimensions,
        asset1.hitboxes,
        asset2.state.position,
        asset2.dimensions,
        asset2.hitboxes
    ) is not None


def _update_rafts(rafts: List[Asset], board: Board) -> None:
    """
    Passively accelerates dynamic Rafts along intersecting fluid current vectors.
    """
    for raft in rafts:
        layer = raft.state.layer
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        flow_vx = 0.0
        flow_vy = 0.0
        in_fluid = False

        for fluid in fluids:
            if _intersects(raft, fluid):
                fvx, fvy = _fluid_velocity(fluid)
                flow_vx += fvx
                flow_vy += fvy
                in_fluid = True

        if in_fluid:
            raft.state.velocity.vx = flow_vx
            raft.state.velocity.vy = flow_vy
        else:
            raft.state.velocity.vx = 0.0
            raft.state.velocity.vy = 0.0


def update(assets: List[Asset], board: Board, delta: float) -> None:
    """
    Executes environmental field resolution pass across active mutable entities:
    1. Resolves passive hydrodynamic currents for Rafts.
    2. Implements Surface Interception: entities on Rafts adopt Raft reference frames
       and suppress submersion.
    3. Implements Virtual Edge Traversals: shoreline crossings trigger spatial drop
       displacement, toggle submersion, emit splash particles, and enforce one-way ledges.
    4. Implements Direct Immersion: entities in Fluids acquire current velocity vectorally
       and enter the submerged state.
    """
    rafts = [a for a in assets if a.instance == AssetInstances.RAFTS.value]
    _update_rafts(rafts, board)

    for asset in assets:
        if asset.instance in (
            AssetInstances.RAFTS.value,
            AssetInstances.PROJECTILES.value
        ):
            continue

        layer = asset.state.layer

        # -------------------------------------------------------------
        # 1. SURFACE HIERARCHY INTERCEPTION (BRIDGES & RAFTS)
        # -------------------------------------------------------------
        on_surface = False
        surface_vx = 0.0
        surface_vy = 0.0

        # 1a. Evaluate Static Bridges (sensor mass m = -1, zero drift)
        layer_bridges = board.instances(AssetInstances.BRIDGES.value, layer)
        for bridge in layer_bridges:
            if _intersects(asset, bridge):
                on_surface = True
                surface_vx = 0.0
                surface_vy = 0.0
                break

        # 1b. Evaluate Dynamic Rafts (m > 0, drifts with current)
        if not on_surface:
            for raft in board.instances(AssetInstances.RAFTS.value, layer):
                if _intersects(asset, raft):
                    on_surface = True
                    surface_vx = raft.state.velocity.vx
                    surface_vy = raft.state.velocity.vy
                    break

        if on_surface:
            asset.state.velocity.vx += surface_vx
            asset.state.velocity.vy += surface_vy
            asset.state.mutators.triggers.submerged = False
            continue

        # -------------------------------------------------------------
        # 2. VIRTUAL EDGE CROSSING (SHORELINES)
        # -------------------------------------------------------------
        shorelines = board.instances(AssetInstances.SHORELINES.value, layer)
        in_shoreline = False

        for shore in shorelines:
            if _intersects(asset, shore):
                in_shoreline = True
                nx, ny = _shoreline_normal(shore.state.orientation)
                vx = asset.state.velocity.vx
                vy = asset.state.velocity.vy
                v_dot = vx * nx + vy * ny

                # Entry transition: velocity points into water
                if v_dot > 0:
                    if not asset.state.mutators.triggers.submerged:
                        t = shore.state.thickness
                        disp_x = int(nx * (t + (asset.dimensions.w // 2))) if nx != 0.0 else 0
                        disp_y = int(ny * (t + (asset.dimensions.l // 2))) if ny != 0.0 else 0

                        asset.state.position.x += disp_x
                        asset.state.position.y += disp_y
                        asset.state.mutators.triggers.submerged = True

                        if board.cradle:
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

                        logger.info(
                            f"Telemetry:Fields:ShorelineCrossing "
                            f"entity={asset.name} "
                            f"shore={shore.name} "
                            f"orient={shore.state.orientation}",
                            f"normal=({nx}, {ny}) "
                            f"pre_pos=({asset.state.position.x}, {asset.state.position.y}) "
                            f"dim=({asset.dimensions.w}, {asset.dimensions.l}) "
                            f"displacement=({disp_x}, {disp_y}) "
                            f"post_pos=({asset.state.position.x + disp_x}, {asset.state.position.y + disp_y})"
                        )
                        

                # Exit / Ledge constraint: velocity points toward bank
                elif v_dot < 0:
                    if not shore.state.bidirectional:
                        if nx != 0.0:
                            asset.state.velocity.vx = 0.0
                        if ny != 0.0:
                            asset.state.velocity.vy = 0.0

        # -------------------------------------------------------------
        # 3. DIRECT ENVIRONMENTAL FLUID IMMERSION
        # -------------------------------------------------------------
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        in_fluid = False
        flow_vx = 0.0
        flow_vy = 0.0

        for fluid in fluids:
            if _intersects(asset, fluid):
                fvx, fvy = _fluid_velocity(fluid)
                flow_vx += fvx
                flow_vy += fvy
                in_fluid = True

        if in_fluid:
            logger.debug(
                f"Telemetry:Fields:FluidImmersion entity={asset.name} "
                f"pos=({asset.state.position.x}, {asset.state.position.y}) "
                f"applied_flow=({flow_vx}, {flow_vy}) "
                f"final_vel=({asset.state.velocity.vx}, {asset.state.velocity.vy})"
            )
            if asset.instance == AssetInstances.CRATES.value:
                asset.state.velocity.vx = flow_vx
                asset.state.velocity.vy = flow_vy
            else:
                asset.state.velocity.vx += flow_vx
                asset.state.velocity.vy += flow_vy

            was_submerged = asset.state.mutators.triggers.submerged
            asset.state.mutators.triggers.submerged = True

            if not was_submerged and board.cradle:
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
            if not in_shoreline:
                asset.state.mutators.triggers.submerged = False