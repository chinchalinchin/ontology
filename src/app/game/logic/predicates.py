"""
@domain.logic
@app.module
@app.semantics

# Ontology: Source - app.game.logic.modules.predicates

Stateless Predicates for making assertions of Assets.
"""
# Application Libraries
from app.assets.base import Asset
from app.assets.hitboxes.core import NoHitbox
from app.assets.hitboxes.crafts import MaterialHitbox
from app.assets.hitboxes.objects import LayeredHitbox
from app.game.logic.relations.materials import MaterialIndex
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
    LayerProjections
)

# Cython Libraries
from libs.core.models import Position


def is_weight(asset: Asset) -> bool:
    """
    Evaluates physical candidate qualification for weight caching, excluding
    sensors, non-physical categories, NoHitbox assets, passable MaterialHitbox
    crafts, and non-blocking Door out-projections.
    """
    if asset.category in (
        AssetCategories.CURSORS,
        AssetCategories.EFFECTS,
        AssetCategories.GEOGRAPHY,
        AssetCategories.TILES,
        AssetCategories.WIDGETS
    ):
        return False

    if asset.properties.mass < 0:
        return False

    if isinstance(asset.hitbox, NoHitbox):
        return False

    if (
        isinstance(asset.hitbox, MaterialHitbox)
        and not MaterialIndex().is_obstacle(asset.state.blueprint)
    ):
        return False

    if (
        isinstance(asset.hitbox, LayeredHitbox)
        and asset.state.projection == LayerProjections.OUT
    ):
        return False

    return True


def is_obstacle(asset: Asset) -> bool:
    """
    Evaluates whether an entity instance qualifies as a physical navigational obstacle.
    """
    return asset.instance in (
        AssetInstances.CHESTS,
        AssetInstances.SIGNS,
        AssetInstances.CRATES,
        AssetInstances.GATES,
        AssetInstances.STRUTS,
        AssetInstances.OBSTACLES,
        AssetInstances.TREES,
    )


def _in_corridor(
    px: int,
    py: int,
    ox: int,
    oy: int,
    w: int,
    l: int,
    length: int,
    direction: str
) -> bool:
    """
    Evaluates whether integer coordinate (px, py) intersects a single directional
    fluid corridor using half-open AABB bounds without heap allocation.
    """
    if length <= 0:
        return False

    if direction == Directions.DOWN:
        return ox <= px < ox + w and oy <= py < oy + length
    if direction == Directions.UP:
        return ox <= px < ox + w and oy - length <= py < oy
    if direction == Directions.RIGHT:
        return ox <= px < ox + length and oy <= py < oy + l
    if direction == Directions.LEFT:
        return ox - length <= px < ox and oy <= py < oy + l

    return False


def in_pool(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects the annular pool of a fluid entity.
    """
    pool = fluid.state.pool
    if not pool or pool.w <= 0 or pool.l <= 0:
        return False

    px = int(position.x)
    py = int(position.y)
    return (
        pool.x <= px < pool.x + pool.w
        and pool.y <= py < pool.y + pool.l
    )


def in_stream(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects the parent corridor or
    any active child branch corridor of the specified fluid entity.
    """
    px = int(position.x)
    py = int(position.y)
    fw = fluid.properties.dimensions.w
    fl = fluid.properties.dimensions.l

    if _in_corridor(
        px,
        py,
        int(fluid.state.position.x),
        int(fluid.state.position.y),
        fw,
        fl,
        fluid.state.length,
        fluid.state.source
    ):
        return True

    branches = fluid.state.branches
    if not branches:
        return False

    for branch in branches:
        if _in_corridor(
            px,
            py,
            int(branch.position.x),
            int(branch.position.y),
            fw,
            fl,
            branch.length,
            branch.source
        ):
            return True

    return False


def in_fluid(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects either the annular pool
    or directional stream corridors of a fluid entity.
    """
    hitboxes = fluid.state.hitboxes
    if hitboxes:
        px = int(position.x)
        py = int(position.y)
        fx = int(fluid.state.position.x)
        fy = int(fluid.state.position.y)
        for hb in hitboxes:
            hx = fx + hb.position.x
            hy = fy + hb.position.y
            if (
                hx <= px < hx + hb.dimensions.w
                and hy <= py < hy + hb.dimensions.l
            ):
                return True
        return False

    if in_pool(position, fluid):
        return True
    return in_stream(position, fluid)