# cython: language_level=3
"""
Ontology Native Renderer (Cython)
Directly interfaces with SDL2 C-Headers to execute hardware-accelerated rendering, 
bypassing the Python Global Interpreter Lock (GIL) and ctypes overhead.
"""

# -----------------------------------------------------------------------------
# C-Header Definitions
# -----------------------------------------------------------------------------
cdef extern from "SDL2/SDL.h":
    # Opaque structures
    ctypedef struct SDL_Window:
        pass
    ctypedef struct SDL_Renderer:
        pass
    ctypedef struct SDL_Texture:
        pass
    ctypedef struct SDL_Surface:
        void* pixels
        int pitch
        
    # Standard Rect struct for cropping/pasting
    ctypedef struct SDL_Rect:
        int x
        int y
        int w
        int h
        
    # Core SDL Functions
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
    void SDL_DestroyTexture(SDL_Texture* texture)
    
    SDL_Surface* SDL_CreateRGBSurfaceWithFormat(unsigned int flags, int width, int height, int depth, unsigned int format)
    void SDL_FreeSurface(SDL_Surface* surface)
    
    # Core SDL Constants
    unsigned int SDL_INIT_VIDEO
    unsigned int SDL_WINDOW_HIDDEN
    unsigned int SDL_RENDERER_ACCELERATED
    int SDL_TEXTUREACCESS_TARGET
    unsigned int SDL_PIXELFORMAT_RGBA32

cdef extern from "SDL2/SDL_image.h":
    int IMG_Init(int flags)
    void IMG_Quit()
    SDL_Texture* IMG_LoadTexture(SDL_Renderer* renderer, const char* file)
    int IMG_SavePNG(SDL_Surface* surface, const char* file)
    
    int IMG_INIT_PNG

# -----------------------------------------------------------------------------
# Global Singletons
# -----------------------------------------------------------------------------
cdef SDL_Window* _window = NULL
cdef SDL_Renderer* _renderer = NULL

# -----------------------------------------------------------------------------
# Extension Types
# -----------------------------------------------------------------------------
cdef class TexturePtr:
    """
    Cython extension type wrapping the raw C-pointer for an SDL_Texture.
    This provides a safe way to store GPU memory addresses in standard Python 
    variables without manual pointer arithmetic or ctypes.
    """
    cdef SDL_Texture* ptr
    cdef public int w
    cdef public int h

    def __dealloc__(self):
        # Prevent GPU memory leaks by automatically destroying the texture
        # when the Python wrapper object is garbage collected.
        if self.ptr != NULL:
            SDL_DestroyTexture(self.ptr)
            self.ptr = NULL


# -----------------------------------------------------------------------------
# Public Python/Cython API
# -----------------------------------------------------------------------------

def init_sdl():
    """Initializes the SDL subsystems and instantiates the hidden hardware renderer."""
    global _window, _renderer
    SDL_Init(SDL_INIT_VIDEO)
    IMG_Init(IMG_INIT_PNG)
    
    # Create a hidden window for offscreen GPU rendering context
    _window = SDL_CreateWindow(b"Ontology Offscreen Canvas", 0, 0, 800, 600, SDL_WINDOW_HIDDEN)
    _renderer = SDL_CreateRenderer(_window, -1, SDL_RENDERER_ACCELERATED)
    
    if _renderer == NULL:
        raise RuntimeError("Failed to initialize hardware-accelerated SDL_Renderer.")

def load_texture(str filepath) -> TexturePtr:
    """Loads a physical .png file directly into GPU memory."""
    cdef bytes b_filepath = filepath.encode('utf-8')
    cdef SDL_Texture* tex = IMG_LoadTexture(_renderer, b_filepath)
    
    if tex == NULL:
        raise RuntimeError(f"Failed to load texture into GPU memory: {filepath}")
    
    cdef TexturePtr wrapper = TexturePtr()
    wrapper.ptr = tex
    return wrapper

