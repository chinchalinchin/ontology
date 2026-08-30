# cython: language_level=3
"""
# Ontology: libs.core.input
"""
cdef extern from "SDL2/SDL.h":
    void SDL_PumpEvents()
    const unsigned char* SDL_GetKeyboardState(int* numkeys)
    
    ctypedef union SDL_Event:
        unsigned int type
        
    int SDL_PollEvent(SDL_Event* event)

def pump() -> None:
    cdef SDL_Event event
    
    # SDL_PollEvent implicitly pumps the OS queue and drains it.
    # This prevents the Window Manager from freezing the application!
    while SDL_PollEvent(&event):
        pass

def poll(tuple scancodes) -> tuple:
    cdef const unsigned char* keys = SDL_GetKeyboardState(NULL)
    # Return a tuple of booleans (1 or 0) corresponding to the requested scancodes
    return tuple(keys[code] for code in scancodes)