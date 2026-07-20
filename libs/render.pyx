# cdef extern blocks tell Cython to look at the C headers
cdef extern from "SDL2/SDL.h":
    ctypedef struct SDL_Window:
        pass
    ctypedef struct SDL_Renderer:
        pass
    ctypedef struct SDL_Texture:
        pass
    
    # Structure for cropping and positioning
    ctypedef struct SDL_Rect:
        int x, y, w, h
        
    int SDL_Init(unsigned int flags)
    SDL_Window* SDL_CreateWindow(const char* title, int x, int y, int w, int h, unsigned int flags)
    SDL_Renderer* SDL_CreateRenderer(SDL_Window* window, int index, unsigned int flags)
    int SDL_RenderCopy(SDL_Renderer* renderer, SDL_Texture* texture, const SDL_Rect* srcrect, const SDL_Rect* dstrect)
    void SDL_RenderPresent(SDL_Renderer* renderer)
    void SDL_RenderClear(SDL_Renderer* renderer)
    void SDL_DestroyTexture(SDL_Texture* texture)
    void SDL_DestroyRenderer(SDL_Renderer* renderer)
    void SDL_DestroyWindow(SDL_Window* window)
    void SDL_Quit()

# Include the SDL_image extension for PNG support
cdef extern from "SDL2/SDL_image.h":
    int IMG_Init(int flags)
    SDL_Texture* IMG_LoadTexture(SDL_Renderer* renderer, const char* file)
    void IMG_Quit()

# SDL Constants
cdef unsigned int SDL_INIT_VIDEO = 0x00000020
cdef int IMG_INIT_PNG = 0x00000002

def render_scene():
    """Python-callable wrapper function"""
    
    # 1. Initialize C Subsystems
    SDL_Init(SDL_INIT_VIDEO)
    IMG_Init(IMG_INIT_PNG)
    
    # 2. Create Window and Renderer pointers
    cdef SDL_Window* win = SDL_CreateWindow(b"Cython Native Crop & Paste", 0, 0, 800, 600, 0)
    cdef SDL_Renderer* ren = SDL_CreateRenderer(win, -1, 0)
    
    # 3. Load PNGs directly into GPU Textures
    cdef SDL_Texture* bg_tex = IMG_LoadTexture(ren, b"background.png")
    cdef SDL_Texture* fg_tex = IMG_LoadTexture(ren, b"foreground.png")
    
    # 4. Define C-struct Rectangles for Cropping and Pasting
    cdef SDL_Rect crop_rect
    crop_rect.x = 50
    crop_rect.y = 50
    crop_rect.w = 200
    crop_rect.h = 200
    
    cdef SDL_Rect paste_rect
    paste_rect.x = 300
    paste_rect.y = 150
    paste_rect.w = 200
    paste_rect.h = 200

    # 5. Native Rendering Execution (No GIL, C-level speeds)
    SDL_RenderClear(ren)
    
    # Draw Background (Passing NULL for rects stretches to fill)
    SDL_RenderCopy(ren, bg_tex, NULL, NULL)
    
    # Draw Foreground (Applying the crop and paste rects)
    # Using & syntax to pass the memory address of the C structs
    SDL_RenderCopy(ren, fg_tex, &crop_rect, &paste_rect)
    
    SDL_RenderPresent(ren)
    
    # Memory Management (Must manually free C pointers)
    SDL_DestroyTexture(bg_tex)
    SDL_DestroyTexture(fg_tex)
    SDL_DestroyRenderer(ren)
    SDL_DestroyWindow(win)
    
    IMG_Quit()
    SDL_Quit()