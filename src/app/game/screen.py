"""
# Ontology: Screen

Package for the Screen class, an abstraction over the Cython SDL rendering interface and image registries.
"""

# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.config.enums import AssetInstances
from app.input.player import Player

# Cython Libraries
from libs.core import Position, Dimensions
from libs.render import canvas, construct, render, TexturePtr
from libs.registry import Registry

class Screen:
    """
    Manages the rendering layer and camera calculations.
    """
    screensize: Dimensions
    boardsize: Dimensions
    bg_canvas: TexturePtr
    fg_canvas: TexturePtr

    def __init__(self, 
        screensize: Dimensions,
        boardsize: Dimensions,
        tiles: List[Asset],
        registry: Registry
    ):
        self.screensize = screensize
        self.boardsize = boardsize
        
        # Instantiate Painter's Algorithm Targets
        self.bg_canvas = canvas(self.boardsize.w, self.boardsize.l)
        self.fg_canvas = canvas(self.boardsize.w, self.boardsize.l)
        
        cython_bg_tiles = []
        cython_fg_tiles = []
        
        for tile in tiles:
            # Query Registry using the computed tile key
            frame_key = tile.frame.key(tile.id, tile.state)
            tex_data = registry.data(frame_key)
            if tex_data:
                tex, sx, sy, sw, sl = tex_data
                
                # Append flat primitives directly for the C-loop
                tile_tuple = ( 
                    tex,
                    sx, 
                    sy, 
                    sw, 
                    sl,
                    tile.state.position.x, 
                    tile.state.position.y,
                    tile.dimensions.w, 
                    tile.dimensions.l,
                    tile.state.multiple.nx, 
                    tile.state.multiple.ny
                )

                # Route properties
                if tile.taxonomy.instance == AssetInstances.BACK:
                    cython_bg_tiles.append(tile_tuple)
                elif tile.taxonomy.instance == AssetInstances.FORE:
                    cython_fg_tiles.append(tile_tuple)
        
        construct(self.bg_canvas, cython_bg_tiles)
        construct(self.fg_canvas, cython_fg_tiles)

    def camera(self, player: Player) -> Position:
        """
        Calculates the camera's top-left coordinates, centered on the player,
        and clamps it to the boundaries of the board.
        """
        # Center the camera on the player
        cam_x = player.state.position.x + (player.dimensions.w // 2) - (self.screensize.w // 2)
        cam_y = player.state.position.y + (player.dimensions.l // 2) - (self.screensize.l // 2)

        # Clamp to board edges
        max_x = max(0, self.boardsize.w - self.screensize.w)
        max_y = max(0, self.boardsize.l - self.screensize.l)

        cam_x = max(0, min(cam_x, max_x))
        cam_y = max(0, min(cam_y, max_y))

        return Position(x=cam_x, y=cam_y)

    def draw(self, 
        assets: List[Asset], 
        player: Player, 
        registry: Registry
    ) -> None:
        """
        Calculates viewport positioning, culls non-visible items, and routes data to the renderer.
        """
        pov = self.camera(player)
        active_assets = []
        
        for asset in assets:
            # 1. Resolve current animation frame key
            frame_key = asset.frame.key(asset.id, asset.state)
            
            # 2. Query registry for C-level source coordinates
            tex_data = registry.data(frame_key)

            if not tex_data:
                continue 

            tex, sx, sy, sw, sl = tex_data
            
            # 3. Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
            dx, dy = asset.state.position.x, asset.state.position.y
            dw, dl = asset.dimensions.w, asset.dimensions.l
            
            # 4. Strict Camera Culling: Only pass geometry if intersecting the camera frame 
            if (dx + dw >= pov.x and dx <= pov.x + self.screensize.w and
                dy + dl >= pov.y and dy <= pov.y + self.screensize.l):
                
                active_assets.append((tex, sx, sy, sw, sl, dx, dy, dw, dl))

        # Pass purely native integers to bypass heavy object allocation
        render(
            self.bg_canvas, 
            self.fg_canvas,
            active_assets, 
            pov.x, 
            pov.y, 
            self.screensize.w, 
            self.screensize.l
        )