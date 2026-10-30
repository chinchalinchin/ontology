"""
@domain.logic
@app.services
@workflow.generation
@workflow.ecology
@workflow.fluids

# Ontology: Source - app.services.generators.game.cartographer

Module for Cartographer generator class.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    TYPE_CHECKING,
)

# Application Libraries
import app.game.logic.predicates as predicates
from app.assets.base import Asset
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
)
from libs.core.math import geometry
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position,
)

if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.logic.relations.shorelines import ShorelineIndex

logger = logging.getLogger(__name__)

STEP_SIZE = 32


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
        shores = board.shorelines(layer)
        if shores:
            board.remove(list(shores))

    @classmethod
    def _collect_water_rectangles(cls, layer: str, board: Board) -> List[Tuple[int, int, int, int]]:
        """
        Extracts active fluid stream corridors, annular pools, and child branch
        corridors into primitive (min_x, min_y, max_x, max_y) AABB tuples for contour sweeps.
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

            # 3. Child branch corridors
            for branch in getattr(fluid.state, "branches", None) or []:
                if branch.length <= 0:
                    continue
                bx = branch.position.x
                by = branch.position.y
                b_dir = branch.source
                b_dir_str = b_dir.value if hasattr(b_dir, "value") else str(b_dir)

                if b_dir_str == Directions.DOWN.value:
                    rects.append((bx, by, bx + fw, by + branch.length))
                elif b_dir_str == Directions.UP.value:
                    rects.append((bx, by - branch.length, bx + fw, by))
                elif b_dir_str == Directions.RIGHT.value:
                    rects.append((bx, by, bx + branch.length, by + fl))
                elif b_dir_str == Directions.LEFT.value:
                    rects.append((bx - branch.length, by, bx, by + fl))

            # 4. Compound hitboxes (captures secondary pools from recursive bifurcations)
            for hb in getattr(fluid.state, "hitboxes", None) or []:
                if hb.dimensions.w > 0 and hb.dimensions.l > 0:
                    rect = (
                        fx + hb.position.x,
                        fy + hb.position.y,
                        fx + hb.position.x + hb.dimensions.w,
                        fy + hb.position.y + hb.dimensions.l,
                    )
                    if rect not in rects:
                        rects.append(rect)

        return rects

    @classmethod
    def _resolve_fluid_id(
        cls,
        board: Board,
        layer: str,
        axis: str,
        sample_c: int,
        water_coord: int,
    ) -> Optional[str]:
        """
        Identifies the fluid entity occupying the interior water coordinate adjacent to the margin.
        """
        water_pos = Position(sample_c, water_coord) if axis == 'x' else Position(water_coord, sample_c)
        fluids = board.instances(AssetInstances.FLUIDS.value, layer)

        for fluid in fluids:
            fx = fluid.state.position.x
            fy = fluid.state.position.y

            for hb in fluid.hitboxes:
                hx = fx + hb.position.x
                hy = fy + hb.position.y
                if (
                    hx <= water_pos.x <= hx + hb.dimensions.w
                    and hy <= water_pos.y <= hy + hb.dimensions.l
                ):
                    return fluid.id

            pool = fluid.state.pool
            if pool and pool.w > 0 and pool.l > 0:
                if geometry.inside(water_pos.x, water_pos.y, [(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)]):
                    return fluid.id

            if fluid.state.length > 0 and predicates.in_stream(water_pos, fluid):
                return fluid.id

        return None

    @classmethod
    def _build_shoreline_hitbox(
        cls,
        orientation: str,
        length: int,
        thickness: int = 8,
        dimensions: Optional[Dimensions] = None,
    ) -> Hitbox:
        """
        Constructs a narrow sensor strip aligned along the water perimeter threshold.
        """
        tile_w = dimensions.w if dimensions is not None else STEP_SIZE
        tile_l = dimensions.l if dimensions is not None else STEP_SIZE

        if orientation == Directions.UP.value:
            return Hitbox(Position(0, 0), Dimensions(length, thickness))
        elif orientation == Directions.DOWN.value:
            return Hitbox(Position(0, max(0, tile_l - thickness)), Dimensions(length, thickness))
        elif orientation == Directions.LEFT.value:
            return Hitbox(Position(0, 0), Dimensions(thickness, length))
        elif orientation == Directions.RIGHT.value:
            return Hitbox(Position(max(0, tile_w - thickness), 0), Dimensions(thickness, length))
        return Hitbox(Position(0, 0), Dimensions(length, thickness))

    @classmethod
    def is_step_fluid(
        cls,
        board: Board,
        layer: str,
        axis: str,
        start_c: int,
        length: int,
        fixed_coord: int,
    ) -> bool:
        """
        Samples whether the 1D interval along active axis intersects water on the layer.
        """
        mid_c = start_c + length // 2
        for c in (mid_c, start_c + 1, start_c + length - 1):
            pos = Position(c, fixed_coord) if axis == 'x' else Position(fixed_coord, c)
            if board.fluid(layer, pos):
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
        axis: Optional[str] = None,
        elevation: int = 0,
    ) -> bool:
        """
        Validates whether the substrate bordering the water is occluded by
        map boundaries or immovable static obstacles (mass == 0) on the specified elevation tier.
        """
        sizes = board.size(layer)
        layer_size = sizes[0] if sizes else None
        if layer_size and layer_size.w > 0 and layer_size.l > 0:
            if x < 0 or y < 0 or (x + w) > layer_size.w or (y + l) > layer_size.l:
                return True

        perimeters = board.perimeters.get(layer, {}).get(elevation, [])
        perim_obstacles = [
            (b.position.x, b.position.y, b.dimensions.w, b.dimensions.l)
            for b in perimeters
            if not (axis == 'y' and b.dimensions.l == 1)
            and not (axis == 'x' and b.dimensions.w == 1)
        ]
        if perim_obstacles and geometry.occluded(x, y, w, l, perim_obstacles):
            return True

        candidates = set(board.weights(layer, elevation=elevation))
        candidates.update(board.obstacles(layer, elevation=elevation))
        candidate_obstacles: List[Tuple[int, int, int, int]] = []

        for asset in candidates:
            if asset.category in (AssetCategories.SHEETS.value, AssetCategories.EFFECTS.value):
                continue
            if asset.instance == AssetInstances.RAFTS.value:
                continue
            if asset.instance == AssetInstances.GATES.value and asset.state.switch:
                continue
            if hasattr(asset.properties, "mass") and asset.properties.mass != 0:
                continue

            for hb in asset.hitboxes:
                candidate_obstacles.append((
                    asset.state.position.x + hb.position.x,
                    asset.state.position.y + hb.position.y,
                    hb.dimensions.w,
                    hb.dimensions.l,
                ))

        return bool(candidate_obstacles and geometry.occluded(x, y, w, l, candidate_obstacles))

    @classmethod
    def _resolve_step(
        cls,
        desc: Dict,
        c: int,
        step_len: int,
        layer: str,
        board: Board,
        index: ShorelineIndex,
        season: Optional[str],
    ) -> Optional[str]:
        """
        Evaluates a single step along a contour descriptor and returns the resolved
        shoreline Asset ID, or None if the step is submerged, occluded, or unmapped.
        """
        axis = desc['axis']
        probe_coord = desc['probe_coord']
        water_coord = desc.get('water_coord', desc['margin_coord'] + 16)

        # 1. Water-to-water junction: skip if land-side probe intersects water
        if cls.is_step_fluid(board, layer, axis, c, step_len, probe_coord):
            logger.info(
                f"Telemetry:Cartographer:SkipWaterJunction orientation={desc['orientation']} "
                f"axis={axis} c={c} probe_coord={probe_coord}"
            )
            return None

        # 2. Boundary or static obstacle occlusion on bordering substrate
        if axis == 'x':
            probe_x, probe_y, probe_w, probe_l = c, probe_coord, step_len, 1
        else:
            probe_x, probe_y, probe_w, probe_l = probe_coord, c, 1, step_len

        if cls._detect_flank_occlusions(probe_x, probe_y, probe_w, probe_l, layer, board, axis=axis):
            return None

        # 3. Adjacent background substrate tile at step midpoint
        sample_c = c + step_len // 2
        probe_pos = Position(sample_c, probe_coord) if axis == 'x' else Position(probe_coord, sample_c)
        tile = board.tile(layer, probe_pos)
        if not tile:
            return None

        # 4. Relational shoreline lookup for (tile, fluid, season)
        fluid_id = cls._resolve_fluid_id(board, layer, axis, sample_c, water_coord)
        return index.resolve(tile.id, fluid_id, season=season)

    @classmethod
    def _shoreline_position(
        cls,
        orientation: str,
        c: int,
        margin_coord: int,
        dimensions: Dimensions,
    ) -> Position:
        """
        Computes the top-left world coordinate for a shoreline segment.
        """
        if orientation == Directions.UP.value:
            return Position(c, margin_coord)
        elif orientation == Directions.DOWN.value:
            return Position(c, margin_coord - dimensions.l)
        elif orientation == Directions.LEFT.value:
            return Position(margin_coord, c)
        return Position(margin_coord - dimensions.w, c)

    @classmethod
    def _spawn_segment(
        cls,
        segment: Dict,
        layer: str,
        board: Board,
    ) -> Asset:
        """
        Instantiates a coalesced Shoreline Asset via the Board's Cradle service.
        """
        hb = cls._build_shoreline_hitbox(
            segment['orientation'],
            segment['length'],
            segment['thickness'],
            dimensions=segment['dimensions'],
        )
        shore_asset = board.cradle.spawn_shoreline(
            id=segment['id'],
            layer=layer,
            position=segment['pos'],
            orientation=segment['orientation'],
            length=segment['length'],
            hitboxes=[hb],
        )
        if segment['season']:
            shore_asset.state.season = segment['season']

        logger.debug(
            f"Cartographer: Spawned shoreline '{shore_asset.name}' "
            f"(id='{shore_asset.id}', orientation='{segment['orientation']}', "
            f"length={segment['length']}, season='{shore_asset.state.season}')"
        )
        return shore_asset

    @classmethod
    def _coalesce_segments(
        cls,
        descriptors: List[Dict],
        layer: str,
        board: Board,
        index: ShorelineIndex,
    ) -> List[Asset]:
        """
        Evaluates descriptors against substrate terrain and occluders, coalescing
        contiguous runs into unified Shoreline entities.
        """
        if not board.cradle:
            return []

        season = board.calendar.season if board.calendar else None
        new_shorelines: List[Asset] = []

        for desc in descriptors:
            curr_seg: Optional[Dict] = None

            for c in range(desc['start'], desc['end'], STEP_SIZE):
                step_len = min(STEP_SIZE, desc['end'] - c)
                shoreline_id = cls._resolve_step(desc, c, step_len, layer, board, index, season)

                if not shoreline_id:
                    if curr_seg is not None:
                        new_shorelines.append(cls._spawn_segment(curr_seg, layer, board))
                        curr_seg = None
                    continue

                if curr_seg is not None and curr_seg['id'] == shoreline_id:
                    curr_seg['length'] += step_len
                    continue

                if curr_seg is not None:
                    new_shorelines.append(cls._spawn_segment(curr_seg, layer, board))

                shore_props = board.cradle.spawnables.shorelines.get(shoreline_id)
                curr_seg = {
                    'id': shoreline_id,
                    'pos': cls._shoreline_position(
                        desc['orientation'],
                        c,
                        desc['margin_coord'],
                        shore_props.dimensions,
                    ),
                    'length': step_len,
                    'orientation': desc['orientation'],
                    'thickness': shore_props.thickness,
                    'dimensions': shore_props.dimensions,
                    'season': season,
                }

            if curr_seg is not None:
                new_shorelines.append(cls._spawn_segment(curr_seg, layer, board))

        return new_shorelines

    @classmethod
    def _build_descriptor(
        cls,
        x: int,
        y: int,
        w: int,
        l: int,
        orientation: str,
    ) -> Dict:
        """
        Translates a raw (x, y, w, l, orientation) contour tuple into a 1D sweep descriptor.
        """
        if orientation in (Directions.UP.value, Directions.DOWN.value):
            is_up = orientation == Directions.UP.value
            return {
                'orientation': orientation,
                'axis': 'x',
                'start': x,
                'end': x + w,
                'margin_coord': y,
                'probe_coord': y - 1 if is_up else y + 1,
                'water_coord': y + 1 if is_up else y - 1,
            }

        is_left = orientation == Directions.LEFT.value
        return {
            'orientation': orientation,
            'axis': 'y',
            'start': y,
            'end': y + l,
            'margin_coord': x,
            'probe_coord': x - 1 if is_left else x + 1,
            'water_coord': x + 1 if is_left else x - 1,
        }

    @classmethod
    def generate(
        cls,
        layer: str,
        board: Board,
        index: ShorelineIndex,
    ) -> List[Asset]:
        """
        Synthesizes procedural shoreline assets across the aggregate water boundaries
        of the specified layer using contour analysis.
        """
        water_rects = cls._collect_water_rectangles(layer, board)
        if not water_rects:
            return []

        logger.info(f"Telemetry:Cartographer:{layer}:CollectedWaterRects={water_rects}")
        boundaries = geometry.contours(water_rects)
        logger.info(f"Telemetry:Cartographer:{layer}:DerivedContours={boundaries}")

        descriptors = [cls._build_descriptor(*b) for b in boundaries]
        return cls._coalesce_segments(descriptors, layer, board, index)