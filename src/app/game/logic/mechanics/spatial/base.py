"""
@domain.concrete
@domain.logic
@app.base
@app.mechanic
@physics.space
@workflow.collisions
@workflow.combat
@workflow.interactions

# Ontology: Source - app.game.logic.mechanics.spatial.base

SpatialMechanic implementation base class.
"""
# Standard Libraries
import collections
from typing import (
    Dict,
    List, 
    Set,
    Tuple,
    Optional
)
import logging

# Application Libraries
from app.static.semantics import AssetInstances
from app.assets.base import Asset
from app.game.logic.mechanics import Mechanic

# Cython Libraries
import libs.core.math.physics as physics
from libs.core.math.space import Space
from libs.core.models import (
    Position, 
    Dimensions, 
    Hitbox,
    Boundary
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------------------


class SpatialMechanic(Mechanic):
    """
    ## SpatialMechanic

    Base mechanic for systems requiring broad-phase spatial hashing and geometry resolution.
    """
    grid: Space

    @staticmethod
    def _elevations(asset: Asset, include_empty: bool = False) -> Set[int]:
        """
        Resolves normalized non-negative elevation tiers occupied by an asset.
        When include_empty is False, preserves sensor schemas (such as LayeredHitbox
        OUT projections) that report no solid collision elevations while still
        exposing active hitboxes, and excludes intentionally empty hitbox schemas.
        """
        tiers = {
            max(0, t)
            for t in asset.hitbox.elevations(asset.properties, asset.state)
        }
        if tiers:
            return tiers
        if include_empty or asset.hitboxes:
            return {max(0, asset.elevation)}
        return set()

    def __init__(self, cell_size: int = 64, max_entities: int = 2000):
        # Allocated exactly once in memory during orchestration
        super().__init__()
        self.grid = Space(cell_size=cell_size, max_entities=max_entities)

    def center(self, position: Position, dimensions: Dimensions):
        return (position.x + dimensions.w / 2, position.y + dimensions.l / 2)

    def collisions(self, assets: List[Asset], elevation: Optional[int] = None) -> List[Tuple[Asset, Asset]]:
        """
        Extracts primitives using standard physics hitboxes, queries the C-grid, 
        and returns colliding Asset pairs.
        """
        if len(assets) < 2:
            return []
        primitive_data = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else 
            asset.primitive(i)
            for i, asset in enumerate(assets)
        ]
        colliding_indices = physics.collisions(primitive_data, self.grid)
        return [(assets[id_a], assets[id_b]) for id_a, id_b in colliding_indices]

    def bipartite(
        self,
        dynamics: List[Asset],
        statics: List[Asset],
        elevation: Optional[int] = None
    ) -> List[Tuple[Asset, Asset]]:
        """
        Evaluates dynamic-vs-static candidate collisions without hashing or
        evaluating static-vs-static or dynamic-vs-dynamic pairs.
        """
        if not dynamics or not statics:
            return []
        dynamic_primitives = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else
            asset.primitive(i)
            for i, asset in enumerate(dynamics)
        ]
        static_primitives = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else
            asset.primitive(i)
            for i, asset in enumerate(statics)
        ]
        colliding_indices = physics.bipartite_collisions(
            dynamic_primitives,
            static_primitives,
            self.grid
        )
        return [(dynamics[id_a], statics[id_b]) for id_a, id_b in colliding_indices]

    def intersections(self, assets: List[Asset]) -> List[Tuple[Asset, Asset]]:
        """
        Evaluates spatial intersections across active asset hitboxes partitioned by
        shared elevation tiers, applying a 2px contact margin to motive entities so
        flush post-collision contact registers while preserving target HitboxSchema
        geometry (such as LayeredHitbox) and respecting intentionally empty hitboxes.
        """
        if len(assets) < 2:
            return []

        by_elevation: Dict[int, List[Asset]] = collections.defaultdict(list)
        for asset in assets:
            for tier in self._elevations(asset, include_empty=False):
                by_elevation[tier].append(asset)

        results: List[Tuple[Asset, Asset]] = []
        seen: Set[Tuple[int, int]] = set()

        for tier, tier_assets in by_elevation.items():
            if len(tier_assets) < 2:
                continue

            primitive_data = []
            for i, asset in enumerate(tier_assets):
                base_hbs = asset.hitbox.get(asset.properties, asset.state, tier)

                if asset.instance in (
                    AssetInstances.PLAYERS, 
                    AssetInstances.SPRITES
                ):
                    padded_hbs = [
                        Hitbox(
                            position=Position(x=hb.position.x - 2, y=hb.position.y - 2),
                            dimensions=Dimensions(w=hb.dimensions.w + 4, l=hb.dimensions.l + 4)
                        )
                        for hb in base_hbs
                    ]
                    primitive_data.append(asset.primitive(i, hitboxes=padded_hbs))
                else:
                    primitive_data.append(asset.primitive(i, hitboxes=base_hbs))

            colliding_indices = physics.collisions(primitive_data, self.grid)
            for id_a, id_b in colliding_indices:
                asset_a = tier_assets[id_a]
                asset_b = tier_assets[id_b]
                pair_key = (min(id(asset_a), id(asset_b)), max(id(asset_a), id(asset_b)))
                if pair_key not in seen:
                    seen.add(pair_key)
                    results.append((asset_a, asset_b))

        return results

    def proximities(self, assets: List[Asset]) -> List[Tuple[Asset, Asset]]:
        """
        Bypasses physics hitboxes, constructing a virtual hitbox padded by 
        the entity's action radius. This determines interaction reach,
        filtered to candidate pairs sharing an elevation tier.
        """
        if len(assets) < 2:
            return []

        primitive_data = []
        for i, asset in enumerate(assets):
            # Extract action radius safely, defaulting to 0 when parameters are absent
            # so static targets remain indexed 1:1 with assets for physics.collisions
            params = asset.state.mutators.parameters
            radius = (
                params.action.radius
                if params is not None and params.action is not None
                else 0
            )

            # Pad the dimensions by the radius in all directions
            pad_hb = Hitbox(
                position=Position(x=-radius, y=-radius), 
                dimensions=Dimensions(
                    w=asset.dimensions.w + (radius * 2), 
                    l=asset.dimensions.l + (radius * 2)
                )
            )
            primitive_data.append(asset.primitive(i, hitboxes=[pad_hb]))

        colliding_indices = physics.collisions(primitive_data, self.grid)
        results: List[Tuple[Asset, Asset]] = []
        for id_a, id_b in colliding_indices:
            asset_a = assets[id_a]
            asset_b = assets[id_b]
            if (
                self._elevations(asset_a, include_empty=True)
                & self._elevations(asset_b, include_empty=True)
            ):
                results.append((asset_a, asset_b))

        return results

    def constrain(
        self, 
        assets: List[Asset], 
        boundaries: List[Boundary], 
        elevation: Optional[int] = None
    ) -> List[Tuple[Asset, Boundary]]:        
        """
        Extracts primitives, queries the C-grid for Negative IDs (Boundaries), 
        and returns colliding constraint pairs.
        """
        if not assets or not boundaries:
            return []
        primitive_assets = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else 
            asset.primitive(i)
            for i, asset in enumerate(assets)
        ]
        primitive_bounds = [
            (i, b.position.x, b.position.y, b.dimensions.w, b.dimensions.l)
            for i, b in enumerate(boundaries)
        ]
        colliding_indices = physics.bipartite(primitive_assets, primitive_bounds, self.grid)
        return [(assets[id_a], boundaries[id_b]) for id_a, id_b in colliding_indices]