def create_render_target(int width, int height) -> TexturePtr:
    """Instantiates a blank texture assigned as an accelerated rendering target."""
    cdef SDL_Texture* tex = SDL_CreateTexture(
        _renderer, 
        SDL_PIXELFORMAT_RGBA32, 
        SDL_TEXTUREACCESS_TARGET, 
        width, height
    )
    if tex == NULL:
        raise RuntimeError("Failed to create GPU render target.")
    
    cdef TexturePtr wrapper = TexturePtr()
    wrapper.ptr = tex
    wrapper.w = width
    wrapper.h = height
    return wrapper

def draw_to_target(TexturePtr target, TexturePtr source, tuple src_rect=None, tuple dst_rect=None):
    """Binds a target texture, copies a cropped source onto it, and unbinds."""
    cdef SDL_Rect c_src
    cdef SDL_Rect c_dst
    cdef SDL_Rect* p_src = NULL
    cdef SDL_Rect* p_dst = NULL
    
    if src_rect is not None:
        c_src.x, c_src.y, c_src.w, c_src.h = src_rect
        p_src = &c_src
        
    if dst_rect is not None:
        c_dst.x, c_dst.y, c_dst.w, c_dst.h = dst_rect
        p_dst = &c_dst

    # Bind target, render to it natively without GIL, unbind
    SDL_SetRenderTarget(_renderer, target.ptr)
    SDL_RenderCopy(_renderer, source.ptr, p_src, p_dst)
    SDL_SetRenderTarget(_renderer, NULL)

def render_scene(TexturePtr background, list active_assets):
    """
    Renders the composite scene in C-level loop.
    active_assets should be a list of tuples: (TexturePtr, src_rect_tuple, dst_rect_tuple)
    """
    SDL_RenderClear(_renderer)
    
    # 1. Blit the pre-compiled static background
    if background is not None:
        SDL_RenderCopy(_renderer, background.ptr, NULL, NULL)
        
    # 2. Setup reusable C structures for the loop
    cdef SDL_Rect c_src
    cdef SDL_Rect c_dst
    cdef SDL_Rect* p_src
    cdef SDL_Rect* p_dst
    cdef TexturePtr tex_wrapper
    
    # 3. Overlay the stateful/animated assets
    for asset_data in active_assets:
        tex_wrapper, src_rect, dst_rect = asset_data
        
        if src_rect is not None:
            c_src.x, c_src.y, c_src.w, c_src.h = src_rect
            p_src = &c_src
        else:
            p_src = NULL
            
        if dst_rect is not None:
            c_dst.x, c_dst.y, c_dst.w, c_dst.h = dst_rect
            p_dst = &c_dst
        else:
            p_dst = NULL
            
        SDL_RenderCopy(_renderer, tex_wrapper.ptr, p_src, p_dst)
        
    # 4. Swap buffers
    SDL_RenderPresent(_renderer)

def save_to_png(str filename, int width=800, int height=600):
    """Extracts pixel data from the active hardware renderer to debug onto disk."""
    cdef bytes b_filename = filename.encode('utf-8')
    
    cdef SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormat(
        0, width, height, 32, SDL_PIXELFORMAT_RGBA32
    )
    
    if surface == NULL:
        raise RuntimeError("Failed to create SDL_Surface for saving PNG.")
        
    # Perform raw pixel readback from GPU
    SDL_RenderReadPixels(_renderer, NULL, SDL_PIXELFORMAT_RGBA32, surface.pixels, surface.pitch)
    IMG_SavePNG(surface, b_filename)
    SDL_FreeSurface(surface)

def quit_sdl():
    """Safely terminate SDL bindings."""
    global _window, _renderer
    if _renderer != NULL:
        SDL_DestroyRenderer(_renderer)
        _renderer = NULL
    if _window != NULL:
        SDL_DestroyWindow(_window)
        _window = NULL
    IMG_Quit()
    SDL_Quit()