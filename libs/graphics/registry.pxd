# cython: language_level=3
"""
# libs/registry.pxd

Header file for the Asset Registry and Texture Pointers.
"""

from libs.graphics.render cimport SDL_Texture

# Define the memory layout for the TexturePtr extension type.
cdef class TexturePtr:
    cdef SDL_Texture* ptr
    cdef public int w
    cdef public int l