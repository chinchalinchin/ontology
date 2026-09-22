"""
# Ontology: app.services.generators.game.actuator

Package for constructing Fluid Effect flows and procedural shoreline margins.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING

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
    from app.game.logic.relations.shorelines import ShorelineIndex

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
    Stateless geometric service calculating raycast stream truncation,
    annular pooling bounds, compound sensor hitboxes, and procedural shoreline perimeters.
    """
    shorelines: Optional[ShorelineIndex]

    def __init__(self, shorelines: Optional[ShorelineIndex] = None):
        self.shorelines = shorelines

    def _collect_obstacles(self, fluid: Asset, board: Board, direction: str) -> List[Tuple]:
        layer = fluid.state.layer
        fx = fluid.state.position.x
        fy = fluid.state.position.y
        obstacle_tuples: List[Tuple] = []

        # 1. Map boundaries from procedural perimeter sweep
        perimeters = board.perimeters.get(layer, [])
        for b in perimeters:
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

            if asset.instance == AssetInstances.RAFTS.value:
                continue

            if asset.instance == AssetInstances.GATES.value and asset.state.switch:
                continue

            for hb in asset.hitboxes:
                ox = asset.state.position.x + hb.position.x
                oy = asset.state.position.y + hb.position.y
                ow = hb.dimensions.w
                ol = hb.dimensions.l

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
        pool_hitboxes = [
            Hitbox(Position(pool_x - fx, pool_y - fy), Dimensions(pool_w, pool_l))
        ]

        return pool_bounds, pool_hitboxes

    # -------------------------------------------------------------
    # PROCEDURAL SHORELINE GENERATION & OCCLUSION LOGIC
    # -------------------------------------------------------------

    def _detect_flank_occlusions(
        self, 
        x: int, 
        y: int, 
        w: int, 
        l: int, 
        layer: str, 
        board: Board
    ) -> bool:
        """
        Validates whether a candidate flank cell is occluded by layer boundaries
        or physical static obstacles (mass >= 0).
        """
        sizes = board.size(layer)
        layer_size = sizes[0] if sizes else None
        if layer_size and layer_size.w > 0 and layer_size.l > 0:
            if x < 0 or y < 0 or (x + w) > layer_size.w or (y + l) > layer_size.l:
                return True

        # Check procedural perimeters
        perimeters = board.perimeters.get(layer, [])
        for b in perimeters:
            bx = b.position.x
            by = b.position.y
            bw = b.dimensions.w
            bl = b.dimensions.l
            if x < bx + bw and x + w > bx and y < by + bl and y + l > by:
                return True

        # Check non-fluid solid obstacles
        candidates = set(board.weights(layer))
        candidates.update(board.obstacles(layer))

        for asset in candidates:
            if asset.category in (
                AssetCategories.SHEETS.value,
                AssetCategories.EFFECTS.value
            ):
                continue

            if asset.instance == AssetInstances.RAFTS.value:
                continue

            if asset.instance == AssetInstances.GATES.value and asset.state.switch:
                continue

            for hb in asset.hitboxes:
                ox = asset.state.position.x + hb.position.x
                oy = asset.state.position.y + hb.position.y
                ow = hb.dimensions.w
                ol = hb.dimensions.l

                if x < ox + ow and x + w > ox and y < oy + ol and y + l > oy:
                    return True

        return False

    def _is_inside_fluid(
        self, 
        x: int, 
        y: int, 
        w: int, 
        l: int, 
        fluid: Asset, 
        stream_length: int, 
        pool: Optional[Pool]
    ) -> bool:
        """
        Determines whether a candidate land cell overlaps active fluid water.
        """
        if stream_length > 0:
            fx = fluid.state.position.x
            fy = fluid.state.position.y
            fw = fluid.properties.dimensions.w
            fl = fluid.properties.dimensions.l
            direction = fluid.state.source
            direction_str = direction.value if hasattr(direction, "value") else str(direction)

            if direction_str == Directions.DOWN.value:
                sx, sy, sw, sl = fx, fy, fw, stream_length
            elif direction_str == Directions.UP.value:
                sx, sy, sw, sl = fx, fy - stream_length, fw, stream_length
            elif direction_str == Directions.RIGHT.value:
                sx, sy, sw, sl = fx, fy, stream_length, fl
            elif direction_str == Directions.LEFT.value:
                sx, sy, sw, sl = fx - stream_length, fy, stream_length, fl
            else:
                sx, sy, sw, sl = fx, fy, fw, fl

            if x < sx + sw and x + w > sx and y < sy + sl and y + l > sy:
                return True

        if pool is not None:
            if x < pool.x + pool.w and x + w > pool.x and y < pool.y + pool.l and y + l > pool.y:
                return True

        return False

    def _extract_flank_descriptors(
        self, 
        fluid: Asset, 
        stream_length: int, 
        pool: Optional[Pool]
    ) -> List[Dict]:
        """
        Calculates linear corridor flanks and annular pool perimeters.
        """
        descriptors = []
        fx = fluid.state.position.x
        fy = fluid.state.position.y
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        direction = fluid.state.source
        direction_str = direction.value if hasattr(direction, "value") else str(direction)

        if stream_length > 0:
            if direction_str == Directions.DOWN.value:
                # West flank: Land West, Water East
                descriptors.append({
                    'orientation': Directions.LEFT.value,
                    'axis': 'y',
                    'start': fy,
                    'end': fy + stream_length,
                    'water_coord': fx,
                    'land_coord': fx - 32
                })
                # East flank: Land East, Water West
                descriptors.append({
                    'orientation': Directions.RIGHT.value,
                    'axis': 'y',
                    'start': fy,
                    'end': fy + stream_length,
                    'water_coord': fx + fw,
                    'land_coord': fx + fw
                })
                # Distal flank: Land South, Water North
                descriptors.append({
                    'orientation': Directions.DOWN.value,
                    'axis': 'x',
                    'start': fx,
                    'end': fx + fw,
                    'water_coord': fy + stream_length,
                    'land_coord': fy + stream_length
                })
            elif direction_str == Directions.UP.value:
                # West flank: Land West, Water East
                descriptors.append({
                    'orientation': Directions.LEFT.value,
                    'axis': 'y',
                    'start': fy - stream_length,
                    'end': fy,
                    'water_coord': fx,
                    'land_coord': fx - 32
                })
                # East flank: Land East, Water West
                descriptors.append({
                    'orientation': Directions.RIGHT.value,
                    'axis': 'y',
                    'start': fy - stream_length,
                    'end': fy,
                    'water_coord': fx + fw,
                    'land_coord': fx + fw
                })
                # Distal flank: Land North, Water South
                descriptors.append({
                    'orientation': Directions.UP.value,
                    'axis': 'x',
                    'start': fx,
                    'end': fx + fw,
                    'water_coord': fy - stream_length,
                    'land_coord': fy - stream_length - 32
                })
            elif direction_str == Directions.RIGHT.value:
                # North flank: Land North, Water South
                descriptors.append({
                    'orientation': Directions.UP.value,
                    'axis': 'x',
                    'start': fx,
                    'end': fx + stream_length,
                    'water_coord': fy,
                    'land_coord': fy - 32
                })
                # South flank: Land South, Water North
                descriptors.append({
                    'orientation': Directions.DOWN.value,
                    'axis': 'x',
                    'start': fx,
                    'end': fx + stream_length,
                    'water_coord': fy + fl,
                    'land_coord': fy + fl
                })
                # Distal flank: Land East, Water West
                descriptors.append({
                    'orientation': Directions.RIGHT.value,
                    'axis': 'y',
                    'start': fy,
                    'end': fy + fl,
                    'water_coord': fx + stream_length,
                    'land_coord': fx + stream_length
                })
            elif direction_str == Directions.LEFT.value:
                # North flank: Land North, Water South
                descriptors.append({
                    'orientation': Directions.UP.value,
                    'axis': 'x',
                    'start': fx - stream_length,
                    'end': fx,
                    'water_coord': fy,
                    'land_coord': fy - 32
                })
                # South flank: Land South, Water North
                descriptors.append({
                    'orientation': Directions.DOWN.value,
                    'axis': 'x',
                    'start': fx - stream_length,
                    'end': fx,
                    'water_coord': fy + fl,
                    'land_coord': fy + fl
                })
                # Distal flank: Land West, Water East
                descriptors.append({
                    'orientation': Directions.LEFT.value,
                    'axis': 'y',
                    'start': fy,
                    'end': fy + fl,
                    'water_coord': fx - stream_length,
                    'land_coord': fx - stream_length - 32
                })

        if pool is not None:
            # North outer flank: Land North, Water South
            descriptors.append({
                'orientation': Directions.UP.value,
                'axis': 'x',
                'start': pool.x,
                'end': pool.x + pool.w,
                'water_coord': pool.y,
                'land_coord': pool.y - 32
            })
            # South outer flank: Land South, Water North
            descriptors.append({
                'orientation': Directions.DOWN.value,
                'axis': 'x',
                'start': pool.x,
                'end': pool.x + pool.w,
                'water_coord': pool.y + pool.l,
                'land_coord': pool.y + pool.l
            })
            # West outer flank: Land West, Water East
            descriptors.append({
                'orientation': Directions.LEFT.value,
                'axis': 'y',
                'start': pool.y,
                'end': pool.y + pool.l,
                'water_coord': pool.x,
                'land_coord': pool.x - 32
            })
            # East outer flank: Land East, Water West
            descriptors.append({
                'orientation': Directions.RIGHT.value,
                'axis': 'y',
                'start': pool.y,
                'end': pool.y + pool.l,
                'water_coord': pool.x + pool.w,
                'land_coord': pool.x + pool.w
            })

        return descriptors

    def _build_shoreline_hitbox(self, orientation: str, length: int, thickness: int = 8) -> Hitbox:
        """
        Constructs a narrow sensor strip aligned along the land-water boundary.
        """
        if orientation == Directions.UP.value:
            return Hitbox(Position(0, 32 - thickness), Dimensions(length, thickness))
        elif orientation == Directions.DOWN.value:
            return Hitbox(Position(0, 0), Dimensions(length, thickness))
        elif orientation == Directions.LEFT.value:
            return Hitbox(Position(32 - thickness, 0), Dimensions(thickness, length))
        elif orientation == Directions.RIGHT.value:
            return Hitbox(Position(0, 0), Dimensions(thickness, length))
        return Hitbox(Position(0, 0), Dimensions(length, thickness))

    def _generate_shorelines(
        self, 
        fluid: Asset, 
        board: Board, 
        stream_length: int, 
        pool: Optional[Pool]
    ) -> List[Asset]:
        """
        Samples unoccluded flank cells, resolves secondary indices against bordering tiles,
        and coalesces contiguous segments into Shoreline assets.
        """
        if not self.shorelines or not board.cradle:
            return []

        layer = fluid.state.layer
        descriptors = self._extract_flank_descriptors(fluid, stream_length, pool)
        new_shorelines: List[Asset] = []

        for desc in descriptors:
            orientation = desc['orientation']
            axis = desc['axis']
            start = desc['start']
            end = desc['end']
            land_coord = desc['land_coord']

            curr_seg = None

            def commit_segment():
                nonlocal curr_seg
                if curr_seg:
                    hb = self._build_shoreline_hitbox(
                        curr_seg['orientation'], 
                        curr_seg['length'],
                        curr_seg['thickness']
                    )
                    shore_asset = board.cradle.spawn_shoreline(
                        id=curr_seg['id'],
                        layer=layer,
                        position=curr_seg['pos'],
                        orientation=curr_seg['orientation'],
                        length=curr_seg['length'],
                        parent_fluid=fluid.name,
                        hitboxes=[hb],
                        bidirectional=True
                    )
                    new_shorelines.append(shore_asset)
                    curr_seg = None

            c = start
            while c < end:
                step_len = min(32, end - c)
                if axis == 'x':
                    cell_x, cell_y = c, land_coord
                    cell_w, cell_l = step_len, 32
                else:
                    cell_x, cell_y = land_coord, c
                    cell_w, cell_l = 32, step_len

                # 1. Skip if overlaps fluid itself
                if self._is_inside_fluid(cell_x, cell_y, cell_w, cell_l, fluid, stream_length, pool):
                    commit_segment()
                    c += step_len
                    continue

                # 2. Skip if occluded by boundary or static obstacle
                if self._detect_flank_occlusions(cell_x, cell_y, cell_w, cell_l, layer, board):
                    commit_segment()
                    c += step_len
                    continue

                # 3. Query adjacent background tile
                tile = board.tile(layer, Position(cell_x, cell_y))
                if not tile:
                    commit_segment()
                    c += step_len
                    continue

                # 4. Resolve shoreline asset key from secondary index
                shoreline_id = self.shorelines.resolve(tile.id, fluid.id)
                if not shoreline_id:
                    commit_segment()
                    c += step_len
                    continue

                thickness = 8
                shore_props = board.cradle.spawnables.shorelines.get(shoreline_id)
                if shore_props and hasattr(shore_props, 'thickness'):
                    thickness = shore_props.thickness

                # 5. Coalesce contiguous runs
                if (
                    curr_seg is not None
                    and curr_seg['id'] == shoreline_id
                    and curr_seg['expected_next'] == c
                ):
                    curr_seg['length'] += step_len
                    curr_seg['expected_next'] += step_len
                else:
                    commit_segment()
                    curr_seg = {
                        'id': shoreline_id,
                        'pos': Position(cell_x, cell_y),
                        'length': step_len,
                        'orientation': orientation,
                        'thickness': thickness,
                        'expected_next': c + step_len
                    }

                c += step_len

            commit_segment()

        return new_shorelines

    def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        # 1. Purge previous child shorelines
        if fluid.state.shorelines:
            old_shorelines = [
                board.asset(name, fluid.state.layer) 
                for name in fluid.state.shorelines
            ]
            valid_removals = [s for s in old_shorelines if s is not None]
            if valid_removals:
                board.remove(valid_removals)
            fluid.state.shorelines.clear()

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

        # 2. Generate and link new child shorelines
        new_shorelines = self._generate_shorelines(fluid, board, stream_length, pool_bounds)
        if new_shorelines:
            board.add(new_shorelines)
            fluid.state.shorelines = [s.name for s in new_shorelines]

        logger.info(
            f"Fluid(name={fluid.name}, direction={direction}) | "
            f" Length: {stream_length}px,  "
            f"Struck: {getattr(struck_obstacle, 'name', 'bounds')}, "
            f"Pool: {pool_bounds is not None}, "
            f"Shorelines: {len(new_shorelines)}"
        )

        return stream_length, pool_bounds, hitboxes