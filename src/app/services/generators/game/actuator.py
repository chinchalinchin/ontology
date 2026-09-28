"""
# Ontology: app.services.generators.game.actuator

Package for constructing Fluid Effect flows and radial pools.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    List, 
    Optional, 
    Tuple, 
    TYPE_CHECKING
)

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from app.models.state import Pool

if TYPE_CHECKING: 
    from app.game.board import Board

# Cython Libraries
from libs.core.math import geometry
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)

logger = logging.getLogger(__name__)


class Actuator:
    """
    Service calculating raycast stream truncation and annular pooling bounds.
    """

    def _collect_obstacles(self, 
        fluid: Asset, 
        board: Board, 
        direction: str
    ) -> List[Tuple]:
        layer = fluid.state.layer
        fx = fluid.state.position.x
        fy = fluid.state.position.y
        obstacle_tuples: List[Tuple] = []

        # 1. Map boundaries from procedural perimeter sweep
        perimeters = board.perimeters.get(layer, [])
        for b in perimeters:
            if direction == Directions.DOWN.value and (
                b.position.y <= fy
            ): continue
            elif direction == Directions.UP.value and (
                (b.position.y + b.dimensions.l) >= fy
            ): continue
            elif direction == Directions.RIGHT.value and (
                b.position.x <= fx
            ): continue
            elif direction == Directions.LEFT.value and (
                (b.position.x + b.dimensions.w) >= fx
            ): continue

            obstacle_tuples.append((
                b.position.x,
                b.position.y,
                b.dimensions.w,
                b.dimensions.l,
                None
            ))

        # 2. Environmental physical assets strictly restricted to immovable static bodies (mass == 0)
        candidates = set(board.weights(layer))
        candidates.update(board.obstacles(layer))

        for asset in candidates:
            if asset is fluid: continue

            if asset.category in (
                AssetCategories.SHEETS.value, 
                AssetCategories.EFFECTS.value
            ): continue

            if asset.instance == AssetInstances.RAFTS.value: continue

            if asset.instance == AssetInstances.GATES.value and (
                asset.state.switch
            ): continue

            # Exclude dynamic bodies (mass > 0) from fluid occlusion (Fix B011)
            if hasattr(asset.properties, "mass") and asset.properties.mass != 0:
                continue

            for hb in asset.hitboxes:
                ox = asset.state.position.x + hb.position.x
                oy = asset.state.position.y + hb.position.y
                ow = hb.dimensions.w
                ol = hb.dimensions.l

                if direction == Directions.UP.value and (
                    oy >= fy
                ): continue
                elif direction == Directions.DOWN.value and (
                    (oy + ol) <= fy
                ): continue
                elif direction == Directions.LEFT.value and (
                    ox >= fx
                ): continue
                elif direction == Directions.RIGHT.value and (
                    (ox + ow) <= fx
                ): continue

                obstacle_tuples.append((ox, oy, ow, ol, asset))

        logger.debug(
            settings.SEPARATOR.join([
                "Actuator",
                fluid.name,
                "Candidate Obstacles"
            ]) + f": {len(obstacle_tuples)}"
        )
        return obstacle_tuples

    def _calculate_max_distance(self, fluid: Asset, board: Board, direction: str) -> int:
        layer = fluid.state.layer
        sizes = board.size(layer)
        layer_size = sizes[0] if sizes else None

        fx = fluid.state.position.x
        fy = fluid.state.position.y

        if not layer_size or layer_size.w == 0 or layer_size.l == 0:
            return 10000

        if direction == Directions.DOWN.value:
            return max(0, layer_size.l - fy)
        elif direction == Directions.UP.value:
            return max(0, fy)
        elif direction == Directions.RIGHT.value:
            return max(0, layer_size.w - fx)
        elif direction == Directions.LEFT.value:
            return max(0, fx)

        return 10000

    def _build_stream_hitbox(self, direction: str, length: int, fw: int, fl: int) -> Optional[Hitbox]:
        if length <= 0:
            return None

        if direction == Directions.DOWN.value:
            return Hitbox(Position(0, 0), Dimensions(fw, length))
        elif direction == Directions.UP.value:
            return Hitbox(Position(0, -length), Dimensions(fw, length))
        elif direction == Directions.RIGHT.value:
            return Hitbox(Position(0, 0), Dimensions(length, fl))
        elif direction == Directions.LEFT.value:
            return Hitbox(Position(-length, 0), Dimensions(length, fl))

        return None

    def _partition_pool(
        self,
        obstacle: Asset,
        fluid: Asset,
        flow: int
    ) -> Tuple[Pool, List[Hitbox]]:
        """
        Calculates a solid annular flood zone around an obstacle struck by fluid.
        Snaps pool boundaries to 32px tile grid multiples.
        """
        ox = obstacle.state.position.x
        oy = obstacle.state.position.y
        ow = obstacle.dimensions.w
        ol = obstacle.dimensions.l

        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l

        fx = fluid.state.position.x
        fy = fluid.state.position.y

        raw_min_x = ox - flow * fw
        raw_min_y = oy - flow * fl
        raw_max_x = ox + ow + flow * fw
        raw_max_y = oy + ol + flow * fl

        pool_x = int((raw_min_x // fw) * fw)
        pool_y = int((raw_min_y // fl) * fl)
        pool_end_x = int(((raw_max_x + fw - 1) // fw) * fw)
        pool_end_y = int(((raw_max_y + fl - 1) // fl) * fl)

        pool_w = pool_end_x - pool_x
        pool_l = pool_end_y - pool_y

        pool_bounds = Pool(x=pool_x, y=pool_y, w=pool_w, l=pool_l)
        pool_hitboxes = [
            Hitbox(Position(pool_x - fx, pool_y - fy), Dimensions(pool_w, pool_l))
        ]

        return pool_bounds, pool_hitboxes

    def propagate(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        """
        Pass 1: Truncates fluid stream against map bounds and static obstacles (mass == 0),
        expands annular pooling, updates compound hitboxes, and resets dirty flag.
        """
        source_prop = fluid.state.source
        direction = source_prop.value if hasattr(source_prop, "value") else str(source_prop)        
        flow = fluid.state.flow
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        fx = fluid.state.position.x
        fy = fluid.state.position.y

        fluid.frame.tile_w = fw
        fluid.frame.tile_l = fl

        obstacle_tuples = self._collect_obstacles(fluid, board, direction)
        max_dist = self._calculate_max_distance(fluid, board, direction)

        stream_length, struck_obstacle = geometry.raycast(
            fx,
            fy,
            fw,
            fl,
            direction,
            obstacle_tuples,
            max_dist
        )

        hitboxes: List[Hitbox] = []
        stream_hb = self._build_stream_hitbox(direction, stream_length, fw, fl)
        if stream_hb:
            hitboxes.append(stream_hb)

        pool_bounds: Optional[Pool] = None
        if isinstance(struck_obstacle, Asset) and flow > 0:
            pool_bounds, pool_hitboxes = self._partition_pool(struck_obstacle, fluid, flow)
            hitboxes.extend(pool_hitboxes)

        fluid.state.length = stream_length
        fluid.state.pool = pool_bounds
        fluid.state.hitboxes = hitboxes
        fluid.state.dirty = False

        return stream_length, pool_bounds, hitboxes

    def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        """
        Unified execution interface for isolated fluid propagation.
        """
        return self.propagate(fluid, board)