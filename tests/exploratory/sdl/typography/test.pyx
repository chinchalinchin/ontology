# cython: language_level=3
cimport test as sdl2_ttf

def run_text_viewer():
    with open("content.txt", "rb") as f:
        text_bytes = f.read()

    if sdl2_ttf.SDL_Init(sdl2_ttf.SDL_INIT_VIDEO) != 0:
        raise RuntimeError("Failed to initialize SDL2.")
        
    if sdl2_ttf.TTF_Init() != 0:
        sdl2_ttf.SDL_Quit()
        raise RuntimeError("Failed to initialize SDL2_ttf.")
        
    cdef sdl2_ttf.SDL_Window* window = sdl2_ttf.SDL_CreateWindow(
        b"SDL2_ttf Cython Binding",
        sdl2_ttf.SDL_WINDOWPOS_CENTERED,
        sdl2_ttf.SDL_WINDOWPOS_CENTERED,
        800,
        600,
        0
    )
    
    cdef sdl2_ttf.SDL_Renderer* renderer = sdl2_ttf.SDL_CreateRenderer(window, -1, 0)
    
    cdef sdl2_ttf.TTF_Font* font = sdl2_ttf.TTF_OpenFont(b"font.ttf", 16)
    if font is NULL:
        sdl2_ttf.SDL_DestroyRenderer(renderer)
        sdl2_ttf.SDL_DestroyWindow(window)
        sdl2_ttf.TTF_Quit()
        sdl2_ttf.SDL_Quit()
        raise RuntimeError("Failed to load test/font.ttf.")
        
    cdef sdl2_ttf.SDL_Color black
    black.r = 0
    black.g = 0
    black.b = 0
    black.a = 255
    
    # Render the text surface with a 750px wrap limit to fit inside the 800px window
    cdef sdl2_ttf.SDL_Surface* surface = sdl2_ttf.TTF_RenderUTF8_Blended_Wrapped(font, text_bytes, black, 750)
    cdef sdl2_ttf.SDL_Texture* texture = sdl2_ttf.SDL_CreateTextureFromSurface(renderer, surface)
    
    cdef sdl2_ttf.SDL_Rect dstrect
    dstrect.x = 25
    dstrect.y = 25
    dstrect.w = surface.w
    dstrect.h = surface.h
    
    sdl2_ttf.SDL_FreeSurface(surface)
    
    cdef sdl2_ttf.SDL_Event event
    cdef bint running = True
    
    while running:
        while sdl2_ttf.SDL_PollEvent(&event):
            if event.type == sdl2_ttf.SDL_QUIT:
                running = False
                
        # Fill background with white
        sdl2_ttf.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
        sdl2_ttf.SDL_RenderClear(renderer)
        
        # Copy text texture to renderer
        sdl2_ttf.SDL_RenderCopy(renderer, texture, NULL, &dstrect)
        
        sdl2_ttf.SDL_RenderPresent(renderer)
        
    # Memory Cleanup
    sdl2_ttf.SDL_DestroyTexture(texture)
    sdl2_ttf.TTF_CloseFont(font)
    sdl2_ttf.SDL_DestroyRenderer(renderer)
    sdl2_ttf.SDL_DestroyWindow(window)
    sdl2_ttf.TTF_Quit()
    sdl2_ttf.SDL_Quit()