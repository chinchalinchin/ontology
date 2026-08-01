# Cythonized intersection logic

from libs.core cimport Position, Dimensions, Hitbox, Shape

cdef class Shape:
    """
    Foundational class for Assets with mutable states.
    """
    dimensions: Dimensions
    hitboxes: List[Hitbox]

    def __init__(self, 
        dimensions: Dimensions,
        hitboxes: List[Hitbox]
    ):
        self.hitboxes = hitboxes
        self.dimensions = dimensions

    def intersects(self, 
        position: Position, 
        shape: Shape,
        other_position: Position, 
        other_shape: Shape
    ):
        """
        """
        return Geometry.intersects(position, shape, other_position, other_shape)

    def move(self, position: Position, velocity: Velocity) -> None:
        """
        Method for moving the Asset position state.
        """
        position.x = position.x + velocity.vx
        position.y = position.y + velocity.vy

def class Geometry:
    """
    """

    @staticmethod
    cdef bint intersects(self, 
        Position pos, 
        Shape shape, 
        Shape other_shape, 
        Position other_pos
    ) nogil:
        cdef int x, y, ox, oy
    
        for hb in shape.hitboxes:
            # Calculate absolute positions purely as C integers on the stack
            x = pos.x + hb.x
            y = pos.y + hb.y
        
        for ohb in other_shape.hitboxes:
            ox = other_pos.x + ohb.x
            oy = other_pos.y + other_hb.y
            
            # Inline AABB collision check using the integers
            if (x < ox + ohb.w and x + hb.w > ox and
                y < oy + ohb.h and y + hb.h > other_abs_y):
                return True
                
    return False

    @staticmethod
    cdef bint onscreen(self,
        Asset asset,
        Player player,
        Screen screen
    ): 
        # implement onscreen method
        screen.dimensions.w, screen.dimensions.h
        player.shape.position.x, player.shape.position.y
        player.shape.dimensions.w, player.shape.dimensions.h
        asset.shape.position.x, asset.shape.dimensions.w
        asset.shape.position.y, asset.shape.dimension.h

        # TODO

        return False

    @staticmethod
    cdef (double, double) center(self
        Asset asset
    ):
        center_x = (asset.state.position.x + asset.properties.dimensions.w) / 2
        center_y = (asset.state.position.y + asset.properties.dimensions.h) / 2
        return (center_x, center_y)

    @staticmethod
    cdef (double, double) offset(self
        Position center,
        Dimensions dim
    )
        clip_x = center.x - dim.w / 2
        clip_y = center.y - dim.h / 2
        return (clip_x, clip_y)