# cython: language_level=3
"""
# Ontology: Math & Geometry
Cythonized high-performance geometry and physics logic.
"""
# Standard Libraries
from typing import List

# Cython Libraries
from libs.core cimport Position, Dimensions, Hitbox


cdef class Geometry:
    """
    Static utility class for geometric calculations.
    """

    @staticmethod
    cdef bint intersects(Position pos, Shape shape, Position other_pos, Shape other_shape):
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

    @staticmethod
    cdef bint onscreen(object asset, object player, object screen): 
        """
        Checks if an asset's bounding box intersects the screen's viewport.
        """
        # Center the camera on the player
        cdef int cam_x = player.shape.position.x + (player.shape.dimensions.l // 2) - (screen.screensize.l // 2)
        cdef int cam_y = player.shape.position.y + (player.shape.dimensions.w // 2) - (screen.screensize.w // 2)
        
        cdef int ax = asset.state.position.x
        cdef int ay = asset.state.position.y
        cdef int aw = asset.properties.dimensions.l
        cdef int ah = asset.properties.dimensions.w
        
        # AABB check against the screen bounds
        if (ax < cam_x + screen.screensize.l and ax + aw > cam_x and
            ay < cam_y + screen.screensize.w and ay + ah > cam_y):
            return True
            
        return False

    @staticmethod
    cdef tuple center(object asset):
        """
        Returns the absolute center point of an asset as a double-precision tuple.
        """
        cdef double center_x = (asset.state.position.x + asset.properties.dimensions.l) / 2.0
        cdef double center_y = (asset.state.position.y + asset.properties.dimensions.w) / 2.0
        return (center_x, center_y)

    @staticmethod
    cdef tuple offset(Position center, Dimensions dim):
        """
        Calculates the top-left offset necessary to center the given dimensions.
        """
        cdef double clip_x = center.x - (dim.l / 2.0)
        cdef double clip_y = center.y - (dim.w / 2.0)
        return (clip_x, clip_y)


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