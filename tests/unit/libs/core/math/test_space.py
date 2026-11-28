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

# Cython Libraries
from libs.core.math.space import Space

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
    """
    Verifies dynamic per-bucket stride expansion preserves all entities beyond the
    initial 50-entity bucket stride as well as entities occupying other active buckets.
    """
    grid = mock_space_grid
    grid.clear()

    # Populate a separate active bucket before triggering stride expansion
    grid.insert(1000, 640, 640, 16, 16)
    grid.insert(1001, 640, 640, 16, 16)

    # Insert 60 entities into the same cell (exceeding initial max_per_bucket = 50)
    count = 60
    for entity_id in range(count):
        grid.insert(entity_id, 0, 0, 16, 16)

    pairs = grid.query()
    expected_dense_pairs = (count * (count - 1)) // 2
    assert len(pairs) == expected_dense_pairs + 1
    assert (1000, 1001) in pairs


def test_space_negative_coordinates_no_self_pairing(mock_space_grid):
    """
    Verifies entities spanning negative and positive cell coordinates do not
    hash-collide into self-pairs (id, id) during Space.query().
    """
    grid = mock_space_grid
    grid.clear()

    grid.insert(0, -15, -15, 114, 114)
    grid.insert(1, 55, -15, 114, 114)

    pairs = grid.query()
    assert pairs == [(0, 1)]


def test_space_insert_ignores_non_positive_dimensions(mock_space_grid):
    """Verifies degenerate AABBs (w <= 0 or l <= 0) are not inserted into buckets."""
    grid = mock_space_grid
    grid.clear()

    grid.insert(0, 10, 10, 32, 32)
    grid.insert(1, 10, 10, 0, 32)
    grid.insert(2, 10, 10, 32, 0)
    grid.insert(3, 10, 10, -16, 32)

    assert grid.query() == []


def test_space_half_open_cell_boundary_isolation(mock_space_grid):
    """
    Verifies half-open AABB [x, x + w) cell mapping does not pair flush neighbors
    at an exact cell boundary while pairing entities that overlap by 1px.
    """
    grid = mock_space_grid
    cell = grid.cell_size

    grid.clear()
    grid.insert(0, 0, 0, cell, cell)
    grid.insert(1, cell, 0, cell, cell)
    assert grid.query() == []

    grid.clear()
    grid.insert(0, 0, 0, cell + 1, cell)
    grid.insert(1, cell, 0, cell, cell)
    assert grid.query() == [(0, 1)]


def test_space_active_bucket_clear_reuse_cycles(mock_space_grid):
    """
    Verifies O(active_count) clear() completely flushes occupied buckets across
    repeated insert/query/clear cycles with no stale ghost pairs.
    """
    grid = mock_space_grid

    for cycle in range(5):
        grid.clear()
        offset = cycle * grid.cell_size * 3
        grid.insert(cycle * 2, offset, offset, 32, 32)
        grid.insert(cycle * 2 + 1, offset + 8, offset + 8, 32, 32)
        assert grid.query() == [(cycle * 2, cycle * 2 + 1)]

    grid.clear()
    assert grid.query() == []


def test_space_constructor_clamps_non_positive_parameters():
    """Verifies Space clamps non-positive cell_size and max_entities safely."""
    grid = Space(cell_size=0, max_entities=0)
    grid.insert(0, 10, 10, 16, 16)
    grid.insert(1, 12, 12, 16, 16)

    assert grid.query() == [(0, 1)]