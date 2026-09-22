"""
# Ontology: app.game.logic.modules.motion.fields

Module for evaluating environmental vector fields (fluids, currents) and applying
superposition and surface interception onto active mutable assets.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import List, Tuple, Any, TYPE_CHECKING

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


def _direction_vector(source: Any) -> Tuple[float, float]:
    """
    Extracts normalized 2D direction components from a source property.
    """
    direction = source.value if hasattr(source, "value") else str(source)
    return DIRECTION_VECTORS.get(direction, (0.0, 0.0))


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
    3. Implements Direct Immersion: entities in Fluids acquire current velocity
       vectorally and trigger submersion/splash transitions.
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
        layer_rafts = board.instances(AssetInstances.RAFTS.value, layer)

        # -------------------------------------------------------------
        # 1. SURFACE HIERARCHY INTERCEPTION (RAFTS)
        # -------------------------------------------------------------
        on_raft = False
        raft_vx = 0.0
        raft_vy = 0.0

        for raft in layer_rafts:
            if _intersects(asset, raft):
                on_raft = True
                raft_vx = raft.state.velocity.vx
                raft_vy = raft.state.velocity.vy
                break

        if on_raft:
            asset.state.velocity.vx += raft_vx
            asset.state.velocity.vy += raft_vy
            if asset.instance in (
                AssetInstances.PLAYERS.value,
                AssetInstances.SPRITES.value
            ):
                asset.state.mutators.triggers.submerged = False
            continue

        # -------------------------------------------------------------
        # 2. DIRECT ENVIRONMENTAL FLUID IMMERSION
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
            asset.state.velocity.vx += flow_vx
            asset.state.velocity.vy += flow_vy

            if asset.instance in (
                AssetInstances.PLAYERS.value,
                AssetInstances.SPRITES.value
            ):
                was_submerged = asset.state.mutators.triggers.submerged
                asset.state.mutators.triggers.submerged = True

                if not was_submerged and board.cradle:
                    splash_pos = Position(
                        int(asset.state.position.x),
                        int(asset.state.position.y + (asset.dimensions.l // 2))
                    )
                    splash = board.cradle.spawn_passive(EffectsPalette.SPLASH.value, layer, splash_pos)
                    board.add([splash])
        else:
            if asset.instance in (
                AssetInstances.PLAYERS.value,
                AssetInstances.SPRITES.value
            ):
                asset.state.mutators.triggers.submerged = False