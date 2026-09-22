"""
# Ontology: app.services.generators.game.actuator

Package for constructing Fluid Effect flows.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import List, Optional, Tuple, TYPE_CHECKING

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from app.models.state.objects import Pool
from libs.core.math import geometry
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)

if TYPE_CHECKING: 
    from app.game.board import Board

logger = logging.getLogger(__name__)


class Actuator:
    """
    Stateless geometric service calculating raycast stream truncation,
    annular pooling bounds, and compound sensor hitboxes.
    """

    def _collect_obstacles(self, fluid: Asset, board: Board, direction: str) -> List[Tuple]:
        layer = fluid.state.layer
        fx = fluid.state.position.x
        fy = fluid.state.position.y
        obstacle_tuples: List[Tuple] = []

        # 1. Map boundaries from procedural perimeter sweep
        perimeters = board.perimeters.get(layer, [])
        for b in perimeters:
            # Exclude boundaries positioned at or behind the emitter origin
            if direction == Directions.DOWN.value and b.position.y <= fy:
                continue
            elif direction == Directions.UP.value and (b.position.y + b.dimensions.l) >= fy:
                continue
            elif direction == Directions.RIGHT.value and b.position.x <= fx:
                continue
            elif direction == Directions.LEFT.value and (b.position.x + b.dimensions.w) >= fx:
                continue

            obstacle_tuples.append((
                b.position.x,
                b.position.y,
                b.dimensions.w,
                b.dimensions.l,
                None
            ))

        # 2. Environmental physical assets (crates, struts, closed gates, signs)
        candidates = set(board.weights(layer))
        candidates.update(board.obstacles(layer))

        for asset in candidates:
            if asset is fluid:
                continue

            if asset.category in (
                AssetCategories.SHEETS.value, 
                AssetCategories.EFFECTS.value
            ):
                continue

            # Rafts do not participate in fluid obstruction
            if asset.instance == AssetInstances.RAFTS.value:
                continue

            if asset.instance == AssetInstances.GATES.value and asset.state.switch:
                continue

            for hb in asset.hitboxes:
                ox = asset.state.position.x + hb.position.x
                oy = asset.state.position.y + hb.position.y
                ow = hb.dimensions.w
                ol = hb.dimensions.l

                # Exclude bodies positioned at or behind the emitter origin
                if direction == Directions.UP.value and oy >= fy:
                    continue
                elif direction == Directions.DOWN.value and (oy + ol) <= fy:
                    continue
                elif direction == Directions.LEFT.value and ox >= fx:
                    continue
                elif direction == Directions.RIGHT.value and (ox + ow) <= fx:
                    continue

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
        Floods the complete outer bounding box to prevent transparent pixel edge bleed.
        """
        ox = obstacle.state.position.x
        oy = obstacle.state.position.y
        ow = obstacle.dimensions.w
        ol = obstacle.dimensions.l

        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l

        fx = fluid.state.position.x
        fy = fluid.state.position.y

        pool_x = ox - flow * fw
        pool_y = oy - flow * fl
        pool_w = ow + 2 * flow * fw
        pool_l = ol + 2 * flow * fl

        pool_bounds = Pool(x=pool_x, y=pool_y, w=pool_w, l=pool_l)

        # Single solid hitbox covering the entire rectangular pool area
        pool_hitboxes = [
            Hitbox(Position(pool_x - fx, pool_y - fy), Dimensions(pool_w, pool_l))
        ]

        return pool_bounds, pool_hitboxes

    def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
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
        # Do not mutate fluid.properties.hitboxes (properties are static/shared across instances)

        logger.info(
            f"Fluid(name={fluid.name}, direction={direction}): "
            f" Length: {stream_length}px,  "
            f"Struck: {getattr(struck_obstacle, 'name', 'bounds')}, "
            f"Pool: {pool_bounds is not None}"
        )

        return stream_length, pool_bounds, hitboxes
    