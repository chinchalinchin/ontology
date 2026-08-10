cdef extern from "SDL2/SDL.h":
    void SDL_PumpEvents()
    const unsigned char* SDL_GetKeyboardState(int* numkeys)

def pump() -> None:
    SDL_PumpEvents()

def poll(tuple scancodes) -> tuple:
    cdef const unsigned char* keys = SDL_GetKeyboardState(NULL)
    # Return a tuple of booleans (1 or 0) corresponding to the requested scancodes
    return tuple(keys[code] for code in scancodes)