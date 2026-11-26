"""
@domain.concrete
@domain.logic
@app.mechanic
@physics.space
@workflow.interactions

# Ontology: Source - app.game.logic.mechanics.spatial.interaction

InteractionMechanics implementation.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import (
    Dict,
    List,
    Set,
    Tuple,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Intentions,
    Menus
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic
from app.models.menus import (
    MenuEvent,
    DialogueContext
)
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.geometry as geometry

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------


class InteractionMechanics(SpatialMechanic):
    """
    Resolves interactive Object transitions for Players (via hitbox
    intersections) and autonomous Sprites (via action-radius proximities and
    hitbox intersections, prioritizing sprite.state.goal.name).
    """

    def __init__(self):
        super().__init__(max_entities=2000)

    @staticmethod
    def _select_sprite_target(source: Asset, candidates: List[Asset]) -> Asset:
        """
        Prioritizes the candidate matching source.state.goal.name; otherwise
        selects the nearest candidate by squared Euclidean distance.
        """
        goal = source.state.goal
        if goal and goal.name:
            for candidate in candidates:
                if candidate.name == goal.name:
                    return candidate

        sx = source.state.position.x
        sy = source.state.position.y
        return min(
            candidates,
            key=lambda target: (
                (target.state.position.x - sx) ** 2
                + (target.state.position.y - sy) ** 2
            )
        )

    @staticmethod
    def _resolve_door(source: Asset, target: Asset, board: Board) -> None:
        """
        Transitions source across both LayerProjections.IN and
        LayerProjections.OUT Doors. For Sprites, records bidirectional
        memory.doors transitions (B080) and wakes dormant Goals matching the
        entered Layer.
        """
        from_layer = source.state.layer
        to_layer = target.state.outlayer

        if source.taxonomy.instance == AssetInstances.SPRITES:
            if from_layer is not None and to_layer is not None:
                source.state.memory.doors.setdefault(
                    from_layer, {}
                )[target.name] = to_layer

                # Record reciprocal OUT/return edge on to_layer if present (B080)
                reciprocal = board.asset(target.name, to_layer)
                if (
                    reciprocal is None
                    or reciprocal.taxonomy.instance != AssetInstances.DOORS
                    or reciprocal.state.outlayer != from_layer
                ):
                    reciprocal = next(
                        (
                            door
                            for door in board.instances(
                                AssetInstances.DOORS, to_layer
                            )
                            if door.state.outlayer == from_layer
                            and door.state.position.x == target.state.out.x
                            and door.state.position.y == target.state.out.y
                        ),
                        None
                    )

                if reciprocal is not None:
                    source.state.memory.doors.setdefault(
                        to_layer, {}
                    )[reciprocal.name] = from_layer

            # Wake dormant Goals residing on the newly entered Layer
            for mem_goal in source.state.memory.goals.values():
                if mem_goal.dormant and mem_goal.layer == to_layer:
                    mem_goal.dormant = False

        board.relayer(source, to_layer)
        source.state.position.x = target.state.out.x
        source.state.position.y = target.state.out.y

        if source.taxonomy.instance == AssetInstances.PLAYERS:
            source.state.intention = Intentions.IDLE

    def _interact(
        self,
        source: Asset,
        target: Asset,
        board: Board,
        bus: collections.deque,
        processed_sources: Set[str]
    ) -> None:
        """Dispatches interaction side effects between source and target."""
        if target.taxonomy.instance == AssetInstances.DOORS:
            self._resolve_door(source, target, board)
            processed_sources.add(source.name)

        elif target.taxonomy.instance == AssetInstances.CHESTS:
            if source.taxonomy.instance == AssetInstances.SPRITES:
                if target.state.content:
                    pass
                    # TODO: Inventory Management
                source.state.mutators.triggers.interacted = True
                processed_sources.add(source.name)

        elif target.taxonomy.instance == AssetInstances.SIGNS:
            if source.taxonomy.instance == AssetInstances.PLAYERS:
                bus.append(MenuEvent(
                    id=Menus.TEXT,
                    context=DialogueContext(
                        plot=board.plot,
                        object=target.state
                    )
                ))
                processed_sources.add(source.name)
            elif source.taxonomy.instance == AssetInstances.SPRITES:
                source.state.mutators.triggers.interacted = True
                processed_sources.add(source.name)

        elif target.taxonomy.instance == AssetInstances.REACTABLES:
            target.state.active = True
            if source.taxonomy.instance == AssetInstances.SPRITES:
                source.state.mutators.triggers.interacted = True
            processed_sources.add(source.name)

    def _resolve_players(
        self,
        sources: List[Asset],
        targets: List[Asset],
        board: Board,
        bus: collections.deque,
        processed_sources: Set[str]
    ) -> None:
        """Resolves Player interactions strictly via hitbox intersections."""
        source_ids = {id(asset) for asset in sources}
        target_ids = {id(asset) for asset in targets}
        colliding_pairs = self.intersections(sources + targets)

        for asset_a, asset_b in colliding_pairs:
            if id(asset_a) in source_ids and id(asset_b) in target_ids:
                source, target = asset_a, asset_b
            elif id(asset_b) in source_ids and id(asset_a) in target_ids:
                source, target = asset_b, asset_a
            else:
                continue

            if source.name in processed_sources:
                continue

            self._interact(source, target, board, bus, processed_sources)

    def _resolve_sprites(
        self,
        sources: List[Asset],
        targets: List[Asset],
        board: Board,
        bus: collections.deque,
        processed_sources: Set[str]
    ) -> None:
        """
        Resolves Sprite interactions within action.radius (matching find ->
        interact closed-ball distance semantics, B067) or direct hitbox contact,
        prioritizing sprite.state.goal.name.
        """
        source_ids = {id(asset) for asset in sources}
        target_ids = {id(asset) for asset in targets}

        proximity_pairs = self.proximities(sources + targets)
        intersection_pairs = self.intersections(sources + targets)

        candidates_by_source: Dict[str, List[Asset]] = collections.defaultdict(list)
        seen_pairs: Set[Tuple[int, int]] = set()

        for asset_a, asset_b in proximity_pairs:
            if id(asset_a) in source_ids and id(asset_b) in target_ids:
                source, target = asset_a, asset_b
            elif id(asset_b) in source_ids and id(asset_a) in target_ids:
                source, target = asset_b, asset_a
            else:
                continue

            pair_key = (id(source), id(target))
            if pair_key in seen_pairs:
                continue

            action_radius = source.state.mutators.parameters.action.radius
            if not geometry.nearby(
                source.state.position.x,
                source.state.position.y,
                target.state.position.x,
                target.state.position.y,
                action_radius
            ):
                continue

            seen_pairs.add(pair_key)
            candidates_by_source[source.name].append(target)

        for asset_a, asset_b in intersection_pairs:
            if id(asset_a) in source_ids and id(asset_b) in target_ids:
                source, target = asset_a, asset_b
            elif id(asset_b) in source_ids and id(asset_a) in target_ids:
                source, target = asset_b, asset_a
            else:
                continue

            pair_key = (id(source), id(target))
            if pair_key in seen_pairs:
                continue

            seen_pairs.add(pair_key)
            candidates_by_source[source.name].append(target)

        for source in sources:
            if source.name in processed_sources:
                continue

            candidates = candidates_by_source.get(source.name)
            if not candidates:
                continue

            target = self._select_sprite_target(source, candidates)
            self._interact(source, target, board, bus, processed_sources)

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """Evaluates Object interactions across all Board Layers."""
        processed_sources: Set[str] = set()

        for layer in board.layers():
            sprites = board.instances(AssetInstances.SPRITES, layer)
            players = board.instances(AssetInstances.PLAYERS, layer)

            # Clear interacted trigger whenever a Sprite leaves Intentions.INTERACT
            for sprite in sprites:
                if sprite.state.intention != Intentions.INTERACT:
                    sprite.state.mutators.triggers.interacted = False

            sprite_sources = [
                asset for asset in sprites
                if asset.state.intention == Intentions.INTERACT
                and asset.name not in processed_sources
            ]
            player_sources = [
                asset for asset in players
                if asset.state.intention == Intentions.INTERACT
                and asset.name not in processed_sources
            ]

            if not sprite_sources and not player_sources:
                continue

            doors = board.instances(AssetInstances.DOORS, layer)
            chests = board.instances(AssetInstances.CHESTS, layer)
            signs = board.instances(AssetInstances.SIGNS, layer)
            reactables = [
                effect for effect in board.instances(
                    AssetInstances.REACTABLES, layer
                )
                if effect.state.intention == Intentions.INTERACT
            ]
            targets = doors + chests + signs + reactables

            if not targets:
                continue

            if player_sources:
                self._resolve_players(
                    player_sources,
                    targets,
                    board,
                    bus,
                    processed_sources
                )

            if sprite_sources:
                self._resolve_sprites(
                    sprite_sources,
                    targets,
                    board,
                    bus,
                    processed_sources
                )