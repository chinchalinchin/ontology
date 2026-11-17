# cython: language_level=3
"""
@domain.system
@app.library
@modality.appearance
@workflow.rendering

# Ontology: Libraries - libs.graphics.render

SDL Interfaces for rendering Assets.
"""
# Standard Libraries
import logging

# Cython Libraries
from libs.graphics.registry cimport (
    Registry,
    TexturePtr, 
    TTFFont, 
    TTF_Font, 
    SDL_Color
)
from libs.core.models cimport (
    Position, 
    Dimensions
)

logger = logging.getLogger("libs.graphics.render")

# -----------------------------------------------------------------------------
# C-Header Definitions
# -----------------------------------------------------------------------------
cdef extern from "SDL2/SDL.h":
    ctypedef struct SDL_Window:
        pass
    ctypedef struct SDL_Renderer:
        pass
    ctypedef struct SDL_Texture:
        pass
    ctypedef struct SDL_Surface:
        void* pixels
        int pitch
        int w
        int h
    ctypedef struct SDL_RendererInfo:
        const char *name
        unsigned int flags
        unsigned int num_texture_formats
        unsigned int texture_formats[16]
        int max_texture_width
        int max_texture_height
    ctypedef struct SDL_Rect:
        int x
        int y
        int w
        int h

    int SDL_GetRendererInfo(SDL_Renderer* renderer, SDL_RendererInfo* info)
    const char* SDL_GetCurrentVideoDriver()
    const char* SDL_GetError()
    
    int SDL_Init(unsigned int flags)
    void SDL_Quit()

    SDL_Window* SDL_CreateWindow(
        const char* title, 
        int x, 
        int y, 
        int w, 
        int h, 
        unsigned int flags
    )
    void SDL_DestroyWindow(SDL_Window* window)
    void SDL_ShowWindow(SDL_Window* window)

    SDL_Renderer* SDL_CreateRenderer(
        SDL_Window* window, 
        int index, 
        unsigned int flags
    )
    SDL_Renderer* SDL_CreateSoftwareRenderer(SDL_Surface* surface)
    void SDL_DestroyRenderer(SDL_Renderer* renderer)
    
    SDL_Texture* SDL_CreateTexture(
        SDL_Renderer* renderer, 
        unsigned int format, 
        int access, 
        int w, 
        int h
    )
    SDL_Texture* SDL_CreateTextureFromSurface(
        SDL_Renderer* renderer, 
        SDL_Surface* surface
    )
    int SDL_SetRenderTarget(
        SDL_Renderer* renderer, 
        SDL_Texture* texture
    )
    
    int SDL_RenderClear(SDL_Renderer* renderer)
    int SDL_RenderCopy(
        SDL_Renderer* renderer, 
        SDL_Texture* texture, 
        const SDL_Rect* srcrect, 
        const SDL_Rect* dstrect
    )
    void SDL_RenderPresent(SDL_Renderer* renderer)
    void SDL_PumpEvents()
    int SDL_RenderReadPixels(
        SDL_Renderer* renderer, 
        const SDL_Rect* rect, 
        unsigned int format, 
        void* pixels, 
        int pitch
    )
    int SDL_SetRenderDrawBlendMode(
        SDL_Renderer* renderer, 
        int blendMode
    )
    int SDL_RenderFillRect(
        SDL_Renderer* renderer, 
        const SDL_Rect* rect
    )

    SDL_Surface* SDL_CreateRGBSurfaceWithFormat(
        unsigned int flags, 
        int width, 
        int height, 
        int depth, 
        unsigned int format
    )
    void SDL_FreeSurface(SDL_Surface* surface)

    int SDL_SetTextureBlendMode(
        SDL_Texture* texture, 
        int blendMode
    )
    int SDL_SetRenderDrawColor(
        SDL_Renderer* renderer, 
        int r, 
        int g, 
        int b, 
        int a
    )
    int SDL_SetTextureColorMod(
        SDL_Texture* texture, 
        unsigned char r, 
        unsigned char g, 
        unsigned char b
    )
    int SDL_SetTextureAlphaMod(
        SDL_Texture* texture, 
        unsigned char alpha
    )
    unsigned int SDL_INIT_VIDEO
    unsigned int SDL_PIXELFORMAT_RGBA32

    unsigned int SDL_WINDOW_SHOWN
    unsigned int SDL_WINDOW_HIDDEN
    unsigned int SDL_RENDERER_ACCELERATED
    unsigned int SDL_RENDERER_SOFTWARE

    int SDL_TEXTUREACCESS_TARGET
    int SDL_BLENDMODE_BLEND
    int SDL_BLENDMODE_NONE

