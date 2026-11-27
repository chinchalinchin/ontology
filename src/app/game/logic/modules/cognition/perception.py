"""
@domain.automata
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.perception

Epistemic sensory perception, fear evaluation, and active Goal tracking.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import (
    Dict,
    FrozenSet,
    Optional,
    Set,
    Tuple,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Goals,
    Relationships
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------


class Perception:
    """
    Epistemic sensory module for autonomous Sprites.
    Handles same-layer scanning, fear trigger evaluation, and active Goal
    tracking without cross-layer telepathy or inline Door subsumption.
    """
    _last_layer: Dict[str, Optional[str]]
    _known_doors: Dict[str, Set[Tuple[str, str, str]]]
    _seen_unmapped_doors: Dict[str, Set[str]]
    _stalled_doors: Dict[str, Dict[str, Set[str]]]
    _stalled_static: Dict[str, Dict[str, Dict[str, int]]]

    def __init__(self):
        self._last_layer = {}
        self._known_doors = {}
        self._seen_unmapped_doors = {}
        self._stalled_doors = {}
        self._stalled_static = {}

    def mark_stalled_door(
        self,
        sprite_name: str,
        layer: Optional[str],
        door_name: str
    ) -> None:
        """
        Records a Door on the given Layer that caused a navigation stall so
        re-sighting it does not re-trigger an infinite unwind/wake loop (B081)
        and DoorLocator can exclude it in favor of alternate Doors (B087).
        """
        if layer is None or not door_name:
            return
        self._stalled_doors.setdefault(sprite_name, {}).setdefault(
            layer, set()
        ).add(door_name)

    def stalled_doors(
        self,
        sprite_name: str,
        layer: Optional[str]
    ) -> FrozenSet[str]:
        """
        Returns Door names on layer previously marked as stalled for
        sprite_name so DoorLocator can fall back to alternate routes (B087).
        """
        if layer is None:
            return frozenset()
        return frozenset(
            self._stalled_doors.get(sprite_name, {}).get(layer, ())
        )

    def mark_stalled_static(
        self,
        sprite_name: str,
        layer: Optional[str],
        goal_name: str,
        cooldown: int = settings.PATH_RETRY_INTERVAL
    ) -> None:
        """
        Records a backoff cooldown for a stalled same-layer static Goal
        (OBJECT, RESOURCE, PROPERTY) so Perception.scan can re-wake it once
        obstructions may have cleared without per-tick oscillation (B088).
        """
        if layer is None or not goal_name:
            return
        self._stalled_static.setdefault(sprite_name, {}).setdefault(
            layer, {}
        )[goal_name] = max(1, cooldown)

    @staticmethod
    def _contact_origin(source: Asset, target: Asset) -> Position:
        """
        Computes the nearest Sprite origin (x, y) at which source's hitbox
        footprint touches target's hitbox footprint. Distance from
        source.state.position to the returned Position equals the exact
        Euclidean hitbox gap, matching InteractionMechanics._hitbox_distance_sq (B084).
        """
        sx = source.state.position.x
        sy = source.state.position.y
        tx = target.state.position.x
        ty = target.state.position.y

        src_hbs = source.hitboxes
        tgt_hbs = target.hitboxes

        src_boxes = (
            [
                (hb.position.x, hb.position.y, hb.dimensions.w, hb.dimensions.l)
                for hb in src_hbs
            ]
            if src_hbs
            else [(0, 0, source.dimensions.w, source.dimensions.l)]
        )
        tgt_boxes = (
            [
                (
                    tx + hb.position.x,
                    ty + hb.position.y,
                    tx + hb.position.x + hb.dimensions.w,
                    ty + hb.position.y + hb.dimensions.l,
                )
                for hb in tgt_hbs
            ]
            if tgt_hbs
            else [(tx, ty, tx + target.dimensions.w, ty + target.dimensions.l)]
        )

        best_x = sx
        best_y = sy
        best_dist_sq: Optional[int] = None

        for hx, hy, hw, hl in src_boxes:
            for rx1, ry1, rx2, ry2 in tgt_boxes:
                gx = max(rx1 - (hx + hw), min(sx, rx2 - hx))
                gy = max(ry1 - (hy + hl), min(sy, ry2 - hy))
                dx = gx - sx
                dy = gy - sy
                dist_sq = dx * dx + dy * dy
                if dist_sq == 0:
                    return Position(x=gx, y=gy)
                if best_dist_sq is None or dist_sq < best_dist_sq:
                    best_dist_sq = dist_sq
                    best_x = gx
                    best_y = gy

        return Position(x=best_x, y=best_y)

    @staticmethod
    def _door_edges(
        memory_doors: Dict[str, Dict[str, str]]
    ) -> Set[Tuple[str, str, str]]:
        """Flattens bidirectional memory.doors mappings into comparable edge tuples."""
        edges: Set[Tuple[str, str, str]] = set()
        for src_layer, mapping in memory_doors.items():
            for door_name, dst_layer in mapping.items():
                edges.add((src_layer, door_name, dst_layer))
        return edges

    @staticmethod
    def _reachable_layers(
        origin_layer: str,
        memory_doors: Dict[str, Dict[str, str]]
    ) -> Set[str]:
        """Computes all destination Layers reachable from origin_layer via memory.doors."""
        visited: Set[str] = {origin_layer}
        frontier: collections.deque[str] = collections.deque([origin_layer])

        while frontier:
            layer = frontier.popleft()
            edges = memory_doors.get(layer)
            if not edges:
                continue
            for next_layer in edges.values():
                if next_layer and next_layer not in visited:
                    visited.add(next_layer)
                    frontier.append(next_layer)

        visited.discard(origin_layer)
        return visited

    def _wake_cross_layer(self, sprite: Asset, board: Board) -> None:
        """
        Wakes cross-layer dormant Goals strictly on:
          1. Sprite Layer transition,
          2. Newly learned memory.doors edges reaching the Goal's Layer, or
          3. Newly sighted non-stalled unmapped Doors within vision.radius (B081).
        """
        name = sprite.name
        state = sprite.state
        current_layer = state.layer
        memory = state.memory

        # 1. Detect Layer transition
        prev_layer = self._last_layer.get(name)
        layer_changed = prev_layer is not None and prev_layer != current_layer
        self._last_layer[name] = current_layer

        if layer_changed:
            self._seen_unmapped_doors[name] = set()
            self._stalled_doors.pop(name, None)
            self._stalled_static.pop(name, None)

        # 2. Detect newly added memory.doors edges
        current_edges = self._door_edges(memory.doors)
        prev_edges = self._known_doors.get(name)
        new_edges: Set[Tuple[str, str, str]] = (
            current_edges - prev_edges if prev_edges is not None else set()
        )
        self._known_doors[name] = current_edges

        # 3. Detect newly sighted, non-stalled unmapped Doors on current_layer
        sprite_pos = state.position
        vision_radius = state.mutators.parameters.vision.radius
        local_mapped = (
            memory.doors.get(current_layer, {})
            if current_layer is not None
            else {}
        )
        stalled_on_layer = (
            self._stalled_doors.get(name, {}).get(current_layer, set())
            if current_layer is not None
            else set()
        )

        current_unmapped_visible: Set[str] = set()
        if current_layer is not None:
            for portal in board.instances(AssetInstances.DOORS, current_layer):
                if portal.name in local_mapped:
                    continue
                if geometry.nearby(
                    portal.state.position.x,
                    portal.state.position.y,
                    sprite_pos.x,
                    sprite_pos.y,
                    vision_radius
                ):
                    current_unmapped_visible.add(portal.name)

        prev_seen = self._seen_unmapped_doors.get(name, set())
        newly_sighted_unmapped = (
            current_unmapped_visible - prev_seen - stalled_on_layer
        )
        self._seen_unmapped_doors[name] = current_unmapped_visible

        if not (layer_changed or new_edges or newly_sighted_unmapped):
            return

        new_targets = {dst for _, _, dst in new_edges}
        reachable_layers = (
            self._reachable_layers(current_layer, memory.doors)
            if new_edges and current_layer is not None
            else set()
        )

        for mem_goal in memory.goals.values():
            if not mem_goal.dormant:
                continue

            if layer_changed and mem_goal.layer == current_layer:
                mem_goal.dormant = False
                continue

            if not mem_goal.layer or mem_goal.layer == current_layer:
                continue

            if (
                layer_changed
                or mem_goal.layer in new_targets
                or mem_goal.layer in reachable_layers
                or bool(newly_sighted_unmapped)
            ):
                mem_goal.dormant = False

    def _scan_static_goals(self, sprite: Asset, board: Board) -> None:
        """
        Maintains same-layer static Goals (OBJECT, RESOURCE, PROPERTY) in
        memory.goals: decrements stall backoffs, evicts observed missing or
        completed entries, and wakes visible dormant entries once their stall
        backoff has expired (B088).
        """
        state = sprite.state
        current_layer = state.layer
        if current_layer is None:
            return

        sprite_pos = state.position
        vision_radius = state.mutators.parameters.vision.radius
        memory = state.memory

        # Advance per-layer static stall cooldowns
        layer_cooldowns = self._stalled_static.get(sprite.name, {}).get(
            current_layer
        )
        if layer_cooldowns:
            for goal_key in list(layer_cooldowns.keys()):
                layer_cooldowns[goal_key] -= 1
                if layer_cooldowns[goal_key] <= 0:
                    del layer_cooldowns[goal_key]

        for key, mem_goal in list(memory.goals.items()):
            if mem_goal.layer != current_layer:
                continue
            if mem_goal.category not in (
                Goals.OBJECT,
                Goals.RESOURCE,
                Goals.PROPERTY,
            ):
                continue

            if mem_goal.category == Goals.PROPERTY:
                if key in memory.property:
                    memory.goals.pop(key, None)
                    continue
                if not mem_goal.dormant:
                    continue
                if layer_cooldowns and key in layer_cooldowns:
                    continue
                if geometry.nearby(
                    mem_goal.position.x,
                    mem_goal.position.y,
                    sprite_pos.x,
                    sprite_pos.y,
                    vision_radius
                ):
                    mem_goal.dormant = False
                continue

            # OBJECT / RESOURCE: evict if observed missing, else wake when visible off cooldown
            target_asset = board.asset(key, current_layer)
            if target_asset is None:
                if geometry.nearby(
                    mem_goal.position.x,
                    mem_goal.position.y,
                    sprite_pos.x,
                    sprite_pos.y,
                    vision_radius
                ):
                    memory.goals.pop(key, None)
                continue

            if not mem_goal.dormant:
                continue
            if layer_cooldowns and key in layer_cooldowns:
                continue

            contact = self._contact_origin(sprite, target_asset)
            if geometry.nearby(
                contact.x,
                contact.y,
                sprite_pos.x,
                sprite_pos.y,
                vision_radius
            ):
                mem_goal.position.x = contact.x
                mem_goal.position.y = contact.y
                mem_goal.dormant = False

    def scan(self, sprite: Asset, board: Board) -> None:
        """
        Refreshes copied Position snapshots in memory.sprites (B074), wakes
        visible same-layer character Goals (B019, B059), evicts observed dead
        TARGET/SUBJECT goals (B086), maintains static memory goals (B088), and
        evaluates cross-layer dormancy wake triggers (B081).
        """
        state = sprite.state
        if state.mutators.parameters is None:
            return

        current_layer = state.layer
        sprite_pos = state.position
        vision_radius = state.mutators.parameters.vision.radius
        memory = state.memory

        for other_name, other_state in board.characters().items():
            if other_name == sprite.name:
                continue

            # Strict Layer isolation: cannot perceive across Layers
            if other_state.layer != current_layer:
                continue

            if not geometry.nearby(
                other_state.position.x,
                other_state.position.y,
                sprite_pos.x,
                sprite_pos.y,
                vision_radius
            ):
                continue

            # Store copied Position snapshot to prevent live-reference aliasing (B074)
            memory.sprites[other_name] = Position(
                x=other_state.position.x,
                y=other_state.position.y
            )

            mem_goal = memory.goals.get(other_name)
            if mem_goal is None:
                continue

            if other_state.mutators.triggers.dead:
                if mem_goal.category in (Goals.TARGET, Goals.SUBJECT):
                    memory.goals.pop(other_name, None)
                continue

            mem_goal.position.x = other_state.position.x
            mem_goal.position.y = other_state.position.y
            mem_goal.layer = other_state.layer
            mem_goal.dormant = False

        self._wake_cross_layer(sprite, board)
        self._scan_static_goals(sprite, board)

    def fear(self, sprite: Asset, board: Board) -> bool:
        """
        Evaluates triggers.frightened from fear parameters:
          - health.current / health.maximum < fear.limit, OR
          - living same-layer FOE count within fear.radius >= fear.enemy.
        """
        state = sprite.state
        if state.mutators.triggers.dead:
            state.mutators.triggers.frightened = False
            return False

        parameters = state.mutators.parameters
        if parameters is None or parameters.fear is None:
            state.mutators.triggers.frightened = False
            return False

        fear_params = parameters.fear
        health = state.meters.health
        low_health = (
            health.maximum > 0
            and (health.current / health.maximum) < fear_params.limit
        )

        outnumbered = False
        if not low_health and fear_params.enemy > 0:
            hostile_count = 0
            sprite_pos = state.position
            sprite_layer = state.layer
            relationships = state.memory.relationships

            for other_name, other_state in board.characters().items():
                if other_name == sprite.name:
                    continue
                if other_state.layer != sprite_layer:
                    continue
                if other_state.mutators.triggers.dead:
                    continue
                if relationships.get(other_name) != Relationships.FOE:
                    continue
                if geometry.nearby(
                    other_state.position.x,
                    other_state.position.y,
                    sprite_pos.x,
                    sprite_pos.y,
                    fear_params.radius
                ):
                    hostile_count += 1
                    if hostile_count >= fear_params.enemy:
                        outnumbered = True
                        break

        frightened = low_health or outnumbered
        state.mutators.triggers.frightened = frightened
        return frightened

    def _observed_door_transit(
        self,
        sprite: Asset,
        board: Board,
        target_layer: str
    ) -> Optional[Asset]:
        """
        Determines whether the Sprite directly witnessed its tracked Character
        exit through a visible Door on the current Layer into target_layer.
        """
        state = sprite.state
        goal = state.goal
        current_layer = state.layer
        if (
            not goal
            or current_layer is None
            or goal.layer != current_layer
            or not state.mutators.triggers.vision
        ):
            return None

        last_pos = goal.position or state.memory.sprites.get(goal.name)
        if last_pos is None:
            return None

        vision_radius = state.mutators.parameters.vision.radius
        action_radius = state.mutators.parameters.action.radius
        sprite_pos = state.position

        best_door: Optional[Asset] = None
        best_dist_sq: Optional[int] = None

        for door in board.instances(AssetInstances.DOORS, current_layer):
            if door.state.outlayer != target_layer:
                continue

            if not geometry.nearby(
                door.state.position.x,
                door.state.position.y,
                sprite_pos.x,
                sprite_pos.y,
                vision_radius
            ):
                continue

            transit_radius = max(
                action_radius,
                door.dimensions.w,
                door.dimensions.l
            )
            if not geometry.nearby(
                last_pos.x,
                last_pos.y,
                door.state.position.x,
                door.state.position.y,
                transit_radius
            ):
                continue

            dx = door.state.position.x - last_pos.x
            dy = door.state.position.y - last_pos.y
            dist_sq = dx * dx + dy * dy
            if best_dist_sq is None or dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_door = door

        return best_door

    def track(self, sprite: Asset, board: Board) -> None:
        """
        Updates active Goal visibility and coordinates. Restricts goal.layer
        updates strictly to same-layer sightings or observed Door transits
        (using destination-layer exit coordinates, B083), aligns static Goal
        contact origins to hitbox bounds (B084), and rejects dead Characters (B086).
        """
        state = sprite.state
        goal = state.goal
        if not goal:
            state.mutators.triggers.vision = False
            return

        if state.mutators.parameters is None:
            return

        vision_radius = state.mutators.parameters.vision.radius
        current_layer = state.layer

        if goal.category in (Goals.TARGET, Goals.SUBJECT):
            target_state = board.character(goal.name) if goal.name else None
            if target_state is None or target_state.mutators.triggers.dead:
                state.mutators.triggers.vision = False
                return

            if target_state.layer == current_layer:
                if geometry.nearby(
                    target_state.position.x,
                    target_state.position.y,
                    state.position.x,
                    state.position.y,
                    vision_radius
                ):
                    state.mutators.triggers.vision = True
                    goal.position.x = target_state.position.x
                    goal.position.y = target_state.position.y
                    goal.layer = target_state.layer
                else:
                    # Target out of sight on same Layer: freeze last-known coordinates
                    state.mutators.triggers.vision = False
                return

            # Target is on another Layer: update goal.layer only on observed Door transit
            observed_door = self._observed_door_transit(
                sprite=sprite,
                board=board,
                target_layer=target_state.layer
            )
            if observed_door is not None:
                goal.layer = observed_door.state.outlayer
                # Record destination-layer exit coordinates and learn the observed Door edge (B083)
                goal.position.x = observed_door.state.out.x
                goal.position.y = observed_door.state.out.y
                if (
                    current_layer is not None
                    and observed_door.state.outlayer is not None
                ):
                    state.memory.doors.setdefault(
                        current_layer, {}
                    )[observed_door.name] = observed_door.state.outlayer
                logger.info(
                    f"{sprite.name} observed {goal.name} transit Door("
                    f"{observed_door.name}) -> layer '{goal.layer}'"
                )

            state.mutators.triggers.vision = False
            return

        # Cross-layer static/spatial Goal: cannot perceive across Layers
        if goal.layer and goal.layer != current_layer:
            state.mutators.triggers.vision = False
            return

        if goal.category in (Goals.POSITION, Goals.PROPERTY):
            state.mutators.triggers.vision = True
            return

        if goal.category in (Goals.DOOR, Goals.OBJECT, Goals.RESOURCE):
            target_asset = (
                board.asset(goal.name, current_layer)
                if goal.name and current_layer is not None
                else None
            )
            if target_asset is None:
                state.mutators.triggers.vision = False
                return

            # Align Goal coordinate to nearest hitbox-contact Sprite origin (B084)
            contact = self._contact_origin(sprite, target_asset)
            goal.position.x = contact.x
            goal.position.y = contact.y
            state.mutators.triggers.vision = geometry.nearby(
                contact.x,
                contact.y,
                state.position.x,
                state.position.y,
                vision_radius
            )
            return

        state.mutators.triggers.vision = False