"""
# Ontology: Screen
"""

# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
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
        self.bg_canvas = canvas(self.boardsize.l, self.boardsize.w)
        self.fg_canvas = canvas(self.boardsize.l, self.boardsize.w)
        
        cython_bg_tiles = []
        cython_fg_tiles = []
        
        for tile in tiles:
            # Query Registry using the computed tile key
            tex_data = registry.data(tile.frame.key(tile.properties.key, tile.state))
            if tex_data:
                tex, sx, sy, sw, sh = tex_data
                
                # Append flat primitives directly for the C-loop
                tile_tuple = ( 
                    tex,
                    sx, sy, sw, sh,
                    tile.state.position.x, tile.state.position.y,
                    tile.properties.dimensions.l, tile.properties.dimensions.w,
                    tile.state.multiple.nx, tile.state.multiple.ny
                )

                # Route properties
                if tile.state.instance == "back":
                    cython_bg_tiles.append(tile_tuple)
                elif tile.state.instance == "fore":
                    cython_fg_tiles.append(tile_tuple)
        
        construct(self.bg_canvas, cython_bg_tiles)
        construct(self.fg_canvas, cython_fg_tiles)

    def camera(self, player: Player) -> Position:
        """
        Calculates the camera's top-left coordinates, centered on the player,
        and clamps it to the boundaries of the board.
        """
        # Center the camera on the player
        cam_x = player.properties.position.x + (player.properties.dimensions.l // 2) - (self.screensize.l // 2)
        cam_y = player.properties.position.y + (player.properties.dimensions.w // 2) - (self.screensize.w // 2)

        # Clamp to board edges
        max_x = max(0, self.boardsize.l - self.screensize.l)
        max_y = max(0, self.boardsize.w - self.screensize.w)

        cam_x = max(0, min(cam_x, max_x))
        cam_y = max(0, min(cam_y, max_y))

        return Position(x=cam_x, y=cam_y)

    def draw(self, assets: List[Asset], player: Player, registry: Registry) -> None:
        """
        Calculates viewport positioning, culls non-visible items, and routes data to the renderer.
        """
        pov = self.camera(player)
        active_assets = []
        
        for asset in assets:
            # 1. Resolve current animation frame key
            frame_key = asset.frame.key(asset.properties.key, asset.state)
            
            # 2. Query registry for C-level source coordinates
            tex_data = registry.data(frame_key)

            if not tex_data:
                continue 

            tex, sx, sy, sw, sh = tex_data
            
            # 3. Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
            dx, dy = asset.state.position.x, asset.state.position.y
            dw, dh = asset.properties.dimensions.l, asset.properties.dimensions.w
            
            # 4. Strict Camera Culling: Only pass geometry if intersecting the camera frame 
            if (dx + dw >= pov.x and dx <= pov.x + self.screensize.l and
                dy + dh >= pov.y and dy <= pov.y + self.screensize.w):
                
                active_assets.append((tex, sx, sy, sw, sh, dx, dy, dw, dh))

        # Pass purely native integers to bypass heavy object allocation
        render(
            self.bg_canvas, 
            self.fg_canvas,
            active_assets, 
            pov.x, 
            pov.y, 
            self.screensize.l, 
            self.screensize.w
        )