"""
Package for physics.
"""
# Standard Libraries
from typing import List

# Application Libraries
from app.models.properties import Hitbox

class Shape:
    hitboxes: List[Hitbox]

    def __init__(self, hitboxes: List[Hitbox]):
        self.hitboxes = hitboxes

    @staticmethod
    def intersect(a: Hitbox, b: Hitbox) -> bool:
        # implement rectangle intersection)

    def intersects(self, other: Shape):
        for hb in self.hitboxes:
            for ohb in other.hitboxes:
                if self.intersect(hb, ohb):
                    return True 
        return False