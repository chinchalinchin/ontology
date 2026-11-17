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
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Tuple,
)
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    NavigationIntentions,
)
import app.static.settings as settings
from app.game.logic.mechanics import Mechanic
from app.game.logic.modules.paths.plan import Planner
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------

class NavigationMechanics(Mechanic):
    """
    ## NavigationMechanics

    Tactical navigation system executing between TransitionMechanics and MotionMechanics.
    Manages sensory anchors, line-of-sight validation, RRT path generation, dynamic
    waypoint progression, and impassable geometry stall handling.
    """

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
    def padding(asset: Asset) -> Tuple[float, float]:
        """
        Calculates the Minkowski inflation half-extents (hitbox half-dimensions + squeeze radius)
        for a navigating asset.
        """
        hbs = asset.hitboxes
        if hbs:
            half_w = hbs[0].dimensions.w / 2.0
            half_l = hbs[0].dimensions.l / 2.0
        else:
            half_w = asset.dimensions.w / 2.0
            half_l = asset.dimensions.l / 2.0

        squeeze = 0.0
        if (
            asset.state.mutators
            and asset.state.mutators.parameters
            and asset.state.mutators.parameters.squeeze
        ):
            squeeze = float(asset.state.mutators.parameters.squeeze.radius)

        return (half_w + squeeze, half_l + squeeze)


    @staticmethod
    def obstacles(
        layer: str,
        board: Board,
        exclude: list,
        elevation: int = 0,
        pad_x: float = 0.0,
        pad_y: float = 0.0,
    ) -> list:
        """
        Transforms board weights and perimeters for the specified elevation tier
        into flat C-primitive tuples, optionally inflated by Minkowski padding.
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

        return obstacles


    @staticmethod
    def navigating(sprite: Asset) -> bool:
        """
        Verifies if the sprite is pursuing a goal under an active navigation intention.
        """
        if not sprite.state.goal:
            return False
        
        return sprite.state.intention in NavigationIntentions


    def _clear(self, sprite: Asset) -> None:
        """
        Resets tactical trajectory buffers when an entity ceases navigation.
        """
        sprite.state.trajectory.target = None
        sprite.state.trajectory.vertices.clear()
        sprite.state.trajectory.stalled = False


    def _target(self, sprite: Asset, board: Board) -> Optional[Position]:
        """
        Resolves the physical anchor coordinate of the sprite's goal.
        """
        goal = sprite.state.goal
        if not goal:
            return None

        # Same-layer deployed asset: track physical footprint center
        if goal.name:
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
        obstacles: List[Tuple[int, int, int, int]],
        offset: Tuple[int, int]
    ) -> bool:
        """
        """
        planner = Planner(
            start=anchor,
            target=target,
            obstacles=obstacles,
            step_size=32.0,
            max_iter=300,
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
        if sprite.state.mutators.triggers.falling:
            return
        
        # 1. Goal Verification
        if not self.navigating(sprite):
            self._clear(sprite)
            return

        # Cross-layer destinations are managed via door subsumption in CognitionMechanics
        if sprite.state.goal.layer and (
            sprite.state.goal.layer != sprite.state.layer
        ):
            self._clear(sprite)
            return

        # 2. Anchor Computation
        anchor = self.anchor(sprite)
        offset_x = anchor.x - sprite.state.position.x
        offset_y = anchor.y - sprite.state.position.y
        target = self._target(sprite, board)
        if target is None:
            self._clear(sprite)
            return

        goal_x = int(target.x - offset_x)
        goal_y = int(target.y - offset_y)
        if (
            sprite.state.goal.position is not None
            and sprite.state.goal.position.x == goal_x
            and sprite.state.goal.position.y == goal_y
        ):
            goal_target = sprite.state.goal.position
        else:
            goal_target = Position(x=goal_x, y=goal_y)

        exclude = [ sprite.name ]
        if sprite.state.goal.name:
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

        planned = False

        # 4. Path Maintenance
        if geometry.los(
            float(anchor.x),
            float(anchor.y),
            float(target.x),
            float(target.y),
            obstacles,
        ):
            # Line of sight is clear: direct tracking to strategic goal
            self._clear(sprite)
            sprite.state.trajectory.target = goal_target
            sprite.state.trajectory.cooldown = 0

        else:
            # Line of sight is blocked
            if not sprite.state.trajectory.vertices:
                # No active path: evaluate cooldown before planning
                if sprite.state.trajectory.cooldown > 0:
                    sprite.state.trajectory.cooldown -= 1
                    return

                if not self._plan(
                    sprite,
                    anchor,
                    target,
                    obstacles,
                    offset=(offset_x, offset_y)
                ): return

                planned = True

                
            else:
                # Active waypoints exist: validate LOS to immediate waypoint
                target_anchor_x = sprite.state.trajectory.target.x + offset_x
                target_anchor_y = sprite.state.trajectory.target.y + offset_y

                if not geometry.los(
                    float(anchor.x),
                    float(anchor.y),
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
                        anchor,
                        target,
                        obstacles,
                        offset = (offset_x, offset_y)
                    ): return 

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