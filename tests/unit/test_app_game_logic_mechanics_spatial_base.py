"""
# Ontology: tests.unit.test_app_game_logic_mechanics_spatial_base.py
"""
import pytest
from unittest.mock import MagicMock

from app.game.logic.mechanics.spatial.base import SpatialMechanic
from libs.core.models import Dimensions, Position, Hitbox

class ConcreteSpatialMechanic(SpatialMechanic):
    """
    Dummy subclass to implement abstract methods for testing the foundational spatial methods.
    """
    def update(self, board, delta, bus, payload):
        pass

def test_spatial_mechanic_center():
    mechanic = ConcreteSpatialMechanic()
    pos = Position(10, 10)
    dim = Dimensions(32, 64)
    cx, cy = mechanic.center(pos, dim)
    
    assert cx == 26.0  # 10 + (32 / 2)
    assert cy == 42.0  # 10 + (64 / 2)

def test_spatial_mechanic_collisions():
    mechanic = ConcreteSpatialMechanic(cell_size=64, max_entities=100)
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    
    # Asset 1 and 2 share the same spatial boundary
    asset1 = MagicMock()
    asset1.primitive.return_value = (0, 10, 10, 32, 32, [hb])
    
    asset2 = MagicMock()
    asset2.primitive.return_value = (1, 20, 20, 32, 32, [hb])
    
    # Asset 3 is located in a distant cell
    asset3 = MagicMock()
    asset3.primitive.return_value = (2, 200, 200, 32, 32, [hb])
    
    pairs = mechanic.collisions([asset1, asset2, asset3])
    
    assert len(pairs) == 1
    # Check if the collision pair registered correctly irrespective of internal array order
    assert (asset1, asset2) in pairs or (asset2, asset1) in pairs
    assert (asset1, asset3) not in pairs