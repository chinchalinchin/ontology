"""
@domain.system
@app.core
@app.component
@workflow.rendering

# Ontology: Source - app.game.screen

Implementation of the Screen, an abstraction over the Cython SDL rendering interface and the Registry.
"""

# Standard Libraries
import logging
from typing import (
    List,
    Optional,
    Tuple,
    Union,
)

# Application Libraries
from app.assets.base import Asset
from app.game.menus.core import Menu
from app.models.state import (
    CalendarState,
    PaneState,
    SheetState,
)
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    ChannelTypes,
    SystemPanes
)

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import (
    Dimensions,
    Position,
)
from libs.graphics.registry import (
    Registry,
    TexturePtr,
)

logger = logging.getLogger(__name__)


class Screen:
    """
    Manages the rendering layer and camera calculations.
    """
    # Fields
    screensize: Dimensions
    boardsize: Dimensions
    bg_canvas: TexturePtr
    fg_canvas: TexturePtr
    registry: Registry
    # Constants
    _CULL_MARGIN: int = 64

    # ------------------------------------------------ STATIC METHODS

    @staticmethod
    def _sort(asset: Asset) -> Tuple[int, int, int, int]:
        dim_l = asset.dimensions.l if asset.dimensions else 0
        ground_y = int(asset.state.position.y + dim_l + asset.state.anchor)
        return (asset.elevation, asset.substrate, ground_y, asset.properties.priority)


    def release(self, menu: Menu) -> None:
        """Explicitly destroys hardware canvas textures held by a Menu's panes."""
        if not menu.widgets:
            return
        for widget in menu.widgets.values():
            if isinstance(widget.state, PaneState):
                self.registry.destroy_canvas(widget.name)


    def __init__(
        self,
        screensize: Dimensions,
        boardsize: Dimensions,
        tiles: List[Asset],
        registry: Registry,
        calendar: CalendarState,
    ):
        self.screensize = screensize
        self.boardsize = boardsize
        self.registry = registry

        # Hardware Target Minimum: Texture size must not drop below viewport bounds
        canvas_w = max(boardsize.w, screensize.w)
        canvas_l = max(boardsize.l, screensize.l)

        logger.info(
            f"Initializing Screen (Viewport: {self.screensize.w}x{self.screensize.l} |"
            f"Board: {self.boardsize.w}x{self.boardsize.l})"
        )

        is_opaque = len(tiles) == 0

        self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
        self.fg_canvas = render.canvas(canvas_w, canvas_l)

        back_tiles, fore_tiles = self._prerender(tiles, calendar)
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)

    # ------------------------------------------------ PRIVATE METHODS

    def _in_viewport(
        self,
        asset: Asset,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
    ) -> bool:
        """
        Broad-phase viewport AABB check. Bypasses unit-tile bounds for procedural
        multi-tile assets (Fluids, Shorelines) whose geometry extends beyond asset.dimensions.
        """
        if asset.instance in (
            AssetInstances.FLUIDS,
            AssetInstances.SHORELINES,
        ):
            return True

        px = asset.state.position.x
        py = asset.state.position.y
        dw = asset.dimensions.w if asset.dimensions else 0
        dl = asset.dimensions.l if asset.dimensions else 0

        return (
            px + dw >= min_x and px <= max_x and
            py + dl >= min_y and py <= max_y
        )

    
    def _prerender(
        self,
        tiles: List[Asset],
        calendar: CalendarState,
    ) -> Tuple[ list, list ]:
        back_tiles, fore_tiles = [], []

        for tile in tiles:
            # Query macro-temporal era projection
            frame_keys = tile.frame.eras(tile.id, calendar)

            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)
                
                if not tex_data: continue

                tex, sx, sy, sw, sl = tex_data
                tile_tuple = (
                    tex, sx, sy, sw, sl,
                    tile.state.position.x + ox,
                    tile.state.position.y + oy,
                    tile.dimensions.w, tile.dimensions.l,
                    tile.state.multiple.nx, tile.state.multiple.ny,
                )

                if tile.taxonomy.instance == AssetInstances.ENVIRON:
                    back_tiles.append(tile_tuple)
                elif tile.taxonomy.instance == AssetInstances.CANOPY:
                    fore_tiles.append(tile_tuple)

        return back_tiles, fore_tiles


    def _assemble(
        self,
        assets: List[Asset],
        pov: Position,
        bounds: Dimensions,
    ) -> Tuple[list, list]:
        """
        Broad-phase culls assets to the camera viewport, height-sorts the visible
        subset, and assembles render primitives and auxiliary channel operations.
        """
        active_assets = []
        active_channels = []

        min_x = pov.x - self._CULL_MARGIN
        min_y = pov.y - self._CULL_MARGIN
        max_x = pov.x + bounds.w + self._CULL_MARGIN
        max_y = pov.y + bounds.l + self._CULL_MARGIN

        # 1. Broad-phase filter without mutating Board._cache.cached_renderables
        visible = [
            asset for asset in assets
            if asset.category != AssetCategories.TILES
            and self._in_viewport(asset, min_x, min_y, max_x, max_y)
        ]

        # 2. Height-sort only the visible subset prior to querying asset.frame.keys()
        visible.sort(key=self._sort)

        # 3. Narrow-phase frame resolution and crop culling
        for asset in visible:
            frame_keys = asset.frame.keys(asset.id, asset.state)
            channels = asset.frame.channels(asset.id, asset.state, asset.properties)
            submerge_channel = next(
                (
                    op for op in channels
                    if op[0] == ChannelTypes.SUBMERGE
                ),
                None,
            )

            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data:
                    if not isinstance(asset.state, SheetState):
                        logger.warning(f"Registry MISS! Frame key not found: '{frame_key}'")
                    continue

                # Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
                tex, sx, sy, sw, sl = tex_data
                dx, dy = asset.state.position.x + ox, asset.state.position.y + oy
                dw, dl = sw, sl

                # Strict Culling: Only pass geometry if intersecting the target frame
                if (
                    dx + dw >= pov.x and dx <= pov.x + bounds.w and
                    dy + dl >= pov.y and dy <= pov.y + bounds.l
                ):
                    if submerge_channel is None:
                        active_assets.append((
                            tex, sx, sy, sw, sl,
                            dx, dy, dw, dl,
                            255, 255, 255, 255,
                        ))
                    else:
                        split_y, r, g, b, a = submerge_channel[1]
                        # Upper slice: normal rendering
                        active_assets.append((
                            tex, sx, sy, sw, split_y,
                            dx, dy, dw, split_y,
                            255, 255, 255, 255,
                        ))
                        # Lower slice: submerged texture modulation
                        rem_l = sl - split_y
                        active_assets.append((
                            tex, sx, sy + split_y, sw, rem_l,
                            dx, dy + split_y, dw, rem_l,
                            r, g, b, a,
                        ))

            # 4. Auxiliary Channel Tuples
            for c_type, payload in channels:
                if c_type == ChannelTypes.TINT:
                    cx, cy, cw, cl, r, g, b, a = payload
                    dx = asset.state.position.x + cx
                    dy = asset.state.position.y + cy
                    if (
                        dx + cw >= pov.x and dx <= pov.x + bounds.w and
                        dy + cl >= pov.y and dy <= pov.y + bounds.l
                    ):
                        active_channels.append((
                            c_type,
                            dx,
                            dy,
                            cw, cl,
                            r, g, b, a,
                        ))

        return active_assets, active_channels


    def _widgets(self, menus: List[Menu]) -> None:
        """Helper to collect and superimpose widget primitives for a set of menus."""
        widgets = []
        for menu in menus:
            if menu.widgets:
                widgets.extend(menu.widgets.values())

        primitives = []
        for widget in widgets:
            if isinstance(widget.state, PaneState):
                tex = self.registry.get_canvas(widget.name)
                if tex is not None:
                    primitives.append((
                        tex, 0, 0, tex.w, tex.l,
                        widget.state.position.x, widget.state.position.y,
                        widget.dimensions.w, widget.dimensions.l,
                    ))
                    continue

            frame_keys = widget.frame.keys(widget.id, widget.state)
            for key, ox, oy in frame_keys:
                if key:
                    tex_data = self.registry.image(key)

                    if not tex_data:
                        if not isinstance(widget.state, PaneState):
                            logger.warning(f"Registry MISS: Frame key not found: '{key}'")
                        continue

                    tex, sx, sy, sw, sl = tex_data
                    primitives.append((
                        tex, sx, sy, sw, sl,
                        widget.state.position.x + ox, widget.state.position.y + oy,
                        sw, sl,
                    ))

        if primitives:
            render.superimpose(primitives)


    def camera(
        self,
        focus: Position,
        dim: Dimensions,
    ) -> Position:
        """
        Calculates camera viewport coordinates.
        Centers layers smaller than viewport dimensions via negative offsets.
        """
        if self.boardsize.w < self.screensize.w:
            cam_x = -((self.screensize.w - self.boardsize.w) // 2)
        else:
            cam_x = focus.x + (dim.w // 2) - (self.screensize.w // 2)
            max_x = self.boardsize.w - self.screensize.w
            cam_x = max(0, min(cam_x, max_x))

        if self.boardsize.l < self.screensize.l:
            cam_y = -((self.screensize.l - self.boardsize.l) // 2)
        else:
            cam_y = focus.y + (dim.l // 2) - (self.screensize.l // 2)
            max_y = self.boardsize.l - self.screensize.l
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

    def draw(
        self,
        assets: List[Asset],
        focus: Position,
        dim: Dimensions,
    ) -> None:
        """
        Calculates viewport positioning, culls non-visible items, and routes data to the renderer.
        """
        pov = self.camera(focus, dim)
        active_assets, active_channels = self._assemble(
            assets,
            pov,
            self.screensize,
        )

        logger.debug(
            f"Render Payload: Camera({pov.x}, {pov.y}) | "
            f" Total Assets: {len(active_assets)}"
        )

        # Pass purely native integers to bypass heavy object allocation
        render.render(
            self.bg_canvas,
            self.fg_canvas,
            active_assets,
            pov.x,
            pov.y,
            self.screensize.w,
            self.screensize.l,
        )

        if active_channels:
            render.channel(active_channels, pov.x, pov.y)


    def stamp(self, 
        widget: Asset, 
        content: Optional[Union[str, List[str]]] = None
    ) -> None:
        """
        Allocates PaneState.canvas on demand, constructs the 9-slice backdrop,
        and rasterizes bound text onto the canvas.
        """
        if not isinstance(widget.state, PaneState):
            return

        w, l = widget.dimensions.w, widget.dimensions.l
        if w <= 0 or l <= 0:
            return

        primitives = []
        if widget.id != SystemPanes.TRANSPARENT:
            for base_key, ox, oy in widget.frame.keys(widget.id, widget.state):
                tex_data = self.registry.image(base_key)
                if not tex_data:
                    continue
                base_ptr, sx, sy, sw, sl = tex_data
                primitives.append((base_ptr, sx, sy, sw, sl, ox, oy, sw, sl, 1, 1))

        active_content = widget.state.current() if content is None else content

        # Skip GPU texture allocation for transparent layout containers without text
        if not primitives and not active_content and widget.state.content_function is None:
            return

        tex = self.registry.canvas(widget.name, w, l)

        # 1. Clear target canvas and stamp 9-slice background (if any)
        render.construct(tex, primitives)

        # 2. Rasterize font over the cleared canvas
        if isinstance(active_content, str) and active_content:
            font_key = widget.state.font
            font = self.registry.font(font_key)
            if not font:
                logger.warning(
                    f"Registry MISS: Font '{font_key}' not found for widget '{widget.name}'."
                )
                return
            render.write(
                (tex, 0, 0, tex.w, tex.l, 0, 0, tex.w, tex.l), 
                active_content, 
                font
            )


    def bake(self, menu: Menu) -> None:
        """Initializes and stamps all Pane canvases for a newly unpacked Menu."""
        if not menu.widgets:
            return
        for widget in menu.widgets.values():
            if isinstance(widget.state, PaneState):
                self.stamp(widget)


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


    def reconstruct(self, tiles: List[Asset], calendar: CalendarState) -> None:
        """Bakes updated seasonal tile frames without reallocating GPU texture memory."""
        logger.info(
            f"Screen.reconstruct: Baking seasonal tile canvases for "
            f"season='{calendar.season}', cycle='{calendar.cycle}', period={calendar.period} "
            f"across {len(tiles)} tiles."
        )
        back_tiles, fore_tiles = self._prerender(tiles, calendar)
        render.clear(self.fg_canvas)
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)


    def rebake(
        self,
        tiles: List[Asset],
        boardsize: Dimensions,
        calendar: CalendarState,
        screensize: Dimensions = None,
    ) -> None:
        if self.bg_canvas:
            render.destroy(self.bg_canvas)
        if self.fg_canvas:
            render.destroy(self.fg_canvas)

        if screensize:
            self.screensize = screensize

        self.boardsize = boardsize
        canvas_w = max(boardsize.w, self.screensize.w)
        canvas_l = max(boardsize.l, self.screensize.l)

        is_opaque = len(tiles) == 0
        self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
        self.fg_canvas = render.canvas(canvas_w, canvas_l)

        back_tiles, fore_tiles = self._prerender(tiles, calendar)
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
            target=self.bg_canvas,
        )


    def export_render(
        self,
        out_path: str,
        assets: List[Asset],
        focus: Position,
        fdim: Dimensions,
    ) -> None:
        """
        Draws a composited snapshot of the frame and extracts the VRAM buffer to disk.
        """
        logger.info(f"Extracting VRAM view buffer representing full composition to file system -> {out_path}")
        self.draw(assets, focus, fdim)
        render.save(
            out_path,
            self.screensize.w,
            self.screensize.l,
        )


    def export_map(self, out_path: str, assets: List[Asset]) -> None:
        """
        Draws a composited snapshot of the entire board and extracts the full VRAM buffer to disk,
        bypassing the viewport camera culling.
        """
        logger.info(f"Extracting full board VRAM view buffer to file system -> {out_path}")
        pov = Position(x=0, y=0)
        active_assets, active_channels = self._assemble(
            assets,
            pov,
            self.boardsize,
        )

        # 1. Allocate a temporary canvas matching the absolute board dimensions
        full_target = render.canvas(
            self.boardsize.w,
            self.boardsize.l,
            opaque=True,
        )

        # 2. Render directly onto the transient target instead of the default viewport
        render.render(
            self.bg_canvas,
            self.fg_canvas,
            active_assets,
            pov.x,
            pov.y,
            self.boardsize.w,
            self.boardsize.l,
            target=full_target,  # Invokes the Cython update
        )

        if active_channels:
            render.channel(active_channels, pov.x, pov.y, target=full_target)

        # 3. Read the pixels strictly from the custom target
        render.save(out_path, self.boardsize.w, self.boardsize.l, target=full_target)

        # 4. Explicitly free the GPU memory to prevent memory leaks
        render.destroy(full_target)