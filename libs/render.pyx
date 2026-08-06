# cython: language_level=3
"""
# Ontology: Native Renderer (Cython)

Directly interfaces with SDL2 C-Headers to execute hardware-accelerated rendering, 
bypassing the Python Global Interpreter Lock (GIL) and ctypes overhead.
"""

from libs.registry cimport TexturePtr

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
        
    ctypedef struct SDL_Rect:
        int x
        int y
        int w
        int h
        
    int SDL_Init(unsigned int flags)
    void SDL_Quit()
    
    SDL_Window* SDL_CreateWindow(const char* title, int x, int y, int w, int h, unsigned int flags)
    void SDL_DestroyWindow(SDL_Window* window)
    
    SDL_Renderer* SDL_CreateRenderer(SDL_Window* window, int index, unsigned int flags)
    void SDL_DestroyRenderer(SDL_Renderer* renderer)
    
    SDL_Texture* SDL_CreateTexture(SDL_Renderer* renderer, unsigned int format, int access, int w, int h)
    int SDL_SetRenderTarget(SDL_Renderer* renderer, SDL_Texture* texture)
    
    int SDL_RenderClear(SDL_Renderer* renderer)
    int SDL_RenderCopy(SDL_Renderer* renderer, SDL_Texture* texture, const SDL_Rect* srcrect, const SDL_Rect* dstrect)
    void SDL_RenderPresent(SDL_Renderer* renderer)
    void SDL_PumpEvents()
    int SDL_RenderReadPixels(SDL_Renderer* renderer, const SDL_Rect* rect, unsigned int format, void* pixels, int pitch)
    
    SDL_Surface* SDL_CreateRGBSurfaceWithFormat(unsigned int flags, int width, int height, int depth, unsigned int format)
    void SDL_FreeSurface(SDL_Surface* surface)
    
    unsigned int SDL_INIT_VIDEO
    unsigned int SDL_WINDOW_HIDDEN
    unsigned int SDL_RENDERER_ACCELERATED
    int SDL_TEXTUREACCESS_TARGET
    unsigned int SDL_PIXELFORMAT_RGBA32

    int SDL_SetTextureBlendMode(SDL_Texture* texture, int blendMode)
    int SDL_SetRenderDrawColor(SDL_Renderer* renderer, int r, int g, int b, int a)
    int SDL_BLENDMODE_BLEND

cdef extern from "SDL2/SDL_image.h":
    int IMG_Init(int flags)
    void IMG_Quit()
    int IMG_SavePNG(SDL_Surface* surface, const char* file)
    
    int IMG_INIT_PNG

# -----------------------------------------------------------------------------
# Global Singletons
# -----------------------------------------------------------------------------
cdef SDL_Window* _window = NULL
# Note: _renderer is maintained in render.pxd

# -----------------------------------------------------------------------------
# Public Python/Cython API
# -----------------------------------------------------------------------------

def init():
    """Initializes the SDL subsystems and instantiates the hidden hardware renderer."""
    global _window
    
    SDL_Init(SDL_INIT_VIDEO)
    IMG_Init(IMG_INIT_PNG)
    
    _window = SDL_CreateWindow(b"Ontology Offscreen Canvas", 0, 0, 800, 600, SDL_WINDOW_HIDDEN)
    
    # Assign to global cython context mapped from .pxd
    global _renderer
    _renderer = SDL_CreateRenderer(_window, -1, SDL_RENDERER_ACCELERATED)
    
    if _renderer == NULL:
        raise RuntimeError("Failed to initialize hardware-accelerated SDL_Renderer.")

def canvas(int w, int h) -> TexturePtr:
    """Instantiates a blank texture assigned as an accelerated rendering target using primitive integers."""
    cdef SDL_Texture* tex = SDL_CreateTexture(
        _renderer, 
        SDL_PIXELFORMAT_RGBA32, 
        SDL_TEXTUREACCESS_TARGET, 
        w, h
    )
    if tex == NULL:
        raise RuntimeError("Failed to create GPU render target.")
    
    # 1. Enable Alpha Blending
    SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND)

    # 2. Clear VRAM garbage with pure transparency
    SDL_SetRenderTarget(_renderer, tex)
    SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 0)
    SDL_RenderClear(_renderer)
    SDL_SetRenderTarget(_renderer, NULL)

    cdef TexturePtr wrapper = TexturePtr()
    wrapper.ptr = tex
    wrapper.w = w
    wrapper.h = h
    return wrapper