cdef extern from "SDL2/SDL_image.h":
    int IMG_Init(int flags)
    void IMG_Quit()
    int IMG_SavePNG(SDL_Surface* surface, const char* file)
    
    int IMG_INIT_PNG

cdef extern from "SDL2/SDL_ttf.h":
    int TTF_Init()
    void TTF_Quit()
    SDL_Surface* TTF_RenderUTF8_Blended_Wrapped(TTF_Font* font, const char* text, SDL_Color fg, unsigned int wrapLength)
    int TTF_SizeUTF8(TTF_Font* font, const char* text, int* w, int* h)

# -----------------------------------------------------------------------------
# Global Singletons
# -----------------------------------------------------------------------------
cdef SDL_Surface* _canvas_surface = NULL
cdef SDL_Window* _window = NULL
# Note: _renderer is maintained in render.pxd

# Module-level string constants (avoids Enum.__get__ in inner loop)
cdef str _CAT_TILES = "tiles"
cdef str _INST_FLUIDS = "fluids"
cdef str _INST_SHORELINES = "shorelines"
cdef int _CH_TINT = 0       # ChannelTypes.TINT.value
cdef int _CH_SUBMERGE = 1   # ChannelTypes.SUBMERGE.value
cdef int _CULL_MARGIN = 64

# -----------------------------------------------------------------------------
# Public Python/Cython API
# -----------------------------------------------------------------------------

def sysinfo() -> dict:
    """Retrieves low-level SDL context and driver details."""
    cdef SDL_RendererInfo info
    cdef dict sys_info = {
        "video_driver": "Unknown",
        "renderer_name": "Unknown",
        "max_texture_width": 0,
        "max_texture_height": 0,
        "accelerated": False
    }
    
    if SDL_GetCurrentVideoDriver() != NULL:
        sys_info["video_driver"] = SDL_GetCurrentVideoDriver().decode('utf-8')
        
    if _renderer != NULL:
        if SDL_GetRendererInfo(_renderer, &info) == 0:
            sys_info["renderer_name"] = info.name.decode('utf-8')
            sys_info["max_texture_width"] = info.max_texture_width
            sys_info["max_texture_height"] = info.max_texture_height
            sys_info["accelerated"] = bool(info.flags & SDL_RENDERER_ACCELERATED)
            
    return sys_info


def init(int w, int l, bint headless=True):
    """
    Initializes SDL subsystems.
    """
    global _window, _canvas_surface, _renderer
    
    if SDL_Init(SDL_INIT_VIDEO) != 0:
        raise RuntimeError(f"SDL_Init Error: {SDL_GetError().decode('utf-8')}")
        
    IMG_Init(IMG_INIT_PNG)
    
    if TTF_Init() != 0:
        raise RuntimeError("TTF_Init Error: Failed to initialize SDL2_ttf.")
    
    if headless:
        _canvas_surface = SDL_CreateRGBSurfaceWithFormat(0, w, l, 32, SDL_PIXELFORMAT_RGBA32)
        if _canvas_surface == NULL:
            raise RuntimeError(f"Failed to create canvas: {SDL_GetError().decode('utf-8')}")
            
        _renderer = SDL_CreateSoftwareRenderer(_canvas_surface)
        if _renderer == NULL:
            raise RuntimeError(f"Failed to create renderer: {SDL_GetError().decode('utf-8')}")
            
    else:
        _window = SDL_CreateWindow(b"Game", 100, 100, w, l, SDL_WINDOW_HIDDEN)
        if _window == NULL:
            raise RuntimeError(f"Failed to create window: {SDL_GetError().decode('utf-8')}")
            
        _renderer = SDL_CreateRenderer(_window, -1, SDL_RENDERER_ACCELERATED)
        
        if _renderer == NULL:
            logger.info("Using SDL_RENDERER_SOFTWARE")
            logger.warning(f"Accelerated renderer failed: {SDL_GetError().decode('utf-8')}. Falling back to software.")
            _renderer = SDL_CreateRenderer(_window, -1, SDL_RENDERER_SOFTWARE)
            
            if _renderer == NULL:
                raise RuntimeError(f"Failed to initialize SDL_Renderer: {SDL_GetError().decode('utf-8')}")


