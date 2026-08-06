# cython: language_level=3
"""
# Ontology: Math & Geometry
Cythonized high-performance geometry and physics logic.
"""
# Standard Libraries
from typing import List

# Cython Libraries
from libs.core cimport Position, Dimensions, Hitbox, Shape


cdef class Geometry:
    """
    Static utility class for geometric calculations.
    """

    @staticmethod
    cdef bint intersects(
        Position pos, 
        Shape shape, 
        Position other_pos, 
        Shape other_shape
    ):
        """
        Calculates AABB intersection between two Shape objects at native C-speeds.
        """
        cdef int x, y, ox, oy
        cdef Hitbox hb, ohb
        
        for hb in shape.hitboxes:
            # Calculate absolute positions leveraging C integers on the stack
            x = pos.x + hb.position.x
            y = pos.y + hb.position.y
        
            for ohb in other_shape.hitboxes:
                ox = other_pos.x + ohb.position.x
                oy = other_pos.y + ohb.position.y
                
                # Inline AABB collision check using the integer primitives 
                # (Note: Dimensions uses 'l' for length/width and 'w' for height/depth)
                if (x < ox + ohb.dimensions.l and x + hb.dimensions.l > ox and
                    y < oy + ohb.dimensions.w and y + hb.dimensions.w > oy):
                    return True
                    
        return False


cdef class Physics:
    """
    Static utility class for broad-phase and narrow-phase physics resolution.
    """

    @staticmethod
    cdef void collisions(list assets):
        """
        Iterates over a list of active Assets and resolves any geometric overlap.
        """
        cdef int i, j
        cdef int length = len(assets)
        cdef object asset_a, asset_b
        
        for i in range(length):
            for j in range(i + 1, length):
                asset_a = assets[i]
                asset_b = assets[j]
                
                if Geometry.intersects(
                    asset_a.state.position, asset_a.shape,
                    asset_b.state.position, asset_b.shape
                ):
                    # TODO: Trigger collision mutators or halt vectors (Resolution Phase)
                    pass