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
from app.models.state.widgets import (
    DisplayState,
    PaneState
)
from app.models.state.sprites import (
    SpriteState,
    PlayerState
)
from app.game.menus.core import Menu

# Cython Libraries
import libs.graphics.render as render

from libs.core.models import (
    Position, 
    Dimensions
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
        self.bg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l, 
            opaque=is_opaque
        )
        self.fg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l
        ) # Foreground stays transparent
        
        back_tiles, fore_tiles = self._prerender(tiles)
        
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)


    def _prerender(self, 
        tiles: List[Asset]
    ) -> tuple[list, list]:
        """
        Prerender Tile Assets.
        """
        back_tiles, fore_tiles = [], []
        
        logger.debug(f"Constructing {len(tiles)} total tiles...")

        for tile in tiles:
            frame_keys = tile.frame.keys(tile.id, tile.state)
            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data: continue

                tex, sx, sy, sw, sl = tex_data
                tile_tuple = (
                    tex, sx, sy, sw, sl,
                    tile.state.position.x + ox, 
                    tile.state.position.y + oy,
                    tile.dimensions.w, tile.dimensions.l,
                    tile.state.multiple.nx, tile.state.multiple.ny
                )
                # Route properties
                if tile.taxonomy.instance == AssetInstances.BACK:
                    back_tiles.append(tile_tuple)
                elif tile.taxonomy.instance == AssetInstances.FORE:
                    fore_tiles.append(tile_tuple)
                    
        return back_tiles, fore_tiles


    def _widgets(self, menus: List[Menu]) -> None:
        """Helper to collect and superimpose widget primitives for a set of menus."""
        widgets = []
        for menu in menus:
            if menu.widgets:
                widgets.extend(menu.widgets.values())

        primitives = []
        for widget in widgets:
            if isinstance(widget.state, DisplayState):
                tex = widget.state.canvas
                primitives.append((
                    tex, 0, 0, tex.w, tex.l,
                    widget.state.position.x, widget.state.position.y,
                    widget.dimensions.w, widget.dimensions.l
                ))
                continue

            frame_keys = widget.frame.keys(widget.id, widget.state)
            for key, ox, oy in frame_keys:
                if key:
                    tex_data = self.registry.image(key)

                    if not tex_data:
                        if not (
                            isinstance(widget.state, DisplayState) or
                            isinstance(widget.state, PaneState)
                        ):
                            logger.warning(f"Registry MISS: Frame key not found: '{key}'")
                        continue

                    tex, sx, sy, sw, sl = tex_data
                    primitives.append((
                        tex, sx, sy, sw, sl,
                        widget.state.position.x + ox, widget.state.position.y + oy,
                        sw, sl
                    ))

        if primitives:
            render.superimpose(primitives)


    def _flatten(self, 
        menus: List[Menu], 
        overlays: List[Menu]
    ) -> List[Asset]:
        """
        """
        widgets = []
        for menu in overlays:
            if menu.widgets:
                widgets.extend(menu.widgets.values())
        for menu in menus:
            if menu.widgets:
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


    def clear(self) -> None: render.clear()


    def present(self) -> None: render.present()


    def destroy(self) -> None:
        """
        Explicitly destroys hardware canvas textures held by this screen.
        """
        if self.bg_canvas:
            render.destroy(self.bg_canvas)
            self.bg_canvas = None
        if self.fg_canvas:
            render.destroy(self.fg_canvas)
            self.fg_canvas = None
            
    # ------------------------------------------------ CANVAS METHODS

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
        
        # Height-sort the assets directly prior to querying asset.frame.keys()
        #   Primary Sort: Explicit Height OR (Y + Length)
        #   Secondary Sort: Depth-index tie-breaker for overlapping entities
        assets.sort(key=lambda a: (
            a.state.height if a.state.height is not None else (
                (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
            ),
            a.state.depth
        ))

        for asset in assets:
            if asset.category == AssetCategories.TILES: continue

            frame_keys = asset.frame.keys(asset.id, asset.state)
            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data: 
                    if not (
                        isinstance(asset.state, SpriteState) or 
                        isinstance(asset.state, PlayerState)
                    ):
                        logger.warning(f"Registry MISS: Frame key not found: '{frame_key}'")
                    continue 

                # Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
                tex, sx, sy, sw, sl = tex_data
                dx, dy = asset.state.position.x + ox, asset.state.position.y + oy
                dw, dl = sw, sl

                # Strict Camera Culling: Only pass geometry if intersecting the camera frame 
                if (dx + dw >= pov.x and dx <= pov.x + self.screensize.w and
                    dy + dl >= pov.y and dy <= pov.y + self.screensize.l):
                    active_assets.append((tex, sx, sy, sw, sl, dx, dy, dw, dl))

        logger.debug(f"Render Payload: Camera({pov.x}, {pov.y}) | Total Assets: {len(active_assets)}")

        # Pass purely native integers to bypass heavy object allocation
        render.render(
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
        if not isinstance(widget.state, DisplayState):
            return
            
        tex = widget.state.canvas
        base_keys = widget.frame.keys(widget.id, widget.state)
        base_key, ox, oy = base_keys[0]  # Just unpack the first element

        tex_data = self.registry.image(base_key)
        if not tex_data:
            logger.warning(f"Registry MISS: Frame key not found: '{base_key}'")
            return

        base_ptr, sx, sy, sw, sl = tex_data
        
        # 1. Fetch and stamp clean background
        render.construct(tex, [(base_ptr, sx, sy, sw, sl, 0, 0, sw, sl, 1, 1)])
        
        # 2. Re-write the font over the cleared canvas
        if isinstance(content, str) and content:
            font_key = widget.state.font
            font = self.registry.font(font_key)
            if not font:
                logger.warning(
                    f"Registry MISS: Font '{font_key}' not found for widget '{widget.name}'."
                )
                return
            render.write((tex, 0, 0, sw, sl, 0, 0, sw, sl), content, font)
               

    def interface(self, menus: List[Menu], overlays: List[Menu]) -> None:
        """       
        Renders HUD overlays, dims the background if modal menus exist, 
        and renders modal menus on top.
        """
        # 1. Render HUD / Overlays over the raw world
        if overlays:
            self._widgets(overlays)

        # 2. Dim background and render modal menus
        if menus:
            # Alpha: 140-180 provides good contrast for UI panes
            for menu in menus:
                render.dim(r=0, g=0, b=0, a=120)
                self._widgets([menu])

    def rebake(self, 
        tiles: List[Asset], 
        boardsize: Dimensions,
        screensize: Dimensions = None
    ) -> None:
        """
        Dynamically reallocates Cython VRAM canvases for a new world state.
        Safely destroys old textures immediately to prevent VRAM OOM crashes.
        """
        logger.info("Rebaking Screen canvases for new world state...")

        # 1. Explicitly free GPU memory immediately (bypassing Python GC)
        if self.bg_canvas:
            render.destroy(self.bg_canvas)
        if self.fg_canvas:
            render.destroy(self.fg_canvas)

        # 2. Update dimensions
        if screensize:
            self.screensize = screensize

        # Hardware Minimum Clamp: Guarantee rendering bounds never drop below viewport size
        self.boardsize = Dimensions(
            w=max(boardsize.w, self.screensize.w),
            l=max(boardsize.l, self.screensize.l)
        )
        
        logger.debug(f"New Canvas Bounds: {self.boardsize.w}x{self.boardsize.l}")

        # 3. Canvas Opacity Flag: If layer has no tiles, initialize to opaque black
        is_opaque = len(tiles) == 0

        # 4. Reallocate VRAM
        self.bg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l, 
            opaque=is_opaque
        )
        self.fg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l
        )

        # 5. Prerender and Construct
        back_tiles, fore_tiles = self._prerender(tiles)

        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)

    # ------------------------------------------------ EXPORT METHODS

    def export_background(self, out_path: str) -> None:
        """
        Exports the raw generated background canvas mapping to disk.
        """
        logger.info(f"Dumping pre-constructed map textures (bg_canvas) to file system -> {out_path}")
        render.save(
            out_path, 
            self.boardsize.w, 
            self.boardsize.l, 
            target=self.bg_canvas
        )


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
        render.save(
            out_path, 
            self.screensize.w, 
            self.screensize.l
        )


    def export_map(self, out_path: str, assets: List[Asset]) -> None:
        """
        Draws a composited snapshot of the entire board and extracts the full VRAM buffer to disk,
        bypassing the viewport camera culling.
        """
        logger.info(f"Extracting full board VRAM view buffer to file system -> {out_path}")
        active_assets = []
        
        assets.sort(key=lambda a: (
            a.state.height if a.state.height is not None else (
                (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
            ),
            a.state.depth
        ))

        for asset in assets:
            if asset.category == AssetCategories.TILES: continue

            frame_keys = asset.frame.keys(asset.id, asset.state)
            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)
                if not tex_data: continue 

                tex, sx, sy, sw, sl = tex_data
                dx, dy = asset.state.position.x + ox, asset.state.position.y + oy
                dw, dl = sw, sl

                if (dx + dw >= 0 and dx <= self.boardsize.w and
                    dy + dl >= 0 and dy <= self.boardsize.l):
                    active_assets.append((tex, sx, sy, sw, sl, dx, dy, dw, dl))
        
        # 1. Allocate a temporary canvas matching the absolute board dimensions
        full_target = render.canvas(
            self.boardsize.w, 
            self.boardsize.l, 
            opaque=True
        )

        # 2. Render directly onto the transient target instead of the default viewport
        render.render(
            self.bg_canvas, 
            self.fg_canvas,
            active_assets, 
            0, 
            0, 
            self.boardsize.w, 
            self.boardsize.l,
            target=full_target # Invokes the Cython update
        )
        
        # 3. Read the pixels strictly from the custom target
        render.save(out_path, self.boardsize.w, self.boardsize.l, target=full_target)
        
        # 4. Explicitly free the GPU memory to prevent memory leaks
        render.destroy(full_target)