def show():
    """
    Reveals the hidden SDL window and paints a clean black loading screen.
    """
    if _window != NULL:
        SDL_ShowWindow(_window)
        SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 255)
        SDL_RenderClear(_renderer)
        SDL_RenderPresent(_renderer)
        SDL_PumpEvents()


def clear(TexturePtr target=None):
    """
    Clears the active backbuffer or a specific target canvas texture.
    """
    if target is not None:
        if target.ptr != NULL:
            SDL_SetRenderTarget(_renderer, target.ptr)
            SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 0)
            SDL_RenderClear(_renderer)
            SDL_SetRenderTarget(_renderer, NULL)
        return

    SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 255)
    SDL_RenderClear(_renderer)


def present():
    """
    """
    SDL_RenderPresent(_renderer)
    SDL_PumpEvents()


def destroy(TexturePtr target):
    """
    Explicitly destroys an SDL_Texture to free VRAM immediately, 
    bypassing Python's non-deterministic garbage collector.
    """
    if target is not None and target.ptr != NULL:
        if _renderer != NULL:
            SDL_DestroyTexture(target.ptr)
        target.ptr = NULL


def superimpose(list assets):
    """
    """
    cdef SDL_Rect c_src, c_dst
    cdef TexturePtr tex_wrapper
    cdef int sx, sy, sw, sl, dx, dy, dw, dl

    for asset in assets:
        tex_wrapper, sx, sy, sw, sl, dx, dy, dw, dl = asset
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sl
        c_dst.x = dx
        c_dst.y = dy
        c_dst.w, c_dst.h = dw, dl
        SDL_RenderCopy(_renderer, tex_wrapper.ptr, &c_src, &c_dst)


def dim(int r=0, int g=0, int b=0, int a=160):
    """
    Draws a full-screen alpha-blended rectangle over the backbuffer.
    """
    SDL_SetRenderDrawBlendMode(_renderer, SDL_BLENDMODE_BLEND)
    SDL_SetRenderDrawColor(_renderer, r, g, b, a)
    SDL_RenderFillRect(_renderer, NULL)

    
def canvas(int w, int l, bint opaque=False) -> TexturePtr:
    """
    Instantiates a blank texture assigned as a rendering target using primitive integers.
    """
    logger.debug(f"Generating blank VRAM render target canvas size: {w}x{l} | Opaque: {opaque}")
    cdef SDL_Texture* tex = SDL_CreateTexture(
        _renderer, 
        SDL_PIXELFORMAT_RGBA32, 
        SDL_TEXTUREACCESS_TARGET, 
        w, 
        l
    )
    if tex == NULL:
        raise RuntimeError("Failed to create GPU render target.")
    
    # 1. Enable Alpha Blending
    SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND)

    # 2. Clear VRAM garbage with pure transparency or solid black
    SDL_SetRenderTarget(_renderer, tex)
    if opaque:
        SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 255)
    else:
        SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 0)
    
    SDL_RenderClear(_renderer)
    SDL_SetRenderTarget(_renderer, NULL)

    cdef TexturePtr wrapper = TexturePtr()
    wrapper.ptr = tex
    wrapper.w = w
    wrapper.l = l
    return wrapper


def compose(TexturePtr base_ptr, list feature_ptrs) -> TexturePtr:
    logger.debug(f"[TELEMETRY] Compositing base texture ({base_ptr.w}x{base_ptr.l}) with {len(feature_ptrs)} features.")
    
    cdef TexturePtr target = canvas(base_ptr.w, base_ptr.l)

    SDL_SetRenderTarget(_renderer, target.ptr)
    
    if SDL_RenderCopy(_renderer, base_ptr.ptr, NULL, NULL) < 0:
        logger.error(f"[TELEMETRY] Compose Base Copy Error: {SDL_GetError().decode('utf-8')}")

    cdef TexturePtr feat
    for i, feat in enumerate(feature_ptrs):
        if SDL_RenderCopy(_renderer, feat.ptr, NULL, NULL) < 0:
            logger.error(f"[TELEMETRY] Compose Feature {i} Copy Error: {SDL_GetError().decode('utf-8')}")

    SDL_SetRenderTarget(_renderer, NULL)
    logger.debug(f"[TELEMETRY] Composition complete.")
    return target