def compose(TexturePtr base_ptr, list feature_ptrs) -> TexturePtr:
    """
    Binds a blank TEXTUREACCESS_TARGET, stamps the base and features onto it, 
    unbinds, and returns the new flattened TexturePtr.
    """
    cdef TexturePtr target = canvas(base_ptr.w, base_ptr.h)

    # 1. Bind new target texture
    SDL_SetRenderTarget(_renderer, target.ptr)

    # 2. Draw base foundation
    SDL_RenderCopy(_renderer, base_ptr.ptr, NULL, NULL)

    # 3. Stack arbitrary features on top
    cdef TexturePtr feat
    for feat in feature_ptrs:
        SDL_RenderCopy(_renderer, feat.ptr, NULL, NULL)

    # 4. Unbind render target
    SDL_SetRenderTarget(_renderer, NULL)

    return target

def construct(TexturePtr target, list tiles):
    """
    Constructs the static background entirely in C using zero-allocation primitives.
    tiles format: (TexturePtr, src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h, mul_nx, mul_ny)
    """
    SDL_SetRenderTarget(_renderer, target.ptr)
    
    cdef SDL_Rect c_src, c_dst
    cdef TexturePtr tex
    cdef int sx, sy, sw, sh, dx, dy, dw, dh, nx, ny
    cdef int i, j
    
    for tile in tiles:
        # Unpack flat tuples cleanly onto the C-stack
        tex, sx, sy, sw, sh, dx, dy, dw, dh, nx, ny = tile
        
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sh
        c_dst.w, c_dst.h = dw, dh
        
        for i in range(nx):
            for j in range(ny):
                c_dst.x = dx + (i * dw)
                c_dst.y = dy + (j * dh)
                SDL_RenderCopy(_renderer, tex.ptr, &c_src, &c_dst)
                
    SDL_SetRenderTarget(_renderer, NULL)
    
def render(TexturePtr background, list assets, int cam_x, int cam_y, int screen_w, int screen_h):
    """
    Executes the active frame render passing flat coordinates to bypass Python object allocations.
    assets format: (TexturePtr, src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h)
    """
    SDL_RenderClear(_renderer)
    cdef SDL_Rect c_src, c_dst, bg_src
    cdef TexturePtr tex_wrapper
    cdef int sx, sy, sw, sh, dx, dy, dw, dh

    if background is not None:
        bg_src.x = cam_x
        bg_src.y = cam_y
        bg_src.w = screen_w
        bg_src.h = screen_h
        SDL_RenderCopy(_renderer, background.ptr, &bg_src, NULL)
        
    for asset in assets:
        # Safely unpack the primitive git atuple directly into C-variables
        tex_wrapper, sx, sy, sw, sh, dx, dy, dw, dh = asset        
        
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sh
        
        c_dst.x = dx - cam_x
        c_dst.y = dy - cam_y
        c_dst.w, c_dst.h = dw, dh
            
        SDL_RenderCopy(_renderer, tex_wrapper.ptr, &c_src, &c_dst)
                    
    SDL_RenderPresent(_renderer)
    SDL_PumpEvents()

def save(str filename, int w, int h):
    """Extracts pixel data from the active hardware renderer to debug onto disk."""
    cdef bytes b_filename = filename.encode('utf-8')
    
    cdef SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormat(
        0, w, h, 32, SDL_PIXELFORMAT_RGBA32
    )
    
    if surface == NULL:
        raise RuntimeError("Failed to create SDL_Surface for saving PNG.")
        
    SDL_RenderReadPixels(
        _renderer, NULL, SDL_PIXELFORMAT_RGBA32, surface.pixels, surface.pitch
    )
    IMG_SavePNG(surface, b_filename)
    SDL_FreeSurface(surface)

def quit_sdl():
    """Safely terminate SDL bindings."""
    global _window
    global _renderer
    if _renderer != NULL:
        SDL_DestroyRenderer(_renderer)
        _renderer = NULL
    if _window != NULL:
        SDL_DestroyWindow(_window)
        _window = NULL
    IMG_Quit()
    SDL_Quit()