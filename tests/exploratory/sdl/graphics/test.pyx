# cython: language_level=3
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

    const char* SDL_GetError()
    int SDL_Init(unsigned int flags)
    void SDL_Quit()
    SDL_Window* SDL_CreateWindow(const char* title, int x, int y, int w, int h, unsigned int flags)
    void SDL_DestroyWindow(SDL_Window* window)
    SDL_Renderer* SDL_CreateSoftwareRenderer(SDL_Surface* surface)
    SDL_Renderer* SDL_CreateRenderer(SDL_Window* window, int index, unsigned int flags)
    void SDL_DestroyRenderer(SDL_Renderer* renderer)
    SDL_Texture* SDL_CreateTexture(SDL_Renderer* renderer, unsigned int format, int access, int w, int h)
    int SDL_SetRenderTarget(SDL_Renderer* renderer, SDL_Texture* texture)
    int SDL_RenderClear(SDL_Renderer* renderer)
    int SDL_RenderCopy(SDL_Renderer* renderer, SDL_Texture* texture, const SDL_Rect* srcrect, const SDL_Rect* dstrect)
    void SDL_RenderPresent(SDL_Renderer* renderer)
    void SDL_Delay(unsigned int ms)
    int SDL_RenderReadPixels(SDL_Renderer* renderer, const SDL_Rect* rect, unsigned int format, void* pixels, int pitch)
    SDL_Surface* SDL_CreateRGBSurfaceWithFormat(unsigned int flags, int width, int height, int depth, unsigned int format)
    void SDL_FreeSurface(SDL_Surface* surface)
    void SDL_DestroyTexture(SDL_Texture* texture)
    int SDL_QueryTexture(SDL_Texture* texture, unsigned int* format, int* access, int* w, int* h)
    
    unsigned int SDL_INIT_VIDEO
    unsigned int SDL_WINDOW_SHOWN
    unsigned int SDL_WINDOW_HIDDEN
    unsigned int SDL_RENDERER_ACCELERATED
    unsigned int SDL_RENDERER_SOFTWARE
    int SDL_TEXTUREACCESS_TARGET
    unsigned int SDL_PIXELFORMAT_RGBA32
    int SDL_SetTextureBlendMode(SDL_Texture* texture, int blendMode)
    int SDL_SetRenderDrawColor(SDL_Renderer* renderer, int r, int g, int b, int a)
    int SDL_BLENDMODE_NONE
    int SDL_BLENDMODE_BLEND

cdef extern from "SDL2/SDL_image.h":
    int IMG_Init(int flags)
    void IMG_Quit()
    SDL_Texture* IMG_LoadTexture(SDL_Renderer* renderer, const char* file)
    int IMG_SavePNG(SDL_Surface* surface, const char* file)
    int IMG_INIT_PNG

def run_test_headless():
    print("Initializing SDL...")
    SDL_Init(SDL_INIT_VIDEO)
    IMG_Init(IMG_INIT_PNG)

    # 1. Create a surface to act as our canvas
    cdef int target_w = 160 # Assuming 32x32 grass (32 * 5)
    cdef int target_h = 32
    cdef SDL_Surface* canvas = SDL_CreateRGBSurfaceWithFormat(0, target_w, target_h, 32, SDL_PIXELFORMAT_RGBA32)
    
    # 2. Attach a software renderer directly to the surface
    cdef SDL_Renderer* ren = SDL_CreateSoftwareRenderer(canvas)

    print("Loading grass.png...")
    # IMG_LoadTexture works perfectly with a software renderer
    cdef SDL_Texture* grass = IMG_LoadTexture(ren, b"grass.png")
    SDL_SetTextureBlendMode(grass, SDL_BLENDMODE_NONE)

    cdef int w, h
    SDL_QueryTexture(grass, NULL, NULL, &w, &h)

    print("Stamping grass 5 times...")
    SDL_SetRenderDrawColor(ren, 0, 0, 0, 0)
    SDL_RenderClear(ren)

    cdef SDL_Rect dst
    dst.y = 0; dst.w = w; dst.h = h
    cdef int i
    for i in range(5):
        dst.x = i * w
        SDL_RenderCopy(ren, grass, NULL, &dst)

    print("Saving directly from the canvas surface to output.png...")
    # Because the renderer is bound to the surface, the surface already has the pixels!
    IMG_SavePNG(canvas, b"output.png")
    
    print("Cleaning up...")
    SDL_DestroyTexture(grass)
    SDL_DestroyRenderer(ren)
    SDL_FreeSurface(canvas)
    IMG_Quit()
    SDL_Quit()
    print("Done!")
    
