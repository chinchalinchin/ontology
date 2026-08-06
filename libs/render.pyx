# cython: language_level=3
"""
# Ontology: Native Renderer (Cython)

Directly interfaces with SDL2 C-Headers to execute hardware-accelerated rendering, 
bypassing the Python Global Interpreter Lock (GIL) and ctypes overhead.
"""

from libs.core cimport Position, Dimensions, Multiple
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
    int SDL_RenderReadPixels(SDL_Renderer* renderer, const SDL_Rect* rect, unsigned int format, void* pixels, int pitch)
    
    SDL_Surface* SDL_CreateRGBSurfaceWithFormat(unsigned int flags, int width, int height, int depth, unsigned int format)
    void SDL_FreeSurface(SDL_Surface* surface)
    
    unsigned int SDL_INIT_VIDEO
    unsigned int SDL_WINDOW_HIDDEN
    unsigned int SDL_RENDERER_ACCELERATED
    int SDL_TEXTUREACCESS_TARGET
    unsigned int SDL_PIXELFORMAT_RGBA32

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

cdef inline void rectangle(SDL_Rect* rect, Position pos, Dimensions dim):
    """Helper to quickly map custom models to the SDL_Rect C-struct."""
    rect.x = pos.x
    rect.y = pos.y
    rect.w = dim.l 
    rect.h = dim.w 

def canvas(Dimensions dim) -> TexturePtr:
    """Instantiates a blank texture assigned as an accelerated rendering target."""
    cdef SDL_Texture* tex = SDL_CreateTexture(
        _renderer, 
        SDL_PIXELFORMAT_RGBA32, 
        SDL_TEXTUREACCESS_TARGET, 
        dim.l, dim.w
    )
    if tex == NULL:
        raise RuntimeError("Failed to create GPU render target.")
    
    cdef TexturePtr wrapper = TexturePtr()
    wrapper.ptr = tex
    wrapper.w = dim.l
    wrapper.h = dim.w
    return wrapper

def compose(TexturePtr base_ptr, list feature_ptrs) -> TexturePtr:
    """
    Binds a blank TEXTUREACCESS_TARGET, stamps the base and features onto it, 
    unbinds, and returns the new flattened TexturePtr.
    """
    cdef Dimensions dim = Dimensions(base_ptr.w, base_ptr.h)
    cdef TexturePtr target = canvas(dim)

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
    Constructs the static background entirely in C.
    tiles format: (TexturePtr, src_pos, src_dim, dst_pos, dst_dim, dst_mul)
    """
    SDL_SetRenderTarget(_renderer, target.ptr)
    
    cdef SDL_Rect c_src, c_dst
    cdef TexturePtr tex
    cdef Position s_pos, d_pos
    cdef Dimensions s_dim, d_dim
    cdef Multiple multi
    cdef int i, j
    
    for tile in tiles:
        tex, s_pos, s_dim, d_pos, d_dim, multi = tile
        rectangle(&c_src, s_pos, s_dim)
        
        c_dst.w = d_dim.l
        c_dst.h = d_dim.w
        
        for i in range(multi.nx):
            for j in range(multi.ny):
                c_dst.x = d_pos.x + (i * d_dim.l)
                c_dst.y = d_pos.y + (j * d_dim.w)
                SDL_RenderCopy(_renderer, tex.ptr, &c_src, &c_dst)
                
    SDL_SetRenderTarget(_renderer, NULL)
    
def render(TexturePtr background, list assets, Position camera, Dimensions screen):
    """
    """
    SDL_RenderClear(_renderer)
    cdef SDL_Rect c_src, c_dst, bg_src
    cdef TexturePtr tex_wrapper
    cdef int sx, sy, sw, sh, dx, dy, dw, dh

    if background is not None:
        bg_src.x = camera.x
        bg_src.y = camera.y
        bg_src.w = screen.l
        bg_src.h = screen.w
        SDL_RenderCopy(_renderer, background.ptr, &bg_src, NULL)
        
    for asset in assets:
        # Safely unpack the primitive tuple directly into C-variables
        tex_wrapper, sx, sy, sw, sh, dx, dy, dw, dh = asset        
        
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sh
        
        c_dst.x = dx - camera.x
        c_dst.y = dy - camera.y
        c_dst.w, c_dst.h = dw, dh
            
        SDL_RenderCopy(_renderer, tex_wrapper.ptr, &c_src, &c_dst)
                    
    SDL_RenderPresent(_renderer)

def save(str filename, Dimensions dim):
    """Extracts pixel data from the active hardware renderer to debug onto disk."""
    cdef bytes b_filename = filename.encode('utf-8')
    
    cdef SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormat(
        0, dim.l, dim.w, 32, SDL_PIXELFORMAT_RGBA32
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