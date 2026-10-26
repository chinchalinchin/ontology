"""
@domain.concrete
@domain.logic
@app.base
@app.mechanics
@physics.space
@workflow.collisions
@workflow.interactions
# Ontology: Source - app.game.logic.mechanics.spatial.base

SpatialMechanic implementation base class.
"""
# Standard Libraries
from typing import (
    List, 
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

    def __init__(self, cell_size: int = 64, max_entities: int = 2000):
        # Allocated exactly once in memory during orchestration
        self.grid = Space(cell_size=cell_size, max_entities=max_entities)


    def center(self, position: Position, dimensions: Dimensions):
        return (position.x + dimensions.w / 2, position.y + dimensions.l / 2)

    
    def collisions(self, assets: List[Asset], elevation: Optional[int] = None) -> List[Tuple]:
        """
        Extracts primitives using standard physics hitboxes, queries the C-grid, 
        and returns colliding Asset pairs.
        """
        self.grid.clear()
        if not assets:
            return []
        asset_map = dict(enumerate(assets))
        primitive_data = [
            asset.primitive(
                i, 
                hitboxes=asset.hitbox.get(asset.properties, asset.state, elevation, asset.frame)
            ) if elevation is not None else asset.primitive(i)
            for i, asset in enumerate(assets)
        ]
        colliding_indices = physics.collisions(primitive_data, self.grid)
        return [(asset_map[id_a], asset_map[id_b]) for id_a, id_b in colliding_indices]

        
    def intersections(self, assets: List[Asset]) -> List[Tuple]:
        """
        Evaluates spatial intersections across active asset hitboxes, applying a 2px
        contact margin to motive entities so flush post-collision contact registers
        while preserving target HitboxSchema geometry (such as LayeredHitbox).
        """
        self.grid.clear()
        if not assets:
            return []

        asset_map = dict(enumerate(assets))
        primitive_data = []

        for i, asset in enumerate(assets):
            base_hbs = asset.hitboxes
            if not base_hbs and asset.dimensions:
                base_hbs = [Hitbox(position=Position(x=0, y=0), dimensions=asset.dimensions)]

            if asset.instance in (AssetInstances.PLAYERS.value, AssetInstances.SPRITES.value):
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
        return [(asset_map[id_a], asset_map[id_b]) for id_a, id_b in colliding_indices]


    def proximities(self, assets: List[Asset]) -> List[Tuple[Asset]]:
        """
        Bypasses physics hitboxes, constructing a virtual hitbox padded by 
        the entity's action radius. This determines interaction reach.
        """
        self.grid.clear()
        if not assets:
            return []

        asset_map = dict(enumerate(assets))
        primitive_data = []

        for i, asset in enumerate(assets):
            # Extract action radius safely, defaulting to 15 (1/2 grid cell)
            
            if not getattr(asset.state, 'mutators', None) or \
                not asset.state.mutators.parameters:
                continue

            radius = asset.state.mutators.parameters.action.radius

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
        return [(asset_map[id_a], asset_map[id_b]) for id_a, id_b in colliding_indices]


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
        self.grid.clear()
        if not assets or not boundaries:
            return []
        asset_map = dict(enumerate(assets))
        bound_map = dict(enumerate(boundaries))
        primitive_assets = [
            asset.primitive(
                i, 
                hitboxes=asset.hitbox.get(asset.properties, asset.state, elevation, asset.frame)
            ) if elevation is not None else asset.primitive(i)
            for i, asset in enumerate(assets)
        ]
        primitive_bounds = [
            (i, b.position.x, b.position.y, b.dimensions.w, b.dimensions.l)
            for i, b in enumerate(boundaries)
        ]
        colliding_indices = physics.boundaries(primitive_assets, primitive_bounds, self.grid)
        return [(asset_map[id_a], bound_map[id_b]) for id_a, id_b in colliding_indices]