"""
# Ontology: app.game.board.predicates

Stateless domain and geometric predicate functions for game assets and coordinates.
"""
# Standard Libraries
from typing import (
    List, 
    Tuple
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position


def is_weight(asset: Asset) -> bool:
    """
    Evaluates physical candidate qualification for weight caching, excluding
    sensors, cursors, effects, geography, and terrain tiles.
    """
    try:
        mass = asset.properties.mass
        return (
            mass >= 0
            and asset.category not in (
                AssetCategories.CURSORS.value,
                AssetCategories.EFFECTS.value,
                AssetCategories.GEOGRAPHY.value,
                AssetCategories.TILES.value
            )
        )
    except AttributeError:
        return False


def is_obstacle(asset: Asset) -> bool:
    """
    Evaluates whether an entity instance qualifies as a physical navigational obstacle.
    """
    return asset.instance in (
        AssetInstances.CHESTS.value,
        AssetInstances.SIGNS.value,
        AssetInstances.CRATES.value,
        AssetInstances.GATES.value,
        AssetInstances.STRUTS.value,
        AssetInstances.OBSTACLES.value,
        AssetInstances.TREES.values,
    )


def in_pool(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects the annular pool of a fluid entity.
    """
    pool = getattr(fluid.state, "pool", None)
    if not pool or pool.w <= 0 or pool.l <= 0:
        return False

    px = int(position.x)
    py = int(position.y)
    return geometry.inside(
        px,
        py,
        [(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)]
    )


def in_stream(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects the parent corridor or
    any active child branch corridor of the specified fluid entity.
    """
    px = int(position.x)
    py = int(position.y)
    fx = int(fluid.state.position.x)
    fy = int(fluid.state.position.y)
    fw = fluid.properties.dimensions.w
    fl = fluid.properties.dimensions.l
    slen = fluid.state.length

    direction = fluid.state.source
    direction_val = direction.value if hasattr(direction, "value") else str(direction)

    aabbs: List[Tuple[int, int, int, int]] = []

    if slen > 0:
        if direction_val == Directions.DOWN.value:
            aabbs.append((fx, fy, fx + fw, fy + slen))
        elif direction_val == Directions.UP.value:
            aabbs.append((fx, fy - slen, fx + fw, fy))
        elif direction_val == Directions.RIGHT.value:
            aabbs.append((fx, fy, fx + slen, fy + fl))
        elif direction_val == Directions.LEFT.value:
            aabbs.append((fx - slen, fy, fx, fy + fl))

    if fluid.state.branches:
        for branch in fluid.state.branches:
            if branch.length <= 0:
                continue
            bx = int(branch.position.x)
            by = int(branch.position.y)
            b_dir = branch.source
            
            b_dir_val = b_dir.value if hasattr(b_dir, "value") else str(b_dir)

            if b_dir_val == Directions.DOWN.value:
                aabbs.append((bx, by, bx + fw, by + branch.length))
            elif b_dir_val == Directions.UP.value:
                aabbs.append((bx, by - branch.length, bx + fw, by))
            elif b_dir_val == Directions.RIGHT.value:
                aabbs.append((bx, by, bx + branch.length, by + fl))
            elif b_dir_val == Directions.LEFT.value:
                aabbs.append((bx - branch.length, by, bx, by + fl))

    if not aabbs:
        return False

    return geometry.inside(px, py, aabbs)


def in_fluid(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects either the annular pool
    or directional stream corridors of a fluid entity.
    """
    if in_pool(position, fluid):
        return True
    if fluid.state.length > 0 and in_stream(position, fluid):
        return True
    return False