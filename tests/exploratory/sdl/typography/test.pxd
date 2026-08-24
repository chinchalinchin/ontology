from libc.stdint cimport uint32_t, uint8_t

cdef extern from "SDL2/SDL.h":
    cdef int SDL_INIT_VIDEO
    cdef int SDL_WINDOWPOS_CENTERED
    cdef uint32_t SDL_QUIT
    
    int SDL_Init(uint32_t flags)
    void SDL_Quit()
    
    ctypedef struct SDL_Window:
        pass
    ctypedef struct SDL_Renderer:
        pass
    ctypedef struct SDL_Surface:
        int w, h
    ctypedef struct SDL_Texture:
        pass
        
    SDL_Window* SDL_CreateWindow(const char* title, int x, int y, int w, int h, uint32_t flags)
    void SDL_DestroyWindow(SDL_Window* window)
    
    SDL_Renderer* SDL_CreateRenderer(SDL_Window* window, int index, uint32_t flags)
    void SDL_DestroyRenderer(SDL_Renderer* renderer)
    
    int SDL_SetRenderDrawColor(SDL_Renderer* renderer, uint8_t r, uint8_t g, uint8_t b, uint8_t a)
    int SDL_RenderClear(SDL_Renderer* renderer)
    void SDL_RenderPresent(SDL_Renderer* renderer)
    
    SDL_Texture* SDL_CreateTextureFromSurface(SDL_Renderer* renderer, SDL_Surface* surface)
    void SDL_DestroyTexture(SDL_Texture* texture)
    void SDL_FreeSurface(SDL_Surface* surface)
    
    ctypedef struct SDL_Rect:
        int x, y, w, h
        
    int SDL_RenderCopy(SDL_Renderer* renderer, SDL_Texture* texture, const SDL_Rect* srcrect, const SDL_Rect* dstrect)
    
    ctypedef union SDL_Event:
        uint32_t type
        
    int SDL_PollEvent(SDL_Event* event)

cdef extern from "SDL2/SDL_ttf.h":
    int TTF_Init()
    void TTF_Quit()
    
    ctypedef struct TTF_Font:
        pass
        
    TTF_Font* TTF_OpenFont(const char* file, int ptsize)
    void TTF_CloseFont(TTF_Font* font)
    
    ctypedef struct SDL_Color:
        uint8_t r, g, b, a
        
    # Using the _Wrapped variant to handle the blob of text and force newlines
    SDL_Surface* TTF_RenderUTF8_Blended_Wrapped(TTF_Font* font, const char* text, SDL_Color fg, uint32_t wrapLength)