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
from libs.core.math import geometry
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)

if TYPE_CHECKING: 
    from app.game.board import Board
    from app.game.logic.relations.shorelines import ShorelineIndex

logger = logging.getLogger(__name__)


class Actuator:
    """
    Stateless geometric service calculating raycast stream truncation,
    annular pooling bounds, compound sensor hitboxes, and procedural shoreline perimeters.
    """
    shorelines: Optional[ShorelineIndex]

    def __init__(self, shorelines: Optional[ShorelineIndex] = None):
        self.shorelines = shorelines

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

        # 2. Environmental physical assets (crates, struts, closed gates, signs)
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
        Snaps pool boundaries to 32px tile grid multiples to guarantee seamless alignment
        with background terrain tiles and eliminate fractional texture overflow.
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

        # Snap pool boundaries to tile grid multiples
        pool_x = int((raw_min_x // fw) * fw)
        pool_y = int((raw_min_y // fl) * fl)
        pool_end_x = int(((raw_max_x + fw - 1) // fw) * fw)
        pool_end_y = int(((raw_max_y + fl - 1) // fl) * fl)

        pool_w = pool_end_x - pool_x
        pool_l = pool_end_y - pool_y

        pool_bounds = Pool(x=pool_x, y=pool_y, w=pool_w, l=pool_l)

        # Single solid hitbox covering the entire rectangular pool area
        pool_hitboxes = [
            Hitbox(Position(pool_x - fx, pool_y - fy), Dimensions(pool_w, pool_l))
        ]

        return pool_bounds, pool_hitboxes

    # -------------------------------------------------------------
    # WATER FIELD DETECTION & PROCEDURAL SHORELINES
    # -------------------------------------------------------------

    def _is_water(self, px: int, py: int, layer: str, board: Board) -> bool:
        """
        Determines whether a coordinate (px, py) is inside ANY active fluid on the layer.
        """
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        for f in fluids:
            p = f.state.pool
            if p and p.x <= px < p.x + p.w and p.y <= py < p.y + p.l:
                return True

            slen = f.state.length
            if slen > 0:
                fx = f.state.position.x
                fy = f.state.position.y
                fw = f.properties.dimensions.w
                fl = f.properties.dimensions.l
                src = f.state.source
                src_str = src.value if hasattr(src, "value") else str(src)

                if src_str == Directions.DOWN.value and fx <= px < fx + fw and fy <= py < fy + slen:
                    return True
                elif src_str == Directions.UP.value and fx <= px < fx + fw and fy - slen <= py < fy:
                    return True
                elif src_str == Directions.RIGHT.value and fx <= px < fx + slen and fy <= py < fy + fl:
                    return True
                elif src_str == Directions.LEFT.value and fx - slen <= px < fx and fy <= py < fy + fl:
                    return True
        return False


    def _is_water_excluding(
        self, 
        px: int, 
        py: int, 
        layer: str, 
        board: Board, 
        exclude_name: Optional[str]
    ) -> bool:
        """
        Determines whether a coordinate (px, py) is inside ANY active fluid on the layer,
        excluding the fluid identified by exclude_name.
        """
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        for f in fluids:
            if f.name == exclude_name:
                continue

            p = f.state.pool
            if p and p.x <= px < p.x + p.w and p.y <= py < p.y + p.l:
                return True

            slen = f.state.length
            if slen > 0:
                fx = f.state.position.x
                fy = f.state.position.y
                fw = f.properties.dimensions.w
                fl = f.properties.dimensions.l
                src = f.state.source
                src_str = src.value if hasattr(src, "value") else str(src)

                if src_str == Directions.DOWN.value and (
                    fx <= px < fx + fw and fy <= py < fy + slen
                ):
                    return True
                elif src_str == Directions.UP.value and (
                    fx <= px < fx + fw and fy - slen <= py < fy
                ):
                    return True
                elif src_str == Directions.RIGHT.value and (
                    fx <= px < fx + slen and fy <= py < fy + fl
                ):
                    return True
                elif src_str == Directions.LEFT.value and (
                    fx - slen <= px < fx and fy <= py < fy + fl
                ):
                    return True
        return False


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
        Validates whether the substrate bordering the water is occluded by
        map boundaries or static obstacles (mass >= 0).
        """
        sizes = board.size(layer)
        layer_size = sizes[0] if sizes else None
        if layer_size and layer_size.w > 0 and layer_size.l > 0:
            if x < 0 or y < 0 or (x + w) > layer_size.w or (y + l) > layer_size.l:
                return True

        perimeters = board.perimeters.get(layer, [])
        for b in perimeters:
            bx = b.position.x
            by = b.position.y
            bw = b.dimensions.w
            bl = b.dimensions.l
            if x < bx + bw and x + w > bx and y < by + bl and y + l > by:
                return True

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


    def _extract_flank_descriptors(
        self, 
        fluid: Asset, 
        stream_length: int, 
        pool: Optional[Pool]
    ) -> List[Dict]:
        """
        Extracts unoccluded flank margins. Corridors stop at the pool boundary.
        Positions anchor along the water margin; substrate sampling probes the bordering land.
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
                corridor_end = pool.y if (pool is not None and pool.y > fy) else (fy + stream_length)
                if corridor_end > fy:
                    # West flank: Land West, Water East -> Margin at x = fx
                    descriptors.append({
                        'orientation': Directions.LEFT.value,
                        'axis': 'y',
                        'start': fy,
                        'end': corridor_end,
                        'margin_coord': fx,
                        'probe_coord': fx - 1
                    })
                    # East flank: Land East, Water West -> Margin at x = fx + fw - 32
                    descriptors.append({
                        'orientation': Directions.RIGHT.value,
                        'axis': 'y',
                        'start': fy,
                        'end': corridor_end,
                        'margin_coord': fx + fw - 32,
                        'probe_coord': fx + fw + 1
                    })
                if pool is None:
                    descriptors.append({
                        'orientation': Directions.DOWN.value,
                        'axis': 'x',
                        'start': fx,
                        'end': fx + fw,
                        'margin_coord': fy + stream_length - 32,
                        'probe_coord': fy + stream_length + 1
                    })

            elif direction_str == Directions.UP.value:
                corridor_start = (pool.y + pool.l) if (pool is not None and (pool.y + pool.l) < fy) else (fy - stream_length)
                if fy > corridor_start:
                    # West flank: Land West, Water East
                    descriptors.append({
                        'orientation': Directions.LEFT.value,
                        'axis': 'y',
                        'start': corridor_start,
                        'end': fy,
                        'margin_coord': fx,
                        'probe_coord': fx - 1
                    })
                    # East flank: Land East, Water West
                    descriptors.append({
                        'orientation': Directions.RIGHT.value,
                        'axis': 'y',
                        'start': corridor_start,
                        'end': fy,
                        'margin_coord': fx + fw - 32,
                        'probe_coord': fx + fw + 1
                    })
                if pool is None:
                    descriptors.append({
                        'orientation': Directions.UP.value,
                        'axis': 'x',
                        'start': fx,
                        'end': fx + fw,
                        'margin_coord': fy - stream_length,
                        'probe_coord': fy - stream_length - 1
                    })

            elif direction_str == Directions.RIGHT.value:
                corridor_end = pool.x if (pool is not None and pool.x > fx) else (fx + stream_length)
                if corridor_end > fx:
                    # North flank: Land North, Water South -> Margin at y = fy
                    descriptors.append({
                        'orientation': Directions.UP.value,
                        'axis': 'x',
                        'start': fx,
                        'end': corridor_end,
                        'margin_coord': fy,
                        'probe_coord': fy - 1
                    })
                    # South flank: Land South, Water North -> Margin at y = fy + fl - 32
                    descriptors.append({
                        'orientation': Directions.DOWN.value,
                        'axis': 'x',
                        'start': fx,
                        'end': corridor_end,
                        'margin_coord': fy + fl - 32,
                        'probe_coord': fy + fl + 1
                    })
                if pool is None:
                    descriptors.append({
                        'orientation': Directions.RIGHT.value,
                        'axis': 'y',
                        'start': fy,
                        'end': fy + fl,
                        'margin_coord': fx + stream_length - 32,
                        'probe_coord': fx + stream_length + 1
                    })

            elif direction_str == Directions.LEFT.value:
                corridor_start = (pool.x + pool.w) if (pool is not None and (pool.x + pool.w) < fx) else (fx - stream_length)
                if fx > corridor_start:
                    # North flank: Land North, Water South
                    descriptors.append({
                        'orientation': Directions.UP.value,
                        'axis': 'x',
                        'start': corridor_start,
                        'end': fx,
                        'margin_coord': fy,
                        'probe_coord': fy - 1
                    })
                    # South flank: Land South, Water North
                    descriptors.append({
                        'orientation': Directions.DOWN.value,
                        'axis': 'x',
                        'start': corridor_start,
                        'end': fx,
                        'margin_coord': fy + fl - 32,
                        'probe_coord': fy + fl + 1
                    })
                if pool is None:
                    descriptors.append({
                        'orientation': Directions.LEFT.value,
                        'axis': 'y',
                        'start': fy,
                        'end': fy + fl,
                        'margin_coord': fx - stream_length,
                        'probe_coord': fx - stream_length - 1
                    })

        if pool is not None:
            # North pool margin: Land North, Water South -> Top of pool
            descriptors.append({
                'orientation': Directions.UP.value,
                'axis': 'x',
                'start': pool.x,
                'end': pool.x + pool.w,
                'margin_coord': pool.y,
                'probe_coord': pool.y - 1
            })
            # South pool margin: Land South, Water North -> Bottom of pool
            descriptors.append({
                'orientation': Directions.DOWN.value,
                'axis': 'x',
                'start': pool.x,
                'end': pool.x + pool.w,
                'margin_coord': pool.y + pool.l - 32,
                'probe_coord': pool.y + pool.l + 1
            })
            # West pool margin: Land West, Water East -> Left of pool
            descriptors.append({
                'orientation': Directions.LEFT.value,
                'axis': 'y',
                'start': pool.y,
                'end': pool.y + pool.l,
                'margin_coord': pool.x,
                'probe_coord': pool.x - 1
            })
            # East pool margin: Land East, Water West -> Right of pool
            descriptors.append({
                'orientation': Directions.RIGHT.value,
                'axis': 'y',
                'start': pool.y,
                'end': pool.y + pool.l,
                'margin_coord': pool.x + pool.w - 32,
                'probe_coord': pool.x + pool.w + 1
            })

        return descriptors


    def _build_shoreline_hitbox(self, orientation: str, length: int, thickness: int = 8) -> Hitbox:
        """
        Constructs a narrow sensor strip aligned along the water perimeter threshold.
        """
        if orientation == Directions.UP.value:
            # Land North -> Sensor sits on northernmost slice of water
            return Hitbox(Position(0, 0), Dimensions(length, thickness))
        elif orientation == Directions.DOWN.value:
            # Land South -> Sensor sits on southernmost slice of water
            return Hitbox(Position(0, 32 - thickness), Dimensions(length, thickness))
        elif orientation == Directions.LEFT.value:
            # Land West  -> Sensor sits on westernmost slice of water
            return Hitbox(Position(0, 0), Dimensions(thickness, length))
        elif orientation == Directions.RIGHT.value:
            # Land East  -> Sensor sits on easternmost slice of water
            return Hitbox(Position(32 - thickness, 0), Dimensions(thickness, length))
        return Hitbox(Position(0, 0), Dimensions(length, thickness))


    def _generate_shorelines(
        self, 
        fluid: Asset, 
        board: Board, 
        stream_length: int, 
        pool: Optional[Pool]
    ) -> List[Asset]:
        """
        Samples unoccluded flank margins, resolves secondary indices against bordering tiles,
        and coalesces contiguous segments into Shoreline assets anchored directly on water margins.
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
            margin_coord = desc['margin_coord']
            probe_coord = desc['probe_coord']

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
                    shore_x, shore_y = c, margin_coord
                    probe_x, probe_y = c, probe_coord
                    probe_w, probe_l = step_len, 1
                    center_x, center_y = c + step_len // 2, margin_coord + 16
                else:
                    shore_x, shore_y = margin_coord, c
                    probe_x, probe_y = probe_coord, c
                    probe_w, probe_l = 1, step_len
                    center_x, center_y = margin_coord + 16, c + step_len // 2

                # 1. Skip if land-side probe point is flooded by ANY fluid (water meeting water)
                if self._is_water(probe_x, probe_y, layer, board):
                    commit_segment()
                    c += step_len
                    continue

                # 2. Skip if the shoreline tile center is submerged under a different fluid
                if self._is_water_excluding(center_x, center_y, layer, board, exclude_name=fluid.name):
                    commit_segment()
                    c += step_len
                    continue

                # 3. Skip if bordering substrate is occluded by boundary or obstacle
                if self._detect_flank_occlusions(probe_x, probe_y, probe_w, probe_l, layer, board):
                    commit_segment()
                    c += step_len
                    continue

                # 4. Query adjacent background substrate tile
                tile = board.tile(layer, Position(probe_x, probe_y))
                if not tile:
                    commit_segment()
                    c += step_len
                    continue

                # 5. Resolve shoreline asset key from secondary index
                shoreline_id = self.shorelines.resolve(tile.id, fluid.id)
                if not shoreline_id:
                    commit_segment()
                    c += step_len
                    continue

                thickness = 8
                shore_props = board.cradle.spawnables.shorelines.get(shoreline_id)
                if shore_props and hasattr(shore_props, 'thickness'):
                    thickness = shore_props.thickness

                # 6. Coalesce contiguous runs
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
                        'pos': Position(shore_x, shore_y),
                        'length': step_len,
                        'orientation': orientation,
                        'thickness': thickness,
                        'expected_next': c + step_len
                    }

                c += step_len

            commit_segment()

        return new_shorelines


    def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        layer = fluid.state.layer

        # 1. Purge previous child shorelines
        if fluid.state.shorelines:
            old_shorelines = [
                board.asset(name, layer) 
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

        # 2. Generate and link new child shorelines on water margins
        new_shorelines = self._generate_shorelines(fluid, board, stream_length, pool_bounds)
        if new_shorelines:
            board.add(new_shorelines)
            fluid.state.shorelines = [s.name for s in new_shorelines]

        # 3. Clean up any existing shorelines on the layer submerged by expanding water
        all_shorelines = board.instances(AssetInstances.SHORELINES.value, layer)
        submerged_shorelines = []
        for s in all_shorelines:
            scx = s.state.position.x + 16
            scy = s.state.position.y + 16
            if self._is_water_excluding(scx, scy, layer, board, exclude_name=s.state.parent_fluid):
                submerged_shorelines.append(s)

        if submerged_shorelines:
            board.remove(submerged_shorelines)
            for s in submerged_shorelines:
                parent = board.asset(s.state.parent_fluid, layer)
                if parent and hasattr(parent.state, "shorelines") and s.name in parent.state.shorelines:
                    parent.state.shorelines.remove(s.name)

        logger.info(
            f"Fluid(name={fluid.name}, direction={direction}) | "
            f" Length: {stream_length}px,  "
            f"Struck: {getattr(struck_obstacle, 'name', 'bounds')}, "
            f"Pool: {pool_bounds is not None}, "
            f"Shorelines: {len(new_shorelines)}"
        )

        return stream_length, pool_bounds, hitboxes