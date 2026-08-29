# cython: language_level=3
"""
# libs/registry.pxd

Header file for the Asset Registry and Texture Pointers.
"""

from libs.graphics.render cimport SDL_Texture

# Import TTF structs explicitly so render.pyx can safely share the types
cdef extern from "SDL2/SDL_ttf.h":
    ctypedef struct TTF_Font:
        pass
        
    ctypedef unsigned char Uint8
    ctypedef struct SDL_Color:
        Uint8 r
        Uint8 g
        Uint8 b
        Uint8 a

# Define the memory layout for the TexturePtr extension type.
cdef class TexturePtr:
    cdef SDL_Texture* ptr
    cdef public int w
    cdef public int l

# Define the memory layout for the TTFFont extension type.
cdef class TTFFont:
    cdef TTF_Font* ptr
    cdef public SDL_Color color
    cdef public float margins
    cdef public str align_str