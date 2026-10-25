"""
@domain.logic
@app.services
@workflow.collisions

# Ontology: Source - app.services.generators.game.perimeter

Dynamic perimeter generation partitioned by elevation.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    List, 
    Dict, 
    Optional,
    TYPE_CHECKING
)

# Application Libraries
from app.static.semantics import (
    AssetCategories, 
    AssetInstances
)

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import (
    Boundary,
    Dimensions,
    Position
)

logger = logging.getLogger(__name__)

class Perimeter:
    """
    Derives simply-connected outer hulls of an environment partitioned by layer and elevation.
    """

    @classmethod
    def extract(cls, board: Board, layer: str, elevation: Optional[int] = None) -> List[tuple[int, int, int, int]]:
        rects = []
        
        # 1. Map Tiles (Substrates belong to Tier 0)
        if elevation is None or elevation == 0:
            tiles = board.categories(AssetCategories.TILES.value, layer)
            for tile in tiles:
                if tile.taxonomy.instance not in (
                    AssetInstances.ENVIRON.value, 
                    AssetInstances.CANOPY.value
                ):
                    continue
                w = tile.properties.dimensions.w
                l = tile.properties.dimensions.l
                nx = tile.state.multiple.nx
                ny = tile.state.multiple.ny
                x1 = int(tile.state.position.x)
                y1 = int(tile.state.position.y)
                rects.append((x1, y1, x1 + (nx * w), y1 + (ny * l)))

        # 2. Map Elevated Substrates (Platform decks and Stair inclines at E > base elevation)
        if elevation is not None and elevation > 0:
            crafts = board.categories(AssetCategories.CRAFTS.value, layer)
            for craft in crafts:
                base_e = craft.state.elevation if craft.state.elevation is not None else 0
                if craft.taxonomy.instance == AssetInstances.PLATFORMS.value:
                    if elevation > base_e and elevation in craft.hitbox.elevations(craft.properties, craft.state):
                        x1 = int(craft.state.position.x)
                        y1 = int(craft.state.position.y)
                        rects.append((x1, y1, x1 + craft.dimensions.w, y1 + craft.dimensions.l))
                        
                elif craft.taxonomy.instance == AssetInstances.STAIRS.value:
                    if base_e + craft.state.delta == elevation:
                        x1 = int(craft.state.position.x)
                        y1 = int(craft.state.position.y)
                        hbs = craft.hitboxes
                        if hbs:
                            for hb in hbs:
                                hx1 = x1 + hb.position.x
                                hy1 = y1 + hb.position.y
                                rects.append((hx1, hy1, hx1 + hb.dimensions.w, hy1 + hb.dimensions.l))
                        else:
                            rects.append((x1, y1, x1 + craft.dimensions.w, y1 + craft.dimensions.l))

        # 3. Map Static Architecture
        objects = board.categories(AssetCategories.OBJECTS.value, layer)
        crafts = board.categories(AssetCategories.CRAFTS.value, layer)
        space = objects + crafts
        for obj in space:
            # Exclude movable bodies, dynamic crafts, and platforms from standard hulls
            mass = getattr(obj.properties, 'mass', 0)
            if mass > 0 or obj.taxonomy.instance in (
                AssetInstances.CRATES.value,
                AssetInstances.CHESTS.value,
                AssetInstances.RAFTS.value,
                AssetInstances.STAIRS.value,
                AssetInstances.BRIDGES.value,
                AssetInstances.PLATFORMS.value
            ):
                continue

            # Elevation Partitioning: collapse <= 0 to Tier 0
            if elevation is None or elevation == 0:
                if obj.elevation > 0:
                    continue
            else:
                if obj.elevation != elevation:
                    continue

            if not hasattr(obj, 'dimensions'):
                raise ValueError(f"{obj.id} - {obj.name}")
            
            x1 = int(obj.state.position.x)
            y1 = int(obj.state.position.y)
            rects.append((x1, y1, x1 + obj.dimensions.w, y1 + obj.dimensions.l))
            
        return rects

    @classmethod
    def generate(cls, board: Board, layer: str) -> Dict[int, List[Boundary]]:
        weights = board.weights(layer)
        # Collapse all non-positive elevations to Tier 0
        elevations = {
            max(0, e)
            for w in weights
            for e in w.hitbox.elevations(w.properties, w.state)
        } | {0}
        perimeters_by_tier: Dict[int, List[Boundary]] = {}

        for elevation in elevations:
            rects = cls.extract(board, layer, elevation=elevation)
            if not rects:
                continue
                
            raw_contours = geometry.contours(rects)
            perimeters_by_tier[elevation] = [
                Boundary(Position(x, y), Dimensions(w, l))
                for x, y, w, l, *_ in raw_contours
            ]
        return perimeters_by_tier