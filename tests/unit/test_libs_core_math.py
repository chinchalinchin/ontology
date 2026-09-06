"""
# Ontology: tests.unit.test_libs_core_math.py
"""
import pytest
from libs.core.models import Position, Dimensions, Hitbox, Velocity
from libs.core.math import geometry, physics, space

# ----------------------------------------------------------------------------------------
# GEOMETRY TESTS
# ----------------------------------------------------------------------------------------

def test_geometry_intersects():
    pos1 = Position(0, 0)
    dim1 = Dimensions(32, 32)
    hb1 = [Hitbox(Position(0,0), Dimensions(32, 32))]
    
    pos2 = Position(16, 16)
    dim2 = Dimensions(32, 32)
    hb2 = [Hitbox(Position(0,0), Dimensions(32, 32))]
    
    # Narrow-phase AABB positive
    result = geometry.intersects(pos1, dim1, hb1, pos2, dim2, hb2)
    assert result is not None
    assert result == (hb1[0], hb2[0])

def test_geometry_onscreen():
    pos = Position(100, 100)
    dim = Dimensions(32, 32)
    
    # Camera centered safely within screen bounds 
    p_pos = Position(100, 100)
    p_dim = Dimensions(32, 32)
    screen = Dimensions(480, 480)
    
    assert geometry.onscreen(pos, dim, p_pos, p_dim, screen) is True

def test_geometry_cone():
    # Downward check (dy=10) well within radius, cos(120/2) -> 0.5 limit
    assert geometry.cone(0, 0, 0, 10, 100, 0.5, "down") is True
    # Opposite direction check (dy=10 but facing up), should fail
    assert geometry.cone(0, 0, 0, 10, 100, 0.5, "up") is False

def test_geometry_nearby():
    # Distance of 5 is strictly less than radius of 10
    assert geometry.nearby(0, 0, 3, 4, 10) is True
    assert geometry.nearby(0, 0, 10, 10, 5) is False

# ----------------------------------------------------------------------------------------
# SPACE TESTS
# ----------------------------------------------------------------------------------------

def test_space_clear_and_query(mock_space_grid):
    grid = mock_space_grid
    
    # Insert closely packed candidate pairs
    grid.insert(1, 10, 10, 32, 32)
    grid.insert(2, 20, 20, 32, 32)
    
    pairs = grid.query()
    assert len(pairs) == 1
    assert (1, 2) in pairs or (2, 1) in pairs
    
    # Test C-level memset wipe logic
    grid.clear()
    assert len(grid.query()) == 0

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