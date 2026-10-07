"""
# Ontology: app.services.generators.game.actuator

Package for constructing Fluid Effect flows and radial pools.
"""
from __future__ import annotations

# Standard Libraries
import math
import logging
from typing import (
    List, 
    Optional, 
    Tuple, 
    TYPE_CHECKING
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from app.game.board.fields import MoistureField
from app.models.state import (
    Pool, 
    Branch
)

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
    Stateless service calculating raycast stream truncation, annular pooling,
    and downstream flank bifurcation networks.
    """

    def _collect_obstacles(
        self, 
        fluid: Asset, 
        board: Board, 
        direction: str,
        origin_x: Optional[int] = None,
        origin_y: Optional[int] = None
    ) -> List[Tuple]:
        layer = fluid.state.layer
        fx = origin_x if origin_x is not None else fluid.state.position.x
        fy = origin_y if origin_y is not None else fluid.state.position.y
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

            # Exclude dynamic bodies (mass > 0) and sensors (mass < 0) from fluid occlusion
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

        return obstacle_tuples


    def _calculate_max_distance(
        self, 
        x: int, 
        y: int, 
        board: Board, 
        layer: str, 
        direction: str
    ) -> int:
        sizes = board.size(layer)
        layer_size = sizes[0] if sizes else None

        if not layer_size or layer_size.w == 0 or layer_size.l == 0:
            return 10000

        if direction == Directions.DOWN.value:
            return max(0, layer_size.l - y)
        elif direction == Directions.UP.value:
            return max(0, y)
        elif direction == Directions.RIGHT.value:
            return max(0, layer_size.w - x)
        elif direction == Directions.LEFT.value:
            return max(0, x)

        return 10000


    def _build_stream_hitbox(
        self, 
        direction: str, 
        length: int, 
        fw: int, 
        fl: int
    ) -> Optional[Hitbox]:
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
        Calculates an annular pool boundary surrounding an obstacle struck by fluid.
        Snaps pool boundaries to tile grid multiples.
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


    def _calculate_branch_discharges(
        self,
        pool: Pool, 
        direction: str, 
        flow: int, 
        fw: int, 
        fl: int
    ) -> List[Tuple[Position, str, int]]:
        """
        Derives secondary stream discharge coordinates flush with the downstream
        margin and lateral flanks of the annular pool.
        """
        child_flow = flow - 1
        if child_flow <= 0:
            return []

        if direction == Directions.DOWN.value:
            y = pool.y + pool.l
            left_pos = Position(pool.x, y)
            right_pos = Position(pool.x + pool.w - fw, y)
            return [(left_pos, direction, child_flow), (right_pos, direction, child_flow)]
        elif direction == Directions.UP.value:
            y = pool.y
            left_pos = Position(pool.x, y)
            right_pos = Position(pool.x + pool.w - fw, y)
            return [(left_pos, direction, child_flow), (right_pos, direction, child_flow)]
        elif direction == Directions.RIGHT.value:
            x = pool.x + pool.w
            top_pos = Position(x, pool.y)
            bottom_pos = Position(x, pool.y + pool.l - fl)
            return [(top_pos, direction, child_flow), (bottom_pos, direction, child_flow)]
        elif direction == Directions.LEFT.value:
            x = pool.x
            top_pos = Position(x, pool.y)
            bottom_pos = Position(x, pool.y + pool.l - fl)
            return [(top_pos, direction, child_flow), (bottom_pos, direction, child_flow)]

        return []


    def compile_moisture_field(self, layer: str, board: Board) -> MoistureField:
        """
        Constructs a MoistureField representing the linear superposition of all active
        stream corridors, annular pools, and branches across the layer.
        """
        field = MoistureField()
        layer_fluids = board.instances(AssetInstances.FLUIDS.value, layer)

        for fluid in layer_fluids:
            fx = fluid.state.position.x
            fy = fluid.state.position.y
            fw = fluid.properties.dimensions.w
            fl = fluid.properties.dimensions.l
            flow = fluid.state.flow
            length = fluid.state.length
            direction = fluid.state.source
            dir_val = direction.value if hasattr(direction, "value") else str(direction)

            # 1. Linear parent corridor line segment
            if length > 0 and flow > 0:
                mid_x = fx + (fw // 2)
                mid_y = fy + (fl // 2)
                if dir_val == Directions.DOWN.value:
                    field.add_stream(mid_x, fy, mid_x, fy + length, flow)
                elif dir_val == Directions.UP.value:
                    field.add_stream(mid_x, fy, mid_x, fy - length, flow)
                elif dir_val == Directions.RIGHT.value:
                    field.add_stream(fx, mid_y, fx + length, mid_y, flow)
                elif dir_val == Directions.LEFT.value:
                    field.add_stream(fx, mid_y, fx - length, mid_y, flow)

            # 2. Annular pool disk source
            pool = fluid.state.pool
            if pool and pool.w > 0 and pool.l > 0 and flow > 0:
                cx = pool.x + (pool.w / 2.0)
                cy = pool.y + (pool.l / 2.0)
                radius = 0.5 * math.hypot(pool.w, pool.l)
                field.add_pool(cx, cy, radius, flow)

            # 3. Flank child branch corridors
            if fluid.state.branches:
                for branch in fluid.state.branches:
                    if branch.length <= 0 or branch.flow <= 0:
                        continue
                    bx = branch.position.x
                    by = branch.position.y
                    b_mid_x = bx + (fw // 2)
                    b_mid_y = by + (fl // 2)
                    b_dir = branch.source
                    b_dir_val = b_dir.value if hasattr(b_dir, "value") else str(b_dir)

                    if b_dir_val == Directions.DOWN.value:
                        field.add_stream(b_mid_x, by, b_mid_x, by + branch.length, branch.flow)
                    elif b_dir_val == Directions.UP.value:
                        field.add_stream(b_mid_x, by, b_mid_x, by - branch.length, branch.flow)
                    elif b_dir_val == Directions.RIGHT.value:
                        field.add_stream(bx, b_mid_y, bx + branch.length, b_mid_y, branch.flow)
                    elif b_dir_val == Directions.LEFT.value:
                        field.add_stream(bx, b_mid_y, bx - branch.length, b_mid_y, branch.flow)

        return field

    def propagate(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        """
        Truncates fluid corridor against map bounds and static obstacles, expands annular
        pooling, raycasts downstream flank bifurcation branches, and compiles compound hitboxes.
        """
        source_prop = fluid.state.source
        direction = source_prop.value if hasattr(source_prop, "value") else str(source_prop)        
        flow = fluid.state.flow
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        fx = fluid.state.position.x
        fy = fluid.state.position.y
        layer = fluid.state.layer

        fluid.frame.tile_w = fw
        fluid.frame.tile_l = fl

        obstacle_tuples = self._collect_obstacles(fluid, board, direction)
        max_dist = self._calculate_max_distance(fx, fy, board, layer, direction)

        stream_length, struck_obstacle = geometry.raycast(
            fx,
            fy,
            fw,
            fl,
            direction,
            obstacle_tuples,
            max_dist
        )

        pool_bounds: Optional[Pool] = None
        pool_hitboxes: List[Hitbox] = []
        branches: List[Branch] = []
        branch_compound_hitboxes: List[Hitbox] = []

        # 1. Expand pool and truncate parent corridor at pool boundary
        if isinstance(struck_obstacle, Asset) and flow > 0:
            pool_bounds, pool_hitboxes = self._partition_pool(struck_obstacle, fluid, flow)
            
            if direction == Directions.DOWN.value:
                stream_length = max(0, pool_bounds.y - fy)
            elif direction == Directions.UP.value:
                stream_length = max(0, fy - (pool_bounds.y + pool_bounds.l))
            elif direction == Directions.RIGHT.value:
                stream_length = max(0, pool_bounds.x - fx)
            elif direction == Directions.LEFT.value:
                stream_length = max(0, fx - (pool_bounds.x + pool_bounds.w))

            # 2. Bifurcate downstream flank continuation streams
            if flow > 1:
                discharges = self._calculate_branch_discharges(
                    pool_bounds,
                    direction,
                    flow,
                    fw,
                    fl
                )
                for origin_pos, branch_dir, child_flow in discharges:
                    branch_obstacles = self._collect_obstacles(
                        fluid,
                        board,
                        branch_dir,
                        origin_x=origin_pos.x,
                        origin_y=origin_pos.y
                    )
                    b_max_dist = self._calculate_max_distance(
                        origin_pos.x,
                        origin_pos.y,
                        board,
                        layer,
                        branch_dir
                    )
                    b_len, _ = geometry.raycast(
                        origin_pos.x,
                        origin_pos.y,
                        fw,
                        fl,
                        branch_dir,
                        branch_obstacles,
                        b_max_dist
                    )
                    if b_len > 0:
                        b_hb = self._build_stream_hitbox(branch_dir, b_len, fw, fl)
                        b_hitboxes = [b_hb] if b_hb else []
                        branches.append(
                            Branch(
                                position=origin_pos,
                                source=branch_dir,
                                flow=child_flow,
                                length=b_len,
                                hitboxes=b_hitboxes
                            )
                        )

                        # Compound hitbox relative to fluid origin (fx, fy)
                        if branch_dir == Directions.DOWN.value:
                            branch_compound_hitboxes.append(
                                Hitbox(Position(origin_pos.x - fx, origin_pos.y - fy), Dimensions(fw, b_len))
                            )
                        elif branch_dir == Directions.UP.value:
                            branch_compound_hitboxes.append(
                                Hitbox(Position(origin_pos.x - fx, origin_pos.y - fy - b_len), Dimensions(fw, b_len))
                            )
                        elif branch_dir == Directions.RIGHT.value:
                            branch_compound_hitboxes.append(
                                Hitbox(Position(origin_pos.x - fx, origin_pos.y - fy), Dimensions(b_len, fl))
                            )
                        elif branch_dir == Directions.LEFT.value:
                            branch_compound_hitboxes.append(
                                Hitbox(Position(origin_pos.x - fx - b_len, origin_pos.y - fy), Dimensions(b_len, fl))
                            )

        # 3. Assemble compound relative hitboxes
        hitboxes: List[Hitbox] = []
        stream_hb = self._build_stream_hitbox(direction, stream_length, fw, fl)
        if stream_hb:
            hitboxes.append(stream_hb)
        if pool_hitboxes:
            hitboxes.extend(pool_hitboxes)
        if branch_compound_hitboxes:
            hitboxes.extend(branch_compound_hitboxes)

        fluid.state.length = stream_length
        fluid.state.pool = pool_bounds
        fluid.state.branches = branches
        fluid.state.hitboxes = hitboxes
        fluid.state.dirty = False
        fluid.state._keys.clear()

        # 4. Compile and assign continuous hydrological superposition field to Board
        moisture_field = self.compile_moisture_field(layer, board)
        board.set_moisture_field(layer, moisture_field)

        return stream_length, pool_bounds, hitboxes


    def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        """
        Unified execution interface for isolated fluid propagation.
        """
        return self.propagate(fluid, board)