def construct(TexturePtr target, list tiles, bint clear_target=True):
    """
    Constructs a static layer or UI canvas in C using zero-allocation primitives.
    tiles format: 
        (TexturePtr, src_x, src_y, src_w, src_l, dst_x, dst_y, dst_w, dst_l, mul_nx, mul_ny)
    """
    if target is None or target.ptr == NULL:
        return

    SDL_SetRenderTarget(_renderer, target.ptr)

    if clear_target:
        SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 0)
        SDL_RenderClear(_renderer)

    cdef SDL_Rect c_src, c_dst
    cdef TexturePtr tex
    cdef int sx, sy, sw, sl, dx, dy, dw, dl, nx, ny
    cdef int i, j

    for tile in tiles:
        tex, sx, sy, sw, sl, dx, dy, dw, dl, nx, ny = tile

        SDL_SetTextureBlendMode(tex.ptr, SDL_BLENDMODE_BLEND)

        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sl
        c_dst.w, c_dst.h = dw, dl

        for i in range(nx):
            for j in range(ny):
                c_dst.x = dx + (i * dw)
                c_dst.y = dy + (j * dl)
                SDL_RenderCopy(_renderer, tex.ptr, &c_src, &c_dst)

    SDL_SetRenderTarget(_renderer, NULL)


def measure(
    str content, 
    TTFFont font
) -> tuple:
    """
    Determines how many pixels wide and high a given string is in a given font.
    """
    if font is None or font.ptr == NULL:
        return (0, 0)
        
    cdef int w = 0, h = 0
    cdef bytes b_content = content.encode('utf-8')
    TTF_SizeUTF8(font.ptr, b_content, &w, &h)
    
    return (w, h)


