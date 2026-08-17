# cython: language_level=3
"""
# Ontology: libs.core.math

Cythonized high-performance geometry and physics logic.
"""
# Standard Libraries
from typing import List

# Cython Libraries
from libs.core.models cimport Position, Dimensions, Hitbox


cdef class Geometry:
    """
    Static utility class for geometric calculations.
    """

    @staticmethod
    cdef bint intersects(
        Position pos1, 
        Dimensions dim1, 
        list hitboxes1,
        Position pos2, 
        Dimensions dim2, 
        list hitboxes2
    ):
        """
        Calculates AABB intersection between two entities at native C-speeds.
        """
        cdef int x1, y1, w1, h1
        cdef int x2, y2, w2, h2
        cdef Hitbox hb1, hb2
        
        # Fast path: If an object doesn't have hitboxes (e.g., background tiles), 
        # they inherently cannot collide in this engine's narrow phase.
        if not hitboxes1 or not hitboxes2:
            return False
        
        # Iterate over hitboxes. 
        # Notice we typecast `<Hitbox>item` so Cython knows the exact memory layout 
        # and doesn't fall back to standard Python dict lookups inside the loop.
        for item1 in hitboxes1:
            hb1 = <Hitbox>item1
            x1 = pos1.x + hb1.position.x
            y1 = pos1.y + hb1.position.y
            w1 = hb1.dimensions.w
            h1 = hb1.dimensions.l
        
            for item2 in hitboxes2:
                hb2 = <Hitbox>item2
                x2 = pos2.x + hb2.position.x
                y2 = pos2.y + hb2.position.y
                w2 = hb2.dimensions.w
                h2 = hb2.dimensions.l
                
                # Inline AABB collision check using the integer primitives 
                if (x1 < x2 + w2 and x1 + w1 > x2 and
                    y1 < y2 + h2 and y1 + h1 > y2):
                    return True
                    
        return False

    @staticmethod
    cdef bint onscreen(
        Position pos, 
        Dimensions dim, 
        Position p_pos, 
        Dimensions p_dim, 
        Dimensions screen
    ):
        """
        Fast AABB camera culling check. Evaluates if the asset intersects with 
        the camera's viewport (centered on the player).
        """
        # Calculate camera top-left (without board-clamping for raw speed)
        cdef int cam_x = p_pos.x + (p_dim.l // 2) - (screen.w // 2)
        cdef int cam_y = p_pos.y + (p_dim.w // 2) - (screen.l // 2)
        
        return (pos.x < cam_x + screen.w and pos.x + dim.w > cam_x and
                pos.y < cam_y + screen.l and pos.y + dim.l > cam_y)


cdef class Physics:
    """
    Static utility class for broad-phase and narrow-phase physics resolution.
    """

    @staticmethod
    cpdef list collisions(list primitive_data):
        """
        Iterates over a list of primitive spatial data tuples and resolves geometric overlap.
        Returns a Python list of colliding integer ID pairs.
        """
        cdef int i, j
        cdef int length = len(primitive_data)
        cdef tuple data_a, data_b
        cdef list colliding_pairs = []
        
        # TODO: Task 2/3 - Broad-Phase Spatial Hash & Native Narrow-Phase Implementation
        for i in range(length):
            for j in range(i + 1, length):
                data_a = primitive_data[i]
                data_b = primitive_data[j]
                pass

        return colliding_pairs