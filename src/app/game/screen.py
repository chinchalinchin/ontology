"""
# Ontology: app.game.screen

Package for the Screen, an abstraction over the Cython SDL rendering interface and image registries.
"""

# Standard Libraries
import logging
from typing import (
    List, 
    Union
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetInstances, 
    AssetCategories
)
from app.game.menus.core import Menu

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions
)
from libs.graphics.render import (
    clear, 
    present,
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
        
        logger.info(
            f"Initializing Screen (Viewport: {self.screensize.w}x{self.screensize.l} |" 
            f"Board: {self.boardsize.w}x{self.boardsize.l})"
        )
        
        self.registry = registry

        # Canvas Opacity Flag: If layer has no tiles, initialize to opaque black
        is_opaque = len(tiles) == 0

        # Instantiate Painter's Algorithm Targets
        self.bg_canvas = canvas(self.boardsize.w, self.boardsize.l, opaque=is_opaque)
        self.fg_canvas = canvas(self.boardsize.w, self.boardsize.l) # Foreground stays transparent
        
        back_tiles, fore_tiles = self._prerender(tiles)
        
        construct(self.bg_canvas, back_tiles)
        construct(self.fg_canvas, fore_tiles)


    def _prerender(self, 
        tiles: List[Asset]
    ) -> tuple[list, list]:
        """
        Prerender Tile Assets.
        """
        back_tiles, fore_tiles = [], []
        
        logger.debug(f"Constructing {len(tiles)} total tiles...")

        for tile in tiles:
            # Query Registry using the computed tile keys
            frame_keys = tile.frame.keys(tile.id, tile.state)
            for frame_key in frame_keys:
                tex_data = self.registry.image(frame_key)
                if tex_data:
                    tex, sx, sy, sw, sl = tex_data
                    
                    # Append flat primitives directly for the C-loop
                    tile_tuple = (
                        tex, sx, sy, sw, sl,
                        tile.state.position.x, 
                        tile.state.position.y,
                        tile.dimensions.w, 
                        tile.dimensions.l,
                        tile.state.multiple.nx, 
                        tile.state.multiple.ny
                    )

                    # Route properties
                    if tile.taxonomy.instance == AssetInstances.BACK:
                        back_tiles.append(tile_tuple)
                    elif tile.taxonomy.instance == AssetInstances.FORE:
                        fore_tiles.append(tile_tuple)
        return back_tiles, fore_tiles

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

    def clear(self) -> None: clear()

    def present(self) -> None: present()

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

        logger.debug(f"Render Payload: Camera({pov.x}, {pov.y}) | Total Assets: {len(active_assets)}")

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


    def stamp(self, widget: Asset, content: Union[str, List[str]]) -> None:
        """
        Dynamically restamps background and bakes updated text for O(N) runtime rendering. 
        """
        if not hasattr(widget.state, 'canvas') or widget.state.canvas is None:
            return
            
        tex = widget.state.canvas
        base_keys = widget.frame.keys(widget.id, widget.state)
        base_ptr, sx, sy, sw, sl = self.registry.image(base_keys[0])
        
        # 1. Fetch and stamp clean background
        construct(tex, [(base_ptr, sx, sy, sw, sl, 0, 0, sw, sl, 1, 1)])
        
        # 2. Re-write the font over the cleared canvas
        if isinstance(content, str) and content:
            # TODO: determine how font key should be set
            font = self.registry.font("dialogue")
            if font:
                write((tex, 0, 0, sw, sl, 0, 0, sw, sl), content, font)


    def interface(self, menus: List[Menu], overlays: List[Menu]) -> None:
        """
        Bypasses baking to process the widget dictionaries in O(N) linear time directly.
        """
        widgets = self._flatten(menus, overlays)
        primitives = []
        
        for widget in widgets:
            if hasattr(widget.state, 'canvas') and widget.state.canvas is not None:
                tex = widget.state.canvas
                primitives.append((
                    tex, 0, 0, tex.w, tex.l, 
                    widget.state.position.x, widget.state.position.y, 
                    widget.dimensions.w, widget.dimensions.l
                ))
            else:
                frame_keys = widget.frame.keys(widget.id, widget.state)

                for key in frame_keys:
                    tex_data = self.registry.image(key)
                    if tex_data:
                        tex, sx, sy, sw, sl = tex_data
                        primitives.append((
                            tex, sx, sy, sw, sl, 
                            widget.state.position.x, widget.state.position.y, 
                            sw, sl
                        ))
                    elif widget.taxonomy.instance != AssetInstances.PANES:
                        # Ignore transparent layout panes
                        logger.warning(f"Registry MISS for key: '{key}' on widget '{widget.name}'")

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