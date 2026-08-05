"""
# Ontology: Screen
"""

# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.player import Player

# Cython Libraries
from libs.core import Position, Dimensions
from libs.render import canvas, construct, render, TexturePtr

class Screen:
    """
    Manages the rendering layer and camera calculations.
    """
    screensize: Dimensions
    boardsize: Dimensions
    canvas_tex: TexturePtr

    def __init__(self, 
        screensize: Dimensions,
        boardsize: Dimensions,
        tiles: List[Asset]   
    ):
        self.screensize = screensize
        self.boardsize = boardsize
        
        # The background texture is now the size of the whole board
        self.canvas_tex = canvas(self.boardsize)
        
        cython_tiles = [( 
            # TODO: Fetch TexturePtr from Registry using tile.properties.key
            None,
            Position(x=0, y=0),
            tile.properties.dimensions,
            tile.state.position,
            tile.properties.dimensions,
            tile.state.multiple
        ) for tile in tiles]
        
        construct(self.canvas_tex, cython_tiles)

    def camera(self, player: Player) -> Position:
        """
        Calculates the camera's top-left coordinates, centered on the player,
        and clamps it to the boundaries of the board.
        """
        # Center the camera on the player
        cam_x = player.shape.position.x + (player.shape.dimensions.l // 2) - (self.screensize.l // 2)
        cam_y = player.shape.position.y + (player.shape.dimensions.w // 2) - (self.screensize.w // 2)

        # Clamp to board edges
        max_x = max(0, self.boardsize.l - self.screensize.l)
        max_y = max(0, self.boardsize.w - self.screensize.w)

        cam_x = max(0, min(cam_x, max_x))
        cam_y = max(0, min(cam_y, max_y))

        return Position(x=cam_x, y=cam_y)

    def draw(self, assets: List[Asset], player: Player, registry: Registry) -> None:
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
            
            # 3. Create a flat tuple of PRIMITIVE INTEGERS for destination
            dx, dy = asset.state.position.x, asset.state.position.y
            dw, dh = asset.properties.dimensions.l, asset.properties.dimensions.w
            
            # Optional: Simple Python-side integer camera culling here
            if (dx + dw >= pov.x and dx <= pov.x + self.screensize.l and
                dy + dh >= pov.y and dy <= pov.y + self.screensize.w):
                
                active_assets.append((tex, sx, sy, sw, sh, dx, dy, dw, dh))

        render(self.canvas_tex, active_assets, pov, self.screensize)