# cython: language_level=3
"""
# Ontology: Render

Directly interfaces with SDL2 C-Headers to execute headless rendering, bypassing the Python Global Interpreter Lock (GIL) and ctypes overhead.
"""
# Standard Libraries
import logging

# Cython Libraries
from libs.graphics.registry cimport TexturePtr, TTFFont, TTF_Font, SDL_Color

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

# -----------------------------------------------------------------------------
# Public Python/Cython API
# -----------------------------------------------------------------------------

def get_system_info() -> dict:
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
    """Initializes SDL subsystems."""
    global _window, _canvas_surface, _renderer
    
    if SDL_Init(SDL_INIT_VIDEO) != 0:
        raise RuntimeError(f"SDL_Init Error: {SDL_GetError().decode('utf-8')}")
        
    IMG_Init(IMG_INIT_PNG)
    
    if TTF_Init() != 0:
        raise RuntimeError("TTF_Init Error: Failed to initialize SDL2_ttf.")
    
    if headless:
        _canvas_surface = SDL_CreateRGBSurfaceWithFormat(0, w, l, 32, SDL_PIXELFORMAT_RGBA32)
        if _canvas_surface == NULL:
            raise RuntimeError(f"Failed to create main canvas surface: {SDL_GetError().decode('utf-8')}")
            
        _renderer = SDL_CreateSoftwareRenderer(_canvas_surface)
        if _renderer == NULL:
            raise RuntimeError(f"Failed to create software renderer: {SDL_GetError().decode('utf-8')}")
            
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
                raise RuntimeError(f"Failed to initialize SDL_Renderer fallback: {SDL_GetError().decode('utf-8')}")

def show():
    """Reveals the hidden SDL window and paints a clean black loading screen."""
    if _window != NULL:
        SDL_ShowWindow(_window)
        SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 255)
        SDL_RenderClear(_renderer)
        SDL_RenderPresent(_renderer)
        SDL_PumpEvents()

def canvas(int w, int l, bint opaque=False) -> TexturePtr:
    """Instantiates a blank texture assigned as a rendering target using primitive integers."""
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
    """
    Binds a blank TEXTUREACCESS_TARGET, stamps the base and features onto it, 
    unbinds, and returns the new flattened TexturePtr.
    """
    cdef TexturePtr target = canvas(base_ptr.w, base_ptr.l)

    SDL_SetRenderTarget(_renderer, target.ptr)
    SDL_RenderCopy(_renderer, base_ptr.ptr, NULL, NULL)

    cdef TexturePtr feat
    for feat in feature_ptrs:
        SDL_RenderCopy(_renderer, feat.ptr, NULL, NULL)

    SDL_SetRenderTarget(_renderer, NULL)
    return target

def construct(TexturePtr target, list tiles):
    """
    Constructs the static background entirely in C using zero-allocation primitives.
    tiles format: 
        (TexturePtr, src_x, src_y, src_w, src_l, dst_x, dst_y, dst_w, dst_l, mul_nx, mul_ny)
    """
    logger.debug(f"Constructing layer chunk with {len(tiles)} primitive tile coordinates.")
    
    SDL_SetRenderTarget(_renderer, target.ptr)
    
    cdef SDL_Rect c_src, c_dst
    cdef TexturePtr tex
    cdef int sx, sy, sw, sl, dx, dy, dw, dl, nx, ny
    cdef int i, j
    
    for tile in tiles:
        tex, sx, sy, sw, sl, dx, dy, dw, dl, nx, ny = tile
        
        SDL_SetTextureBlendMode(tex.ptr, SDL_BLENDMODE_NONE)
        
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
) -> int:
    """Determines how many pixels wide a given string is in a given font."""
    if font is None or font.ptr == NULL:
        return 0
        
    cdef int w = 0, h = 0
    cdef bytes b_content = content.encode('utf-8')
    TTF_SizeUTF8(font.ptr, b_content, &w, &h)
    
    return w

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
    tex, sx, sy, sw, sl, dx, dy, dw, dl = asset
    
    cdef int margin_px_w = int(sw * font.margins)
    cdef int margin_px_h = int(sl * font.margins)
    
    cdef int wrap_width = sw - (2 * margin_px_w)
    if wrap_width <= 0:
        wrap_width = 1
        
    cdef bytes b_content = content.encode('utf-8')
    cdef SDL_Surface* text_surface = TTF_RenderUTF8_Blended_Wrapped(
        font.ptr, b_content, font.color, wrap_width
    )
    
    if text_surface == NULL:
        return
        
    cdef SDL_Texture* text_tex = SDL_CreateTextureFromSurface(_renderer, text_surface)
    
    cdef SDL_Rect dst_rect
    dst_rect.y = sy + margin_px_h
    dst_rect.w = text_surface.w
    dst_rect.h = text_surface.h
    
    if font.align_str == "center":
        dst_rect.x = sx + margin_px_w + ((wrap_width - text_surface.w) // 2)
    elif font.align_str == "right":
        dst_rect.x = sx + sw - margin_px_w - text_surface.w
    else:
        dst_rect.x = sx + margin_px_w
        
    # Bake the text string permanently into the asset texture
    SDL_SetRenderTarget(_renderer, tex.ptr)
    SDL_SetTextureBlendMode(text_tex, SDL_BLENDMODE_BLEND)
    SDL_RenderCopy(_renderer, text_tex, NULL, &dst_rect)
    SDL_SetRenderTarget(_renderer, NULL)
    
    SDL_DestroyTexture(text_tex)
    SDL_FreeSurface(text_surface)

def render(
    TexturePtr background, 
    TexturePtr foreground, 
    list assets, 
    int cam_x,
    int cam_y, 
    int screen_w, 
    int screen_l
):
    """
    Executes the active frame render passing flat coordinates to bypass Python object allocations.
    assets format: (TexturePtr, src_x, src_y, src_w, src_l, dst_x, dst_y, dst_w, dst_l)
    """
    SDL_RenderClear(_renderer)
    cdef SDL_Rect c_src, c_dst, bg_src, bg_dst
    cdef TexturePtr tex_wrapper
    cdef int sx, sy, sw, sl, dx, dy, dw, dl

    if background is not None:
        bg_src.x = cam_x
        bg_src.y = cam_y
        bg_src.w = screen_w
        bg_src.h = screen_l

        bg_dst.x = 0
        bg_dst.y = 0
        bg_dst.w = screen_w
        bg_dst.h = screen_l

        bg_status = SDL_RenderCopy(_renderer, background.ptr, &bg_src, &bg_dst)
        if bg_status < 0:
            logger.error(f"Background RenderCopy failed: {SDL_GetError().decode('utf-8')} "
                        f"| Texture Size: {background.w}x{background.l} "
                        f"| Requested Source: {bg_src.w}x{bg_src.h}")

    for asset in assets:
        tex_wrapper, sx, sy, sw, sl, dx, dy, dw, dl = asset
        
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sl
        
        c_dst.x = dx - cam_x
        c_dst.y = dy - cam_y
        c_dst.w, c_dst.h = dw, dl
            
        SDL_RenderCopy(_renderer, tex_wrapper.ptr, &c_src, &c_dst)

    if foreground is not None:
        bg_src.x = cam_x
        bg_src.y = cam_y
        bg_src.w = screen_w
        bg_src.h = screen_l
        
        bg_dst.x = 0
        bg_dst.y = 0
        bg_dst.w = screen_w
        bg_dst.h = screen_l
                    
        SDL_RenderCopy(_renderer, foreground.ptr, &bg_src, &bg_dst)
                    
    SDL_RenderPresent(_renderer)
    SDL_PumpEvents()

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