"""
@domain.test
@test.unit
@app.library
@physics.space
@workflow.collisions

# Ontology: Tests - tests.unit.libs.core.math.test_space

Unit tests for the Space Cython Library.
"""
# External Libraries
import pytest

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_library,
    pytest.mark.physics_space,
    pytest.mark.workflow_collisions,
    pytest.mark.workflow_navigation,
]

# ----------------------------------------------------------------------------------------
# SPACE TESTS
# ----------------------------------------------------------------------------------------


def test_space_clear_and_query(mock_space_grid):
    grid = mock_space_grid

    grid.insert(1, 10, 10, 32, 32)
    grid.insert(2, 20, 20, 32, 32)

    pairs = grid.query()
    assert pairs == [(1, 2)]

    grid.clear()
    assert grid.query() == []


def test_space_spanning_multiple_cells_deduplicates_and_orders_pairs(mock_space_grid):
    grid = mock_space_grid

    # Insert in reverse ID order spanning across the 64px cell boundary (cells 0 and 1)
    grid.insert(10, 48, 48, 64, 64)
    grid.insert(3, 52, 52, 64, 64)

    pairs = grid.query()
    assert pairs == [(3, 10)]


def test_space_bucket_capacity_guard(mock_space_grid):
    grid = mock_space_grid
    grid.clear()

    # Insert 60 entities into the exact same cell (exceeding max_per_bucket = 50)
    for entity_id in range(60):
        grid.insert(entity_id, 0, 0, 16, 16)

    pairs = grid.query()
    # Capped at 50 entities: C(50, 2) = 1225 unique pairs
    assert len(pairs) == 1225