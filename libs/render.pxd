# cython: language_level=3
"""
# libs/render.pxd
Header file for the hardware-accelerated SDL2 rendering pipeline.
"""

# 1. Forward-declare the opaque C-structs so other modules know they exist
cdef extern from "SDL2/SDL.h":
    ctypedef struct SDL_Renderer:
        pass
    ctypedef struct SDL_Texture:
        pass

    void SDL_DestroyTexture(SDL_Texture* texture)
    int SDL_QueryTexture(SDL_Texture* texture, unsigned int* format, int* access, int* w, int* h)

# 2. Expose the global rendering context so libs/registry.pyx can load textures
cdef SDL_Renderer* _renderer