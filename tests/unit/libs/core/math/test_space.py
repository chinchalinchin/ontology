"""
# Ontology: tests.unit.libs.core.math.test_space
"""
# External Libraries

import pytest
from libs.core.models import Position, Dimensions, Hitbox, Velocity
from libs.core.math import geometry, physics, space

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
