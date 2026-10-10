"""
# Ontology: app.services.generators.game.perimeter

Package for dynamic environment boundary generation partitioned by elevation tier.
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
from app.config.enums import (
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
    Derives simply-connected outer hulls of an environment partitioned by layer and elevation tier.
    """
    def extract(self, board: Board, layer: str, elevation: Optional[int] = None) -> List[tuple[int, int, int, int]]:
        """
        Translates physical footprints for a specific elevation tier into raw mathematical primitives.
        """
        rects = []
        
        # 1. Map Tiles (Substrate floors bound to base elevation 0)
        if elevation is None or elevation == 0:
            tiles = board.categories(AssetCategories.TILES.value, layer)
            for tile in tiles:
                if tile.taxonomy.instance not in (AssetInstances.BACK.value, AssetInstances.FORE.value):
                    continue
                    
                w = tile.properties.dimensions.w
                l = tile.properties.dimensions.l
                nx = tile.state.multiple.nx
                ny = tile.state.multiple.ny
                
                x1 = int(tile.state.position.x)
                y1 = int(tile.state.position.y)
                rects.append((x1, y1, x1 + (nx * w), y1 + (ny * l)))
            
        # 2. Map Game Space matching elevation tier
        objects = board.categories(AssetCategories.OBJECTS.value, layer)
        crafts = board.categories(AssetCategories.CRAFTS.value, layer)
        space = objects + crafts
        for obj in space:
            if elevation is not None and obj.state.elevation != elevation:
                continue
            x1 = int(obj.state.position.x)
            y1 = int(obj.state.position.y)
            rects.append((x1, y1, x1 + obj.dimensions.w, y1 + obj.dimensions.l))
            
        return rects

    def generate(self, board: Board, layer: str) -> Dict[int, List[Boundary]]:
        """
        Master orchestrator for the Perimeter Generator pipeline.
        Derives boundaries independently for each active elevation tier on the layer.
        """
        logger.info(
            f"Calculating dynamic perimeter boundaries for layer: {layer}"
        )
        
        weights = board.weights(layer)
        elevations = {w.state.elevation for w in weights} | {0}
        perimeters_by_tier: Dict[int, List[Boundary]] = {}

        for elevation in elevations:
            rects = self.extract(board, layer, elevation=elevation)
            if not rects:
                continue
                
            raw_contours = geometry.contours(rects)
            perimeter = [
                Boundary(Position(x, y), Dimensions(w, l))
                for x, y, w, l, *_ in raw_contours
            ]
            perimeters_by_tier[elevation] = perimeter
            logger.info(
                f"Derived tier={elevation} hull containing {len(perimeter)} edges."
            )

        return perimeters_by_tier