def write(
    tuple asset, 
    str content, 
    TTFFont font
):
    """
    Renders text directly onto an asset's texture target. 
    asset format: (TexturePtr, src_x, src_y, src_w, src_l, dst_x, dst_y, dst_w, dst_l)
    """
    if font is None or font.ptr == NULL:
        raise RuntimeError("Invalid or uninitialized font provided.")
        
    cdef TexturePtr tex
    cdef int sx, sy, sw, sl, dx, dy, dw, dl
    cdef int margin_px_w, margin_px_h, wrap_width
    cdef bytes b_content
    cdef SDL_Surface* text_surface = NULL
    cdef SDL_Texture* text_tex = NULL
    cdef SDL_Surface* outline_surface = NULL
    cdef SDL_Texture* outline_tex = NULL
    cdef SDL_Rect dst_rect
    cdef SDL_Rect outline_rect

    tex, sx, sy, sw, sl, dx, dy, dw, dl = asset
    
    margin_px_w = int(sw * font.margins)
    margin_px_h = int(sl * font.margins)
    
    wrap_width = sw - (2 * margin_px_w)
    if wrap_width <= 0:
        wrap_width = 1
        
    b_content = content.encode('utf-8')
    text_surface = TTF_RenderUTF8_Blended_Wrapped(
        font.ptr, b_content, font.color, wrap_width
    )
    
    if text_surface == NULL:
        return
        
    text_tex = SDL_CreateTextureFromSurface(_renderer, text_surface)
    if text_tex == NULL:
        SDL_FreeSurface(text_surface)
        return
        
    dst_rect.y = margin_px_h    
    dst_rect.w = text_surface.w
    dst_rect.h = text_surface.h
    
    if font.align_str == "center":
        dst_rect.x = sx + margin_px_w + ((wrap_width - text_surface.w) // 2)
    elif font.align_str == "right":
        dst_rect.x = sx + sw - margin_px_w - text_surface.w
    else:
        dst_rect.x = sx + margin_px_w

    # Pass 1: Render outline behind the primary text
    if font.outline_ptr != NULL and font.outline_width > 0:
        outline_surface = TTF_RenderUTF8_Blended_Wrapped(
            font.outline_ptr, b_content, font.outline_color, wrap_width + (2 * font.outline_width)
        )
        if outline_surface != NULL:
            outline_tex = SDL_CreateTextureFromSurface(_renderer, outline_surface)
            outline_rect.x = dst_rect.x - font.outline_width
            outline_rect.y = dst_rect.y - font.outline_width
            outline_rect.w = outline_surface.w
            outline_rect.h = outline_surface.h

    # Bake onto the target texture
    SDL_SetRenderTarget(_renderer, tex.ptr)

    if outline_tex != NULL:
        SDL_SetTextureBlendMode(outline_tex, SDL_BLENDMODE_BLEND)
        SDL_RenderCopy(_renderer, outline_tex, NULL, &outline_rect)

    SDL_SetTextureBlendMode(text_tex, SDL_BLENDMODE_BLEND)
    SDL_RenderCopy(_renderer, text_tex, NULL, &dst_rect)

    SDL_SetRenderTarget(_renderer, NULL)
    
    # Cleanup surfaces and intermediate textures
    if outline_tex != NULL:
        SDL_DestroyTexture(outline_tex)
    if outline_surface != NULL:
        SDL_FreeSurface(outline_surface)

    SDL_DestroyTexture(text_tex)
    SDL_FreeSurface(text_surface)
                 

cpdef tuple assemble(
    list assets,
    Registry registry,
    Position pov,
    Dimensions bounds
):
    """
    Cythonized broad-phase viewport cull, 4-tuple perspective sort, and narrow-phase
    primitive/channel assembly.
    """
    cdef int pov_x = pov.x
    cdef int pov_y = pov.y
    cdef int bounds_w = bounds.w
    cdef int bounds_l = bounds.l

    cdef int min_x = pov_x - _CULL_MARGIN
    cdef int min_y = pov_y - _CULL_MARGIN
    cdef int max_x = pov_x + bounds_w + _CULL_MARGIN
    cdef int max_y = pov_y + bounds_l + _CULL_MARGIN
    cdef int view_max_x = pov_x + bounds_w
    cdef int view_max_y = pov_y + bounds_l

    cdef list sortable = []
    cdef object asset, state, props, taxonomy
    cdef str cat, inst
    cdef Position pos
    cdef Dimensions dim
    cdef int px, py, dw, dl, elev, sub, anchor, prio, ground_y
    cdef int idx = 0

    # 1. Broad-phase filter + sort-key tuple construction in a single C loop
    for asset in assets:
        taxonomy = asset.taxonomy
        cat = <str>taxonomy.category
        if cat == _CAT_TILES:
            continue

        state = asset.state
        props = asset.properties
        pos = <Position>state.position
        dim = <Dimensions>props.dimensions

        px = pos.x
        py = pos.y
        dw = dim.w if dim is not None else 0
        dl = dim.l if dim is not None else 0

        inst = <str>taxonomy.instance
        if inst != _INST_FLUIDS and inst != _INST_SHORELINES:
            if px + dw < min_x or px > max_x or py + dl < min_y or py > max_y:
                continue

        elev = state.elevation if state.elevation is not None else 0
        sub = asset.substrate
        anchor = state.anchor
        prio = props.priority
        ground_y = py + dl + anchor

        # Decorate with C-computed sort key (avoids Python key= callback per element)
        sortable.append((elev, sub, ground_y, prio, idx, px, py, asset))
        idx += 1

    # 2. Native tuple sort
    sortable.sort()

    # 3. Narrow-phase frame resolution and primitive assembly
    cdef list active_assets = []
    cdef list active_channels = []
    cdef tuple entry, fk_tuple, tex_data, ch_op, sub_payload, tint_payload
    cdef list frame_keys, channels
    cdef str asset_id, frame_key
    cdef int ox, oy, sx, sy, sw, sl, dx, dy
    cdef int split_y, local_split, rem_l, r, g, b, a
    cdef int c_type, cx, cy, cw, cl
    cdef bint has_submerge
    cdef TexturePtr tex

    for entry in sortable:
        px = entry[5]
        py = entry[6]
        asset = entry[7]
        state = asset.state
        props = asset.properties
        asset_id = <str>asset.taxonomy.id

        frame_keys = asset.frame.keys(asset_id, state)
        channels = asset.frame.channels(asset_id, state, props)

        has_submerge = False
        for ch_op in channels:
            if <int>ch_op[0] == _CH_SUBMERGE:
                sub_payload = <tuple>ch_op[1]
                split_y = sub_payload[0]
                r = sub_payload[1]
                g = sub_payload[2]
                b = sub_payload[3]
                a = sub_payload[4]
                has_submerge = True
                break

        for fk_tuple in frame_keys:
            frame_key = <str>fk_tuple[0]
            ox = fk_tuple[1]
            oy = fk_tuple[2]

            tex_data = registry.image(frame_key)
            if tex_data is None:
                continue

            tex = <TexturePtr>tex_data[0]
            sx = tex_data[1]
            sy = tex_data[2]
            sw = tex_data[3]
            sl = tex_data[4]

            dx = px + ox
            dy = py + oy

            if dx + sw >= pov_x and dx <= view_max_x and dy + sl >= pov_y and dy <= view_max_y:
                if not has_submerge:
                    active_assets.append((
                        tex, sx, sy, sw, sl,
                        dx, dy, sw, sl,
                        255, 255, 255, 255,
                    ))
                else:
                    local_split = split_y - oy
                    if local_split >= sl:
                        active_assets.append((
                            tex, sx, sy, sw, sl,
                            dx, dy, sw, sl,
                            255, 255, 255, 255,
                        ))
                    elif local_split <= 0:
                        active_assets.append((
                            tex, sx, sy, sw, sl,
                            dx, dy, sw, sl,
                            r, g, b, a,
                        ))
                    else:
                        rem_l = sl - local_split
                        active_assets.append((
                            tex, sx, sy, sw, local_split,
                            dx, dy, sw, local_split,
                            255, 255, 255, 255,
                        ))
                        active_assets.append((
                            tex, sx, sy + local_split, sw, rem_l,
                            dx, dy + local_split, sw, rem_l,
                            r, g, b, a,
                        ))

        for ch_op in channels:
            c_type = ch_op[0]
            if c_type == _CH_TINT:
                tint_payload = <tuple>ch_op[1]
                cx = tint_payload[0]
                cy = tint_payload[1]
                cw = tint_payload[2]
                cl = tint_payload[3]
                r = tint_payload[4]
                g = tint_payload[5]
                b = tint_payload[6]
                a = tint_payload[7]
                dx = px + cx
                dy = py + cy
                if dx + cw >= pov_x and dx <= view_max_x and dy + cl >= pov_y and dy <= view_max_y:
                    active_channels.append((c_type, dx, dy, cw, cl, r, g, b, a))

    return active_assets, active_channels


def render(
    TexturePtr background, 
    TexturePtr foreground, 
    list assets, 
    int cam_x, 
    int cam_y, 
    int screen_w, 
    int screen_l, 
    TexturePtr target=None
):
    """
    Executes the active frame render passing flat coordinates to bypass Python object allocations.
    assets format: (TexturePtr, src_x, src_y, src_w, src_l, dst_x, dst_y, dst_w, dst_l, r, g, b, a)
    """
    if target is not None:
        SDL_SetRenderTarget(_renderer, target.ptr)

    cdef SDL_Rect c_src, c_dst, bg_src, bg_dst
    cdef TexturePtr tex_wrapper
    cdef int sx, sy, sw, sl, dx, dy, dw, dl, r, g, b, a

    if background is not None:
        bg_src.x = cam_x if cam_x >= 0 else 0
        bg_src.y = cam_y if cam_y >= 0 else 0
        bg_dst.x = 0 if cam_x >= 0 else -cam_x
        bg_dst.y = 0 if cam_y >= 0 else -cam_y
        bg_src.w = min(screen_w - bg_dst.x, background.w - bg_src.x)
        bg_src.h = min(screen_l - bg_dst.y, background.l - bg_src.y)
        bg_dst.w = bg_src.w
        bg_dst.h = bg_src.h

        SDL_RenderCopy(_renderer, background.ptr, &bg_src, &bg_dst)

    for asset in assets:
        tex_wrapper, sx, sy, sw, sl, dx, dy, dw, dl, r, g, b, a = asset
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sl
        c_dst.x = dx - cam_x
        c_dst.y = dy - cam_y
        c_dst.w = dw
        c_dst.h = dl

        if r != 255 or g != 255 or b != 255:
            SDL_SetTextureColorMod(tex_wrapper.ptr, r, g, b)
        if a != 255:
            SDL_SetTextureAlphaMod(tex_wrapper.ptr, a)

        SDL_RenderCopy(_renderer, tex_wrapper.ptr, &c_src, &c_dst)

        if r != 255 or g != 255 or b != 255:
            SDL_SetTextureColorMod(tex_wrapper.ptr, 255, 255, 255)
        if a != 255:
            SDL_SetTextureAlphaMod(tex_wrapper.ptr, 255)

    if foreground is not None:
        bg_src.x = cam_x if cam_x >= 0 else 0
        bg_src.y = cam_y if cam_y >= 0 else 0
        bg_dst.x = 0 if cam_x >= 0 else -cam_x
        bg_dst.y = 0 if cam_y >= 0 else -cam_y
        bg_src.w = min(screen_w - bg_dst.x, foreground.w - bg_src.x)
        bg_src.h = min(screen_l - bg_dst.y, foreground.l - bg_src.y)
        bg_dst.w = bg_src.w
        bg_dst.h = bg_src.h

        SDL_RenderCopy(_renderer, foreground.ptr, &bg_src, &bg_dst)

    if target is not None:
        SDL_SetRenderTarget(_renderer, NULL)


def channel(list channel_ops, int cam_x, int cam_y, TexturePtr target=None):
    """
    Renders auxiliary channel passes (tints, highlights) directly over the backbuffer.
    channel_ops format: (c_type, dx, dy, dw, dl, r, g, b, a)
    """
    cdef SDL_Rect rect
    cdef int c_type, dx, dy, dw, dl, r, g, b, a

    if target is not None:
        SDL_SetRenderTarget(_renderer, target.ptr)

    SDL_SetRenderDrawBlendMode(_renderer, SDL_BLENDMODE_BLEND)

    for op in channel_ops:
        c_type, dx, dy, dw, dl, r, g, b, a = op
        rect.x = dx - cam_x
        rect.y = dy - cam_y
        rect.w = dw
        rect.h = dl

        if c_type == 0:  # TINT / Fill Rect
            SDL_SetRenderDrawColor(_renderer, r, g, b, a)
            SDL_RenderFillRect(_renderer, &rect)

    if target is not None:
        SDL_SetRenderTarget(_renderer, NULL)
              
              
def save(str filename, int w, int l, TexturePtr target=None):
    """Extracts pixel data from the active hardware renderer or a specific texture to disk."""
    cdef bytes b_filename = filename.encode('utf-8')
    
    logger.debug(f"Saving SDL surface: {filename} bounds: {w}x{l} targeting {'TexturePtr' if target else 'Viewport Default'}")

    cdef SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormat(
        0, w, l, 32, SDL_PIXELFORMAT_RGBA32
    )
    
    if surface == NULL:
        raise RuntimeError("Failed to create SDL_Surface for saving PNG.")
        
    if target is not None:
        SDL_SetRenderTarget(_renderer, target.ptr)
        
    SDL_RenderReadPixels(
        _renderer, NULL, SDL_PIXELFORMAT_RGBA32, surface.pixels, surface.pitch
    )
    IMG_SavePNG(surface, b_filename)
    SDL_FreeSurface(surface)

    if target is not None:
        SDL_SetRenderTarget(_renderer, NULL)


def quit_sdl():
    """Safely terminate SDL bindings."""
    global _canvas_surface, _window
    global _renderer
    
    if _renderer != NULL:
        SDL_DestroyRenderer(_renderer)
        _renderer = NULL
    if _window != NULL:
        SDL_DestroyWindow(_window)
        _window = NULL
    if _canvas_surface != NULL:
        SDL_FreeSurface(_canvas_surface)
        _canvas_surface = NULL
        
    TTF_Quit()
    IMG_Quit()
    SDL_Quit()