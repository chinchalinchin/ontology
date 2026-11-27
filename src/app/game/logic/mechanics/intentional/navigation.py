"""
@domain.concrete
@domain.logic
@app.mechanic
@category.sheets
@modality.intention
@workflow.navigation

# Ontology: Source - app.game.logic.mechanics.intentional.navigation

NavigationMechanics implementation. Manages Sprite Trajectories.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
import math
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Directions,
    Goals,
    NavigationIntentions,
)
import app.static.settings as settings
from app.game.logic.mechanics import Mechanic
from app.game.logic.modules.paths.plan import Planner
from app.game.logic import predicates
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

GoalSignature = Tuple[Optional[str], Optional[Goals], Optional[str]]

HEADING_VECTORS: Dict[Directions, Tuple[float, float]] = {
    Directions.UP: (0.0, -1.0),
    Directions.DOWN: (0.0, 1.0),
    Directions.LEFT: (-1.0, 0.0),
    Directions.RIGHT: (1.0, 0.0),
}
# -----------------------------------------------------

class NavigationMechanics(Mechanic):
    """
    ## NavigationMechanics

    Tactical navigation system executing between TransitionMechanics and MotionMechanics.
    Manages sensory anchors, line-of-sight validation, RRT path generation, dynamic
    waypoint progression, and impassable geometry stall handling.
    """
    _active_goals: Dict[str, GoalSignature]

    def __init__(self):
        super().__init__()
        self._active_goals = {}

    @staticmethod
    def corridor(
        ox: int,
        oy: int,
        w: int,
        l: int,
        length: int,
        direction: str
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Computes half-open world-space AABB bounds (x1, y1, x2, y2) for a single
        directional fluid corridor, matching _in_corridor semantics.
        """
        if length <= 0:
            return None

        if direction == Directions.DOWN:
            return (ox, oy, ox + w, oy + length)
        if direction == Directions.UP:
            return (ox, oy - length, ox + w, oy)
        if direction == Directions.RIGHT:
            return (ox, oy, ox + length, oy + l)
        if direction == Directions.LEFT:
            return (ox - length, oy, ox, oy + l)

        return None


    @staticmethod
    def anchor(asset: Asset) -> Position:
        """
        Calculates the physical sensory origin (footprint center) of an asset.
        """
        hbs = asset.hitboxes
        if not hbs:
            return Position(
                x=asset.state.position.x + asset.dimensions.w // 2,
                y=asset.state.position.y + asset.dimensions.l // 2,
            )
        hb = hbs[0]
        return Position(
            x=asset.state.position.x + hb.position.x + hb.dimensions.w // 2,
            y=asset.state.position.y + hb.position.y + hb.dimensions.l // 2,
        )


    @staticmethod
    def footprint(asset: Asset) -> Tuple[float, float]:
        """
        Calculates the physical hitbox half-extents (half_w, half_l) of a
        navigating asset without squeeze padding.
        """
        hbs = asset.hitboxes
        if hbs:
            return (hbs[0].dimensions.w / 2.0, hbs[0].dimensions.l / 2.0)
        return (asset.dimensions.w / 2.0, asset.dimensions.l / 2.0)


    @classmethod
    def fluids(cls, fluid: Asset) -> List[Tuple[int, int, int, int]]:
        """
        Extracts world-space AABB rectangles (x1, y1, x2, y2) covering a Fluid
        entity's active stream corridors, annular pool, and branches. Uses compiled
        state.hitboxes when populated, falling back to pool/stream/branch bounds.
        """
        fx = int(fluid.state.position.x)
        fy = int(fluid.state.position.y)
        hitboxes = fluid.state.hitboxes

        if hitboxes:
            return [
                (
                    fx + hb.position.x,
                    fy + hb.position.y,
                    fx + hb.position.x + hb.dimensions.w,
                    fy + hb.position.y + hb.dimensions.l,
                )
                for hb in hitboxes
                if hb.dimensions.w > 0 and hb.dimensions.l > 0
            ]

        rects: List[Tuple[int, int, int, int]] = []
        pool = fluid.state.pool
        if pool and pool.w > 0 and pool.l > 0:
            rects.append((pool.x, pool.y, pool.x + pool.w, pool.y + pool.l))

        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        parent = cls.corridor(
            fx, 
            fy, 
            fw, 
            fl, 
            fluid.state.length, 
            fluid.state.source
        )
        if parent is not None:
            rects.append(parent)

        for branch in fluid.state.branches:
            rect = cls.corridor(
                int(branch.position.x),
                int(branch.position.y),
                fw,
                fl,
                branch.length,
                branch.source
            )
            if rect is not None:
                rects.append(rect)

        return rects
    
    
    @classmethod
    def padding(cls, asset: Asset) -> Tuple[float, float]:
        """
        Calculates the Minkowski inflation half-extents (hitbox half-dimensions + squeeze radius)
        for a navigating asset.
        """
        half_w, half_l = cls.footprint(asset)

        squeeze = 0.0
        if (
            asset.state.mutators
            and asset.state.mutators.parameters
            and asset.state.mutators.parameters.squeeze
        ):
            squeeze = float(asset.state.mutators.parameters.squeeze.radius)

        return (half_w + squeeze, half_l + squeeze)


    @staticmethod
    def subtract(
        rect: Tuple[int, int, int, int],
        cutout: Tuple[int, int, int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Computes the exact disjoint 2D AABB difference rect \\ cutout, returning
        up to four residual (x1, y1, x2, y2) rectangles.
        """
        ax1, ay1, ax2, ay2 = rect
        bx1, by1, bx2, by2 = cutout

        if bx2 <= ax1 or bx1 >= ax2 or by2 <= ay1 or by1 >= ay2:
            return [rect]

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        residuals: List[Tuple[int, int, int, int]] = []
        if iy1 > ay1:
            residuals.append((ax1, ay1, ax2, iy1))
        if iy2 < ay2:
            residuals.append((ax1, iy2, ax2, ay2))
        if ix1 > ax1:
            residuals.append((ax1, iy1, ix1, iy2))
        if ix2 < ax2:
            residuals.append((ix2, iy1, ax2, iy2))
        return residuals

    @staticmethod
    def heading(sprite: Asset) -> Tuple[float, float]:
        """
        Resolves a unit heading vector from live velocity when moving,
        falling back to the Sprite's current AnimationState direction.
        """
        vel = sprite.state.velocity
        mag = math.hypot(vel.vx, vel.vy)
        if mag > 1e-3:
            return (vel.vx / mag, vel.vy / mag)
        return HEADING_VECTORS.get(
            sprite.state.animation.direction,
            (0.0, 0.0)
        )
    
    @classmethod
    def _fluid_obstacles(
        cls,
        layer: str,
        board: Board,
        elevation: int,
        pad_x: float,
        pad_y: float
    ) -> List[Tuple[float, float, float, float]]:
        """
        Builds Minkowski-inflated obstacle AABBs for same-elevation Fluid
        corridors and pools, subtracting same-elevation Bridge footprints prior
        to inflation so river crossings remain navigable.
        """
        fluids = board.instances(AssetInstances.FLUIDS, layer, elevation=elevation)
        if not fluids:
            return []

        bridge_rects: List[Tuple[int, int, int, int]] = []
        for bridge in board.bridges(layer):
            if bridge.elevation != elevation:
                continue
            bx = int(bridge.state.position.x)
            by = int(bridge.state.position.y)
            hbs = bridge.hitbox.get(bridge.properties, bridge.state, elevation)
            if hbs:
                for hb in hbs:
                    bridge_rects.append((
                        bx + hb.position.x,
                        by + hb.position.y,
                        bx + hb.position.x + hb.dimensions.w,
                        by + hb.position.y + hb.dimensions.l,
                    ))
            else:
                bridge_rects.append((
                    bx,
                    by,
                    bx + bridge.dimensions.w,
                    by + bridge.dimensions.l,
                ))

        fluid_obstacles: List[Tuple[float, float, float, float]] = []
        for fluid in fluids:
            if not predicates.is_hazard(fluid):
                continue

            rects = cls.fluids(fluid)
            if not rects:
                continue

            for cutout in bridge_rects:
                next_rects: List[Tuple[int, int, int, int]] = []
                for rect in rects:
                    next_rects.extend(cls.subtract(rect, cutout))
                rects = next_rects
                if not rects:
                    break

            for x1, y1, x2, y2 in rects:
                fluid_obstacles.append((
                    float(x1) - pad_x,
                    float(y1) - pad_y,
                    float(x2 - x1) + 2.0 * pad_x,
                    float(y2 - y1) + 2.0 * pad_y,
                ))

        return fluid_obstacles



    @classmethod
    def obstacles(
        cls,
        layer: str,
        board: Board,
        exclude: list,
        elevation: int = 0,
        pad_x: float = 0.0,
        pad_y: float = 0.0,
        fluid_pad_x: Optional[float] = None,
        fluid_pad_y: Optional[float] = None,
    ) -> list:
        """
        Transforms board weights, perimeters, and bridge-carved Fluid hazards
        for the specified elevation tier into flat C-primitive tuples,
        optionally inflated by Minkowski padding.
        """
        obstacles = []

        for asset in board.weights(layer, elevation=elevation):
            if asset.name in exclude:
                continue
            for hb in asset.hitbox.get(asset.properties, asset.state, elevation):
                obstacles.append((
                    float(asset.state.position.x + hb.position.x) - pad_x,
                    float(asset.state.position.y + hb.position.y) - pad_y,
                    float(hb.dimensions.w) + 2.0 * pad_x,
                    float(hb.dimensions.l) + 2.0 * pad_y,
                ))

        for bound in board.perimeters.get(layer, {}).get(elevation, []):
            obstacles.append((
                float(bound.position.x) - pad_x,
                float(bound.position.y) - pad_y,
                float(bound.dimensions.w) + 2.0 * pad_x,
                float(bound.dimensions.l) + 2.0 * pad_y,
            ))

        obstacles.extend(
            cls._fluid_obstacles(
                layer=layer,
                board=board,
                elevation=elevation,
                pad_x=pad_x if fluid_pad_x is None else fluid_pad_x,
                pad_y=pad_y if fluid_pad_y is None else fluid_pad_y,
            )
        )

        return obstacles


    @staticmethod
    def navigating(sprite: Asset) -> bool:
        """
        Verifies if the sprite is pursuing a goal under an active navigation intention.
        """
        if not sprite.state.goal:
            return False
        
        return sprite.state.intention in NavigationIntentions


    @staticmethod
    def _tracks(sprite: Asset) -> bool:
        """
        Determines whether navigation may resolve a Goal's live deployed Asset
        footprint. Static non-position Goals track directly; mobile Character
        Goals require active visual perception (B082).
        """
        goal = sprite.state.goal
        if not goal or not goal.name or goal.category == Goals.POSITION:
            return False

        if goal.category in (Goals.TARGET, Goals.SUBJECT):
            return sprite.state.mutators.triggers.vision

        return True


    @staticmethod
    def _goal(sprite: Asset) -> Optional[GoalSignature]:
        """Builds an identity tuple for detecting Goal substitutions within an Intention."""
        goal = sprite.state.goal
        if not goal:
            return None
        return (goal.name, goal.category, goal.layer)


    @staticmethod
    def _contains(
        x: float,
        y: float,
        obstacle: Tuple[float, float, float, float],
        eps: float = 1e-3
    ) -> bool:
        """Returns True if (x, y) lies inside or on the border of an obstacle AABB."""
        ox, oy, ow, ol = obstacle
        return (
            (ox - eps) <= x <= (ox + ow + eps)
            and (oy - eps) <= y <= (oy + ol + eps)
        )


    @classmethod
    def _project(
        cls,
        point: Position,
        obstacles: List[Tuple[float, float, float, float]],
        max_w: int = 0,
        max_l: int = 0,
        max_depth: int = 3
    ) -> Position:
        """
        Projects an anchor coordinate contained within Minkowski-inflated walls
        or perimeters (e.g., wall-embedded IN Doors, wall-adjacent Characters, or
        squeeze-zone spawns) to the nearest unobstructed integer coordinate inside
        Layer bounds. Returns point unchanged if already clear or unresolvable.
        """
        px = int(point.x)
        py = int(point.y)
        if not any(cls._contains(px, py, obs) for obs in obstacles):
            return point

        frontier: List[Tuple[int, int]] = [(px, py)]
        visited: Set[Tuple[int, int]] = {(px, py)}
        best_pos: Optional[Tuple[int, int]] = None
        best_dist_sq: Optional[int] = None

        for _ in range(max_depth):
            next_frontier: List[Tuple[int, int]] = []
            for cx, cy in frontier:
                containing = next(
                    (obs for obs in obstacles if cls._contains(cx, cy, obs)),
                    None
                )
                if containing is None:
                    continue

                ox, oy, ow, ol = containing
                candidates = (
                    (cx, math.floor(oy) - 1),
                    (cx, math.ceil(oy + ol) + 1),
                    (math.floor(ox) - 1, cy),
                    (math.ceil(ox + ow) + 1, cy),
                )
                for nx, ny in candidates:
                    if nx < 0 or ny < 0:
                        continue
                    if max_w > 0 and nx > max_w:
                        continue
                    if max_l > 0 and ny > max_l:
                        continue
                    if (nx, ny) in visited:
                        continue
                    visited.add((nx, ny))

                    if not any(cls._contains(nx, ny, obs) for obs in obstacles):
                        dx = nx - px
                        dy = ny - py
                        dist_sq = dx * dx + dy * dy
                        if best_dist_sq is None or dist_sq < best_dist_sq:
                            best_dist_sq = dist_sq
                            best_pos = (nx, ny)
                    else:
                        next_frontier.append((nx, ny))

            if best_pos is not None:
                return Position(x=best_pos[0], y=best_pos[1])
            if not next_frontier:
                break
            frontier = next_frontier

        return point


    def _clear(self, sprite: Asset) -> None:
        """
        Resets tactical trajectory buffers and stall cooldown when an entity
        ceases navigation or clears a prior Goal (B089).
        """
        sprite.state.trajectory.target = None
        sprite.state.trajectory.vertices.clear()
        sprite.state.trajectory.stalled = False
        sprite.state.trajectory.cooldown = 0


    def _target(self, sprite: Asset, board: Board) -> Optional[Position]:
        """
        Resolves the physical anchor coordinate of the sprite's goal.
        Bypasses board asset lookup for synthetic Goals.POSITION coordinates (B072)
        and unseen same-layer Characters so frozen last-known coordinates are respected (B082).
        """
        goal = sprite.state.goal
        if not goal:
            return None

        # Same-layer deployed asset: track physical footprint center when epistemically allowed
        if self._tracks(sprite):
            target_asset = board.asset(goal.name, sprite.state.layer) or \
                           board.asset(goal.name)
            if target_asset and target_asset.state.layer == sprite.state.layer:
                return self.anchor(target_asset)

        if goal.position is None:
            return None

        # Coordinate destination: apply sprite footprint displacement
        anchor = self.anchor(sprite)
        offset_x = anchor.x - sprite.state.position.x
        offset_y = anchor.y - sprite.state.position.y
        return Position(
            x=goal.position.x + offset_x,
            y=goal.position.y + offset_y,
        )


    def _plan(self, 
        sprite: Asset, 
        anchor: Position, 
        target: Position,
        obstacles: List[Tuple[float, float, float, float]],
        offset: Tuple[int, int]
    ) -> bool:
        """
        Executes RRT planning and populates trajectory waypoints or stall state.
        """
        planner = Planner(
            start=anchor,
            target=target,
            obstacles=obstacles,
            step_size=32.0,
            max_iter=300,
            heading=self.heading(sprite),
            inertia=0.75,
        )
        path = planner.plan()

        if path:
            # Subtract anchor offset to steer canvas origin cleanly
            sprite.state.trajectory.vertices = [
                Position(x=int(wp.x - offset[0]), y=int(wp.y - offset[1]))
                for wp in path
            ]
            sprite.state.trajectory.target = sprite.state.trajectory.vertices[0]
            sprite.state.trajectory.stalled = False
            sprite.state.trajectory.cooldown = 0
            return True

        # Stall Handling
        sprite.state.trajectory.stalled = True
        sprite.state.trajectory.target = None
        sprite.state.trajectory.vertices.clear()
        sprite.state.trajectory.cooldown = settings.PATH_RETRY_INTERVAL
        logger.info(f"Pathfinding stalled for {sprite.name}; no valid route found.")
        return False

        
    def _navigate(self, sprite: Asset, board: Board) -> None:
        """
        Tactical trajectory update frequency for an individual sprite.
        """
        # Dead sprites cease tactical pathfinding immediately (B085)
        if sprite.state.mutators.triggers.dead:
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        if sprite.state.mutators.triggers.falling:
            return
        
        # 1. Goal Verification
        if not self.navigating(sprite):
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        # Cross-layer destinations are managed via door subsumption in CognitionMechanics
        if sprite.state.goal.layer and (
            sprite.state.goal.layer != sprite.state.layer
        ):
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        # Clear stale stall/cooldown/waypoints whenever the active Goal changes
        # within the same NavigationIntention (e.g. SUBJECT -> DOOR in FIND)
        signature = self._goal(sprite)
        prev_signature = self._active_goals.get(sprite.name)
        if prev_signature is not None and prev_signature != signature:
            self._clear(sprite)
        if signature is not None:
            self._active_goals[sprite.name] = signature

        # 2. Anchor Computation
        anchor = self.anchor(sprite)
        offset_x = anchor.x - sprite.state.position.x
        offset_y = anchor.y - sprite.state.position.y
        target = self._target(sprite, board)
        if target is None:
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        tracks_live = self._tracks(sprite)
        exclude = [sprite.name]
        if tracks_live:
            exclude.append(sprite.state.goal.name)

        pad_x, pad_y = self.padding(sprite)
        obstacles = self.obstacles(
            sprite.state.layer,
            board,
            exclude=exclude,
            elevation=sprite.elevation,
            pad_x=pad_x,
            pad_y=pad_y,
        )

        # 3. Free-Space Endpoint Projection (wall-embedded IN Doors & squeeze zones)
        layer_sizes = board.size(sprite.state.layer)
        max_w = layer_sizes[0].w if layer_sizes else 0
        max_l = layer_sizes[0].l if layer_sizes else 0

        plan_start = self._project(anchor, obstacles, max_w, max_l)
        plan_target = (
            self._project(target, obstacles, max_w, max_l)
            if tracks_live
            else target
        )

        goal_x = int(plan_target.x - offset_x)
        goal_y = int(plan_target.y - offset_y)
        if (
            sprite.state.goal.position is not None
            and sprite.state.goal.position.x == goal_x
            and sprite.state.goal.position.y == goal_y
        ):
            goal_target = sprite.state.goal.position
        else:
            goal_target = Position(x=goal_x, y=goal_y)

        escape_target = (
            Position(
                x=int(plan_start.x - offset_x),
                y=int(plan_start.y - offset_y),
            )
            if plan_start is not anchor
            else None
        )

        planned = False

        # 4. Path Maintenance
        if geometry.los(
            float(plan_start.x),
            float(plan_start.y),
            float(plan_target.x),
            float(plan_target.y),
            obstacles,
        ):
            # Line of sight is clear from plan_start: step out of squeeze zone first if needed
            self._clear(sprite)
            sprite.state.trajectory.target = (
                escape_target if escape_target is not None else goal_target
            )

        else:
            # Line of sight is blocked
            if not sprite.state.trajectory.vertices:
                # No active path: evaluate cooldown before planning
                if sprite.state.trajectory.cooldown > 0:
                    sprite.state.trajectory.cooldown -= 1
                    return

                if not self._plan(
                    sprite,
                    plan_start,
                    plan_target,
                    obstacles,
                    offset=(offset_x, offset_y)
                ):
                    return

                if escape_target is not None:
                    sprite.state.trajectory.vertices.insert(0, escape_target)
                    sprite.state.trajectory.target = escape_target

                planned = True

                
            else:
                # Active waypoints exist: validate LOS to immediate waypoint
                if (
                    escape_target is None
                    or sprite.state.trajectory.target != escape_target
                ):
                    target_anchor_x = sprite.state.trajectory.target.x + offset_x
                    target_anchor_y = sprite.state.trajectory.target.y + offset_y

                    if not geometry.los(
                        float(plan_start.x),
                        float(plan_start.y),
                        float(target_anchor_x),
                        float(target_anchor_y),
                        obstacles,
                    ):
                        # Waypoint path is blocked by dynamic obstacle: replan
                        logger.info(f"Waypoint path occluded for {sprite.name}. Replanning.")
                        sprite.state.trajectory.vertices.clear()
                        sprite.state.trajectory.target = None

                        if not self._plan(
                            sprite,
                            plan_start,
                            plan_target,
                            obstacles,
                            offset=(offset_x, offset_y)
                        ):
                            return

                        if escape_target is not None:
                            sprite.state.trajectory.vertices.insert(0, escape_target)
                            sprite.state.trajectory.target = escape_target

                        planned = True

        # 5. Waypoint Arrival
        if not planned and \
            sprite.state.trajectory.target \
                and sprite.state.trajectory.vertices:
            arrival_radius = sprite.state.mutators.parameters.action.radius

            if geometry.nearby(
                int(sprite.state.position.x),
                int(sprite.state.position.y),
                int(sprite.state.trajectory.target.x),
                int(sprite.state.trajectory.target.y),
                arrival_radius,
            ):
                # Require clear LOS to the subsequent corner vertex before popping early
                if len(sprite.state.trajectory.vertices) > 1:
                    next_wp = sprite.state.trajectory.vertices[1]
                    if not geometry.los(
                        float(anchor.x),
                        float(anchor.y),
                        float(next_wp.x + offset_x),
                        float(next_wp.y + offset_y),
                        obstacles,
                    ):
                        return

                if sprite.state.trajectory.vertices and (
                    sprite.state.trajectory.target == sprite.state.trajectory.vertices[0]
                ):
                    sprite.state.trajectory.vertices.pop(0)
                
                if sprite.state.trajectory.vertices:
                    sprite.state.trajectory.target = sprite.state.trajectory.vertices[0]
                    return
                
                sprite.state.trajectory.target = goal_target
                return


    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Mechanic update loop iterating over all autonomous sprites.
        """
        player = board.player()
        for sprite in board.instances(AssetInstances.SPRITES):

            if player and sprite.name == player.name: 
                continue

            self._navigate(sprite, board)