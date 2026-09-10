"""
# Ontology: app.services.generators.perimeter

Package for dynamic environment boundary generation.
"""
# Standard Libraries
import logging
from typing import List

# Application Libraries
from app.game.board import Board
from app.config.enums import AssetCategories, AssetInstances

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Boundary

logger = logging.getLogger(__name__)

class Perimeter:
    """
    Derives the simply-connected outer hull of an environment dynamically,
    translating spatial limits into Cython-ready mathematical vectors.
    """
    def extract(self, board: Board, layer: str) -> List[tuple[int, int, int, int]]:
        """
        Translates physical Tile and Object footprints into raw mathematical primitives.
        """
        rects = []
        
        # 1. Map Tiles
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
            
        # 2. Map Game Space
        objects = board.categories(AssetCategories.OBJECTS.value, layer)
        crafts = board.categories(AssetCategories.CRAFTS.value)
        space = objects + crafts
        for obj in space:
            x1 = int(obj.state.position.x)
            y1 = int(obj.state.position.y)
            rects.append((x1, y1, x1 + obj.dimensions.w, y1 + obj.dimensions.l))
            
        return rects

    def generate(self, board: Board, layer: str) -> List[Boundary]:
        """
        Master orchestrator for the Perimeter Generator pipeline.
        """
        logger.info(
            f"Calculating dynamic perimeter boundaries for layer: {layer}"
        )
        
        rects = self.extract(board, layer)
        if not rects:
            return []
            
        perimeter = geometry.contours(rects)
        
        logger.info(
            f"Derived simply-connected hull containing {len(perimeter)} edges."
        )
        return perimeter