def run_test():
    print("Initializing SDL...")
    SDL_Init(SDL_INIT_VIDEO)
    IMG_Init(IMG_INIT_PNG)

    # 1. Use a SHOWN window so the GPU keeps the hardware swapchain active!
    cdef SDL_Window* win = SDL_CreateWindow(b"Ontology Test - Look at the Grass!", 100, 100, 400, 200, SDL_WINDOW_HIDDEN)
    # cdef SDL_Window* win = SDL_CreateWindow(b"Ontology Test - Look at the Grass!", 100, 100, 400, 200, SDL_WINDOW_SHOWN)

    # 2. Use the fast Hardware Renderer
    cdef SDL_Renderer* ren = SDL_CreateRenderer(win, -1,SDL_RENDERER_SOFTWARE)

    print("Loading grass.png...")
    cdef SDL_Texture* grass = IMG_LoadTexture(ren, b"grass.png")
    
    # To stamp the grass exactly as it is, overwriting any target transparency
    SDL_SetTextureBlendMode(grass, SDL_BLENDMODE_NONE)

    cdef int w, h
    SDL_QueryTexture(grass, NULL, NULL, &w, &h)
    cdef int target_w = w * 5
    cdef int target_h = h
    
    cdef SDL_Texture* target = SDL_CreateTexture(ren, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_TARGET, target_w, target_h)
    
    # Allow the target texture to blend smoothly when drawn back to the main window
    SDL_SetTextureBlendMode(target, SDL_BLENDMODE_BLEND)

    print("Stamping grass 5 times to the offscreen target...")
    SDL_SetRenderTarget(ren, target)
    
    # Clear the offscreen texture to completely transparent
    SDL_SetRenderDrawColor(ren, 0, 0, 0, 0)
    SDL_RenderClear(ren)

    cdef SDL_Rect dst
    dst.y = 0
    dst.w = w
    dst.h = h
    
    cdef int i
    for i in range(5):
        dst.x = i * w
        SDL_RenderCopy(ren, grass, NULL, &dst)

    print("Rendering target to the visible window...")
    # Reset target back to the visible window
    SDL_SetRenderTarget(ren, NULL)
    
    # Paint the main window a dark grey so we can easily see the grass strip
    SDL_SetRenderDrawColor(ren, 100, 100, 100, 255)
    SDL_RenderClear(ren)

    # Draw the composed 5-tile strip into the center of the window
    cdef SDL_Rect win_dst
    win_dst.w = target_w
    win_dst.h = target_h
    win_dst.x = (400 - target_w) // 2
    win_dst.y = (200 - target_h) // 2
    
    SDL_RenderCopy(ren, target, NULL, &win_dst)
    
    # Flash it to the screen
    SDL_RenderPresent(ren)

    print("Saving offscreen target to output.png...")
    # Switch back to the offscreen target to read its pixels
    SDL_SetRenderTarget(ren, target)
    cdef SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, target_w, target_h, 32, SDL_PIXELFORMAT_RGBA32)
    SDL_RenderReadPixels(ren, NULL, SDL_PIXELFORMAT_RGBA32, surf.pixels, surf.pitch)
    IMG_SavePNG(surf, b"output.png")
    
    print("Cleaning up...")
    SDL_FreeSurface(surf)
    SDL_SetRenderTarget(ren, NULL)
    SDL_DestroyTexture(target)
    SDL_DestroyTexture(grass)
    SDL_DestroyRenderer(ren)
    SDL_DestroyWindow(win)
    IMG_Quit()
    SDL_Quit()
    print("Done!")
