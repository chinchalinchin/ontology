"""
# Ontology: app.game.screen

Package for the Screen, an abstraction over the Cython SDL rendering interface and image registries.
"""

# Standard Libraries
import logging
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.config.enums import AssetInstances, AssetCategories
from app.game.menus.core import Menu

# Cython Libraries
from libs.core.models import Position, Dimensions
from libs.graphics.render import (
    canvas, 
    construct, 
    render, 
    save, 
    superimpose, 
    write 
)
from libs.graphics.registry import (
    Registry, 
    TexturePtr
)

logger = logging.getLogger(__name__)

class Screen:
    """
    Manages the rendering layer and camera calculations.
    """
    screensize: Dimensions
    boardsize: Dimensions
    bg_canvas: TexturePtr
    fg_canvas: TexturePtr
    registry: Registry


    def __init__(self, 
        screensize: Dimensions,
        boardsize: Dimensions,
        tiles: List[Asset],
        registry: Registry
    ):
        self.screensize = screensize
        
        # Hardware Minimum Clamp: Guarantee rendering bounds never drop below viewport size
        self.boardsize = Dimensions(
            w=max(boardsize.w, screensize.w),
            l=max(boardsize.l, screensize.l)
        )
        
        logger.info(f"Initializing Screen overlay (Viewport: {self.screensize.w}x{self.screensize.l} | Board: {self.boardsize.w}x{self.boardsize.l})")
        
        self.registry = registry

        # Canvas Opacity Flag: If layer has no tiles, initialize to opaque black
        is_opaque = len(tiles) == 0

        # Instantiate Painter's Algorithm Targets
        self.bg_canvas = canvas(self.boardsize.w, self.boardsize.l, opaque=is_opaque)
        self.fg_canvas = canvas(self.boardsize.w, self.boardsize.l) # Foreground stays transparent
        
        cython_bg_tiles = []
        cython_fg_tiles = []
        
        logger.debug(f"Offloading primitive coordinates to Cython background construct for {len(tiles)} total tiles.")

        for tile in tiles:
            # Query Registry using the computed tile keys
            frame_keys = tile.frame.keys(tile.id, tile.state)
            for frame_key in frame_keys:
                tex_data = self.registry.image(frame_key)
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


    def _flatten(self, menus: List[Menu], overlays: List[Menu]) -> List[Asset]:
        """
        """
        widgets = []
        for menu in overlays:
            if hasattr(menu, 'widgets') and menu.widgets:
                widgets.extend(menu.widgets.values())
        for menu in menus:
            if hasattr(menu, 'widgets') and menu.widgets:
                widgets.extend(menu.widgets.values())
        return widgets
    
    def camera(self, 
        focus: Position, 
        dim: Dimensions
    ) -> Position:
        """
        Calculates the camera's top-left coordinates, centered on the focus target,
        and clamps it to the boundaries of the board.
        """
        # Center the camera on the target
        cam_x = focus.x + (dim.w // 2) - (self.screensize.w // 2)
        cam_y = focus.y + (dim.l // 2) - (self.screensize.l // 2)

        # Clamp to board edges
        max_x = max(0, self.boardsize.w - self.screensize.w)
        max_y = max(0, self.boardsize.l - self.screensize.l)

        cam_x = max(0, min(cam_x, max_x))
        cam_y = max(0, min(cam_y, max_y))

        return Position(x=cam_x, y=cam_y)

    def clear(self) -> None:
        render.clear()

    def present(self) -> None:
        render.present()

    def draw(self, 
        assets: List[Asset], 
        focus: Position,
        dim: Dimensions
    ) -> None:
        """
        Calculates viewport positioning, culls non-visible items, and routes data to the renderer.
        """
        pov = self.camera(focus, dim)
        active_assets = []
        
        # 1. Height-sort the assets directly prior to querying asset.frame.keys()
        # Primary Sort: Explicit Height OR (Y + Length)
        # Secondary Sort: Depth-index tie-breaker for overlapping entities
        assets.sort(key=lambda a: (
            a.state.height if getattr(a.state, 'height', None) is not None else (
                (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
            ),
            getattr(a.state, 'depth', 0)
        ))
        
        for asset in assets:
            # Filter out Tile assets to avoid dynamic rendering artifacts; 
            # they are already drawn on the pre-compiled canvases.
            if asset.category == AssetCategories.TILES:
                continue

            # 2. Resolve current animation frame keys
            frame_keys = asset.frame.keys(asset.id, asset.state)
            
            for frame_key in frame_keys:
                # 3. Query registry for C-level source coordinates
                tex_data = self.registry.image(frame_key)

                if not tex_data:
                    continue 

                tex, sx, sy, sw, sl = tex_data
                
                # 4. Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
                dx, dy = asset.state.position.x, asset.state.position.y
                dw, dl = sw, sl
                # dw, dl = asset.dimensions.w, asset.dimensions.l
                
                # 5. Strict Camera Culling: Only pass geometry if intersecting the camera frame 
                if (dx + dw >= pov.x and dx <= pov.x + self.screensize.w and
                    dy + dl >= pov.y and dy <= pov.y + self.screensize.l):
                    
                    active_assets.append((tex, sx, sy, sw, sl, dx, dy, dw, dl))

        logger.debug(f"Render Payload: Camera({pov.x}, {pov.y}) | Passing {len(active_assets)} dynamic primitive matrices to Cython.")

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


    def interface(self, menus: List[Menu], overlays: List[Menu]) -> None:
        widgets = self._flatten(menus, overlays)
        primitives = []
        
        for widget in widgets:
            for widget in widgets:
                # Check if this widget manages a custom canvas (Duck-Typing)
                if hasattr(widget.state, 'canvas') and widget.state.canvas is not None:
                    tex = widget.state.canvas
                    
                    # 1. Fetch the clean background from Registry
                    base_keys = widget.frame.keys(widget.id, widget.state)
                    base_ptr, sx, sy, sw, sl = self.registry.image(base_keys[0])
                    
                    # 2. Stamp the clean background over the old canvas to clear the old text
                    construct(tex, [(base_ptr, sx, sy, sw, sl, 0, 0, sw, sl, 1, 1)])
                    
                    # 3. Bake the new text directly onto the freshly cleared canvas
                    # TODO: determine how font should be loaded
                    font = self.registry.font("dialogue")
                    current_content = widget.state.current()
                    if isinstance(current_content, str):
                        write((tex, 0, 0, sw, sl, 0, 0, sw, sl), current_content, font)
                            
                    # Draw the canvas (whether freshly rebaked or statically cached)
                    tex = widget.state.canvas
                    primitives.append((
                        tex, 0, 0, tex.w, tex.l, 
                        widget.state.position.x, widget.state.position.y, 
                        widget.dimensions.w, widget.dimensions.l
                    ))
                continue
                
            # STANDARD FALLBACK: If no custom canvas, query the Registry normally
            frame_keys = widget.frame.keys(widget.id, widget.state)
            for key in frame_keys:
                tex_data = self.registry.image(key)
                if tex_data:
                    tex, sx, sy, sw, sl = tex_data
                    primitives.append((
                        tex, sx, sy, sw, sl, 
                        widget.state.position.x, widget.state.position.y, 
                        widget.dimensions.w, widget.dimensions.l
                    ))

        # Send directly to the Cython rendering function
        superimpose(primitives)


    def export_background(self, out_path: str) -> None:
        """
        Exports the raw generated background canvas mapping to disk.
        """
        logger.info(f"Dumping pre-constructed map textures (bg_canvas) to file system -> {out_path}")
        save(out_path, self.boardsize.w, self.boardsize.l, target=self.bg_canvas)


    def export_render(self, 
        out_path: str, 
        assets: List[Asset], 
        focus: Position, 
        fdim: Dimensions
    ) -> None:
        """
        Draws a composited snapshot of the frame and extracts the VRAM buffer to disk.
        """
        logger.info(f"Extracting VRAM view buffer representing full composition to file system -> {out_path}")
        self.draw(assets, focus, fdim)
        save(out_path, self.screensize.w, self.screensize.l)