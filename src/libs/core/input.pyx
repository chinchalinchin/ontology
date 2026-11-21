# cython: language_level=3
"""
@domain.system
@domain.user
@app.library
@app.device

# Ontology: Libraries - libs.core.input
"""

cdef extern from "SDL2/SDL.h":
    const unsigned char* SDL_GetKeyboardState(int* numkeys)

    unsigned int SDL_QUIT
    unsigned int SDL_KEYDOWN

    ctypedef struct SDL_Keysym:
        int scancode

    ctypedef struct SDL_KeyboardEvent:
        unsigned int type
        unsigned char state
        unsigned char repeat
        SDL_Keysym keysym

    ctypedef union SDL_Event:
        unsigned int type
        SDL_KeyboardEvent key

    int SDL_PollEvent(SDL_Event* event)


cpdef tuple pump():
    """
    Drains the SDL OS event queue to keep the window manager responsive.
    Returns (quit_requested, pressed_scancodes) where quit_requested is True
    if an SDL_QUIT event was observed and pressed_scancodes lists scancodes
    that registered non-repeat SDL_KEYDOWN transitions during this pump.
    """
    cdef SDL_Event event
    cdef bint quit_requested = False
    cdef list pressed = []

    # SDL_PollEvent implicitly pumps the OS queue and drains it.
    # This prevents the Window Manager from freezing the application!
    while SDL_PollEvent(&event):
        if event.type == SDL_QUIT:
            quit_requested = True
        elif event.type == SDL_KEYDOWN and event.key.repeat == 0:
            pressed.append(<int>event.key.keysym.scancode)

    return (quit_requested, pressed)


cpdef tuple poll(tuple scancodes):
    """
    Samples the current SDL keyboard state snapshot for the requested scancodes.
    """
    cdef const unsigned char* keys = SDL_GetKeyboardState(NULL)
    cdef list states = []
    cdef int code

    # Return a tuple of booleans (1 or 0) corresponding to the requested scancodes
    for code in scancodes:
        states.append(keys[code])

    return tuple(states)