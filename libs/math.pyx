# cython: language_level=3
"""
# Ontology: Math & Geometry
Cythonized high-performance geometry and physics logic.
"""
# Standard Libraries
from typing import List

# Cython Libraries
# Note: 'Shape' has been removed from the imports.
from libs.core cimport Position, Dimensions, Hitbox


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
            w1 = hb1.dimensions.l
            h1 = hb1.dimensions.w
        
            for item2 in hitboxes2:
                hb2 = <Hitbox>item2
                x2 = pos2.x + hb2.position.x
                y2 = pos2.y + hb2.position.y
                w2 = hb2.dimensions.l
                h2 = hb2.dimensions.w
                
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
        cdef int cam_x = p_pos.x + (p_dim.l // 2) - (screen.l // 2)
        cdef int cam_y = p_pos.y + (p_dim.w // 2) - (screen.w // 2)
        
        return (pos.x < cam_x + screen.l and pos.x + dim.l > cam_x and
                pos.y < cam_y + screen.w and pos.y + dim.w > cam_y)


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
                
                # Retrieve raw state/properties directly, entirely skipping Shape wrapper
                if Geometry.intersects(
                    asset_a.state.position, asset_a.properties.dimensions, getattr(asset_a.properties, 'hitboxes', []),
                    asset_b.state.position, asset_b.properties.dimensions, getattr(asset_b.properties, 'hitboxes', [])
                ):
                    # TODO: Trigger collision mutators or halt vectors (Resolution Phase)
                    pass