"""
# Ontology: tests.unit.libs.core.math.physics
"""
# External Libraries

import pytest
from libs.core.models import Position, Dimensions, Hitbox, Velocity
from libs.core.math import geometry, physics, space


# ----------------------------------------------------------------------------------------
# PHYSICS TESTS
# ----------------------------------------------------------------------------------------

def test_physics_collisions(mock_space_grid):
    hb = Hitbox(Position(0,0), Dimensions(32, 32))
    
    # Primitive flattened tuples: (id, x, y, w, l, hitboxes)
    p1 = (0, 10, 10, 32, 32, [hb])
    p2 = (1, 20, 20, 32, 32, [hb])
    
    pairs = physics.collisions([p1, p2], mock_space_grid)
    assert len(pairs) == 1

def test_physics_integrate():
    class DummyState:
        def __init__(self):
            self.position = Position(0, 0)
            self.velocity = Velocity(10.0, -10.0)
            
    class DummyAsset:
        def __init__(self):
            self.state = DummyState()
            
    asset = DummyAsset()
    
    # Time delta of 0.5 should integrate position to exactly +5.0 and -5.0
    physics.integrate([asset], 0.5)
    
    assert asset.state.position.x == 5
    assert asset.state.position.y == -5
    
    # Floating accumulators (rx, ry) must cleanly reset after sub-pixel boundaries snap
    assert asset.state.position.rx == 0.0
    assert asset.state.position.ry == 0.0
