"""
# Ontology: app.services.generators.game.cartographer

Module for Cartographer generator class.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    List, 
    Dict, 
    Tuple,
    Optional,
    TYPE_CHECKING
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from libs.core.math import geometry
from libs.core.models import (
    Boundary,
    Dimensions,
    Hitbox,
    Position
)

if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.logic.relations.shorelines import ShorelineIndex

logger = logging.getLogger(__name__)


class Cartographer:
    """
    Stateless geometric generator synthesizing environmental shoreline margins across
    layer-wide water bodies using sweep-line contour analysis.
    """

    @classmethod
    def purge(cls, layer: str, board: Board) -> None:
        """
        Safely disposes of all procedural shoreline assets on the specified layer.
        """
        shores = board.get_shorelines(layer)
        if shores:
            board.remove(list(shores))

    @classmethod
    def _collect_water_rectangles(cls, layer: str, board: Board) -> List[Tuple[int, int, int, int]]:
        """
        Extracts active fluid stream corridors and annular pools on the layer
        into primitive (min_x, min_y, max_x, max_y) AABB tuples for contour sweeps.
        """
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        rects: List[Tuple[int, int, int, int]] = []

        for fluid in fluids:
            fx = fluid.state.position.x
            fy = fluid.state.position.y
            fw = fluid.properties.dimensions.w
            fl = fluid.properties.dimensions.l
            length = fluid.state.length
            direction = fluid.state.source
            direction_str = direction.value if hasattr(direction, "value") else str(direction)

            # 1. Directional stream corridor bounding box
            if length > 0:
                if direction_str == Directions.DOWN.value:
                    rects.append((fx, fy, fx + fw, fy + length))
                elif direction_str == Directions.UP.value:
                    rects.append((fx, fy - length, fx + fw, fy))
                elif direction_str == Directions.RIGHT.value:
                    rects.append((fx, fy, fx + length, fy + fl))
                elif direction_str == Directions.LEFT.value:
                    rects.append((fx - length, fy, fx, fy + fl))

            # 2. Annular pool bounding box
            pool = fluid.state.pool
            if pool is not None and pool.w > 0 and pool.l > 0:
                rects.append((pool.x, pool.y, pool.x + pool.w, pool.y + pool.l))

        return rects

    @classmethod
    def _detect_boundary_orientation(
        cls, 
        boundary: Boundary, 
        layer: str, 
        board: Board
    ) -> Optional[Dict]:
        """
        Identifies the directional water-to-land threshold for a contour boundary segment
        by probing adjacent normal coordinates against board.water.
        """
        bx = boundary.position.x
        by = boundary.position.y
        bw = boundary.dimensions.w
        bl = boundary.dimensions.l

        # Horizontal boundary: length along X, thickness 1 along Y
        if bl == 1:
            mid_x = bx + bw // 2
            is_south_water = board.water(layer, Position(mid_x, by))
            is_north_water = board.water(layer, Position(mid_x, by - 1))

            if is_south_water and not is_north_water:
                return {
                    'orientation': Directions.UP.value,
                    'axis': 'x',
                    'start': bx,
                    'end': bx + bw,
                    'margin_coord': by,
                    'probe_coord': by - 1
                }
            elif is_north_water and not is_south_water:
                return {
                    'orientation': Directions.DOWN.value,
                    'axis': 'x',
                    'start': bx,
                    'end': bx + bw,
                    'margin_coord': by - 32,
                    'probe_coord': by + 1
                }

        # Vertical boundary: thickness 1 along X, length along Y
        elif bw == 1:
            mid_y = by + bl // 2
            is_east_water = board.water(layer, Position(bx, mid_y))
            is_west_water = board.water(layer, Position(bx - 1, mid_y))

            if is_east_water and not is_west_water:
                return {
                    'orientation': Directions.LEFT.value,
                    'axis': 'y',
                    'start': by,
                    'end': by + bl,
                    'margin_coord': bx,
                    'probe_coord': bx - 1
                }
            elif is_west_water and not is_east_water:
                return {
                    'orientation': Directions.RIGHT.value,
                    'axis': 'y',
                    'start': by,
                    'end': by + bl,
                    'margin_coord': bx - 32,
                    'probe_coord': bx + 1
                }

        return None

    @classmethod
    def _resolve_fluid_id(
        cls,
        board: Board,
        layer: str,
        axis: str,
        sample_c: int,
        margin_coord: int
    ) -> Optional[str]:
        """
        Identifies the fluid entity occupying the interior water coordinate adjacent to the margin.
        """
        water_fixed = margin_coord + 16
        water_pos = Position(sample_c, water_fixed) if axis == 'x' else Position(water_fixed, sample_c)
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)
        for fluid in fluids:
            pool = fluid.state.pool
            if pool and pool.x <= water_pos.x < pool.x + pool.w and pool.y <= water_pos.y < pool.y + pool.l:
                return fluid.id
            if fluid.state.length > 0 and board._in_stream(water_pos, fluid):
                return fluid.id
        return None

    @classmethod
    def _build_shoreline_hitbox(cls, orientation: str, length: int, thickness: int = 8) -> Hitbox:
        """
        Constructs a narrow sensor strip aligned along the water perimeter threshold.
        """
        if orientation == Directions.UP.value:
            return Hitbox(Position(0, 0), Dimensions(length, thickness))
        elif orientation == Directions.DOWN.value:
            return Hitbox(Position(0, 32 - thickness), Dimensions(length, thickness))
        elif orientation == Directions.LEFT.value:
            return Hitbox(Position(0, 0), Dimensions(thickness, length))
        elif orientation == Directions.RIGHT.value:
            return Hitbox(Position(32 - thickness, 0), Dimensions(thickness, length))
        return Hitbox(Position(0, 0), Dimensions(length, thickness))

    @classmethod
    def _is_step_water(
        cls,
        board: Board,
        layer: str,
        axis: str,
        start_c: int,
        length: int,
        fixed_coord: int
    ) -> bool:
        """
        Samples whether the 1D interval along active axis intersects water on the layer.
        Evaluates the midpoint and boundaries to prevent sub-tile alignment mismatch.
        """
        mid_c = start_c + length // 2
        samples = [mid_c, start_c + 1, start_c + length - 1]
        for c in samples:
            pos = Position(c, fixed_coord) if axis == 'x' else Position(fixed_coord, c)
            if board.water(layer, pos):
                return True
        return False

    @classmethod
    def _detect_flank_occlusions(
        cls, 
        x: int, 
        y: int, 
        w: int, 
        l: int, 
        layer: str, 
        board: Board,
        axis: Optional[str] = None
    ) -> bool:
        """
        Validates whether the substrate bordering the water is occluded by
        map boundaries or immovable static obstacles (mass == 0).
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

            # Ignore orthogonal 1px perimeter boundary segments
            if axis == 'y' and bl == 1:
                continue
            if axis == 'x' and bw == 1:
                continue

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

            if hasattr(asset.properties, "mass") and asset.properties.mass != 0:
                continue

            for hb in asset.hitboxes:
                ox = asset.state.position.x + hb.position.x
                oy = asset.state.position.y + hb.position.y
                ow = hb.dimensions.w
                ol = hb.dimensions.l

                if x < ox + ow and x + w > ox and y < oy + ol and y + l > oy:
                    return True

        return False

    @classmethod
    def _coalesce_segments(
        cls,
        descriptors: List[Dict],
        layer: str,
        board: Board,
        index: ShorelineIndex
    ) -> List[Asset]:
        """
        Evaluates descriptors against substrate terrain and occluders, coalescing
        contiguous runs into unified Shoreline entities.
        """
        if not board.cradle:
            return []

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
                    hb = cls._build_shoreline_hitbox(
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
                    probe_w, probe_l = step_len, 1
                else:
                    shore_x, shore_y = margin_coord, c
                    probe_w, probe_l = 1, step_len

                # 1. Water-to-water junction: skip if land-side probe intersects water
                if cls._is_step_water(board, layer, axis, c, step_len, probe_coord):
                    commit_segment()
                    c += step_len
                    continue

                # 2. Skip if bordering substrate is occluded by boundary or obstacle (Fix B012)
                probe_x = c if axis == 'x' else probe_coord
                probe_y = probe_coord if axis == 'x' else c
                if cls._detect_flank_occlusions(probe_x, probe_y, probe_w, probe_l, layer, board, axis=axis):
                    commit_segment()
                    c += step_len
                    continue

                # 3. Query adjacent background substrate tile at step midpoint
                sample_c = c + step_len // 2
                probe_pos = Position(sample_c, probe_coord) if axis == 'x' else Position(probe_coord, sample_c)
                tile = board.tile(layer, probe_pos)
                if not tile:
                    commit_segment()
                    c += step_len
                    continue

                # 4. Resolve shoreline asset key from secondary relational index
                fluid_id = cls._resolve_fluid_id(board, layer, axis, sample_c, margin_coord)
                shoreline_id = index.resolve(tile.id, fluid_id)
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
                        'pos': Position(shore_x, shore_y),
                        'length': step_len,
                        'orientation': orientation,
                        'thickness': thickness,
                        'expected_next': c + step_len
                    }

                c += step_len

            commit_segment()

        return new_shorelines

    @classmethod
    def generate(
        cls,
        layer: str,
        board: Board,
        index: ShorelineIndex
    ) -> List[Asset]:
        """
        Synthesizes procedural shoreline assets across the aggregate water boundaries
        of the specified layer using contour analysis.
        """
        water_rects = cls._collect_water_rectangles(layer, board)
        if not water_rects:
            return []
        boundaries = geometry.contours(water_rects)
        descriptors = []
        for b in boundaries:
            desc = cls._detect_boundary_orientation(b, layer, board)
            if desc:
                descriptors.append(desc)
        return cls._coalesce_segments(descriptors, layer, board, index)