"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.locators

Locator implementations.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.game.logic.modules.cognition.base import (
    Locator,
    Operator
)
from app.static.semantics import (
    AssetInstances,
    Locators
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------

class DoorLocator(Locator):
    """
    Locates Doors (both LayerProjections.IN and LayerProjections.OUT) on the
    Sprite's current Layer. Prioritizes the shortest known route in
    memory.doors (minimizing hop count, then distance to the first-hop Door),
    falling back to the nearest unmapped Door within vision.radius.
    """

    @staticmethod
    def _distance_sq(p1: Position, p2: Position) -> int:
        """Computes squared Euclidean distance between two Positions."""
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return dx * dx + dy * dy

    @staticmethod
    def _route(
        current_layer: str,
        target_layer: str,
        doors: List[Asset],
        memory_doors: Dict[str, Dict[str, str]],
        sprite_pos: Position
    ) -> Optional[Asset]:
        """
        Runs breadth-first search over memory.doors to find the first-hop Door
        deployed on current_layer reaching target_layer, minimizing
        (hop_count, squared_distance).
        """
        local_edges = memory_doors.get(current_layer)
        if not local_edges:
            return None

        # Pre-sorting local doors by distance guarantees the first visited path
        # at any minimum hop depth is also closest to the Sprite.
        ordered_doors = sorted(
            doors,
            key=lambda d: DoorLocator._distance_sq(sprite_pos, d.state.position)
        )

        visited: Set[str] = {current_layer}
        frontier: collections.deque[Tuple[str, Asset]] = collections.deque()

        for portal in ordered_doors:
            next_layer = local_edges.get(portal.name)
            if not next_layer or next_layer in visited:
                continue
            if next_layer == target_layer:
                return portal
            visited.add(next_layer)
            frontier.append((next_layer, portal))

        while frontier:
            layer, first_door = frontier.popleft()
            edges = memory_doors.get(layer)
            if not edges:
                continue
            for next_layer in edges.values():
                if not next_layer or next_layer in visited:
                    continue
                if next_layer == target_layer:
                    return first_door
                visited.add(next_layer)
                frontier.append((next_layer, first_door))

        return None

    def locate(self, sprite: Asset, board: Board) -> Optional[Asset]:
        """
        Resolves the next Door on the Sprite's active Layer for pursuing a
        cross-layer Goal, or None if no mapped route or visible unmapped Door
        is available.
        """
        goal = sprite.state.goal
        current_layer = sprite.state.layer
        if (
            not goal
            or not goal.layer
            or current_layer is None
            or goal.layer == current_layer
        ):
            return None

        doors = board.instances(AssetInstances.DOORS, current_layer)
        if not doors:
            return None

        sprite_pos = sprite.state.position
        memory_doors = sprite.state.memory.doors

        # 1. Prioritize direct or multi-hop mapped Door reaching goal.layer
        mapped_door = self._route(
            current_layer=current_layer,
            target_layer=goal.layer,
            doors=doors,
            memory_doors=memory_doors,
            sprite_pos=sprite_pos
        )
        if mapped_door is not None:
            return mapped_door

        # 2. Fall back to nearest unmapped Door on current_layer within vision.radius
        local_edges = memory_doors.get(current_layer, {})
        vision_radius = sprite.state.mutators.parameters.vision.radius
        unmapped_candidates = [
            portal for portal in doors
            if portal.name not in local_edges
            and geometry.nearby(
                portal.state.position.x,
                portal.state.position.y,
                sprite_pos.x,
                sprite_pos.y,
                vision_radius
            )
        ]
        if unmapped_candidates:
            return min(
                unmapped_candidates,
                key=lambda d: self._distance_sq(sprite_pos, d.state.position)
            )

        return None


# -----------------------------------------------------


class LocatorOperator(Operator[Locators, Locator]):
    """
    Dispatches semantic Locator keys to registered Locator strategies
    operating over a Sprite and Board.
    """

    @classmethod
    def defaults(cls) -> Dict[Locators, Locator]:
        return {
            Locators.DOOR: DoorLocator(),
        }

    def resolve(
        self,
        key: Locators,
        sprite: Asset,
        board: Board
    ) -> Optional[Asset]:
        """
        Executes the Locator strategy registered for key and returns the
        located Asset, or None if no candidate is found.
        """
        return self.get(key).locate(sprite, board)