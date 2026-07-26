"""
Package for physics.
"""
# Standard Libraries
from typing import List

# Application Libraries
from app.models.properties import ShapeProperties

class Shape:
    dimension: Dimensions
    hitboxes: List[Hitbox]

    def __init__(self, shape: ShapeProperties):
        self.hitboxes = shape.hitboxes
        self.dimensions = shape.dimensions

    @staticmethod
    def intersect(a: Hitbox, b: Hitbox) -> bool:
        # implement rectangle intersection

    def intersects(self, other: Shape):
        for hb in self.hitboxes:
            for ohb in other.hitboxes:
                if self.intersect(hb, ohb):
                    return True 
        return False

    def onscreen(self, )