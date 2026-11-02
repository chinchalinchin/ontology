"""
@domain.test
@test.unit
@app.service
@workflow.generation
@workflow.collisions

# Ontology: Tests - tests.unit.app.services.generators.game.test_perimeter

Unit tests for the Perimeter class
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances
)

# Cython Libraries
from libs.core.models import (
    Boundary,
    Position,
    Dimensions
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_generation,
    pytest.mark.workflow_collisions
]

# -----------------------------------------------------

def test_perimeter_generator_extract(mock_perimeter, mock_board):
    """
    Verifies Perimeter.extract captures static substrates and architecture,
    while excluding dynamic bodies (mass > 0).
    """
    environ = mock_board.instances(AssetInstances.ENVIRON.value)[0]
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    rects = mock_perimeter.extract(mock_board, "0")

    assert (
        environ.state.position.x, 
        environ.state.position.y, 
        environ.properties.dimensions.w * environ.state.multiple.nx, 
        environ.properties.dimensions.l * environ.state.multiple.ny
    ) in rects

    assert (
        gate.state.position.x,
        gate.state.position.y, 
        gate.properties.dimensions.w, 
        gate.properties.dimensions.l
    ) in rects

    assert (
        crate.state.position.x,
        crate.state.position.y, 
        crate.properties.dimensions.w, 
        crate.properties.dimensions.l
    ) not in rects


def test_perimeter_generator_generate(mock_perimeter, mock_board):
    """
    Verifies Perimeter.generate returns perimeters partitioned by elevation tier.
    """
    perimeters = mock_perimeter.generate(mock_board, "0")

    assert isinstance(perimeters, dict)
    assert 0 in perimeters
    assert len(perimeters[0]) > 0

    for b in perimeters[0]:
        assert isinstance(b, Boundary)
        assert isinstance(b.position, Position)
        assert isinstance(b.dimensions, Dimensions)
        assert isinstance(b.position.x, int)
        assert isinstance(b.position.y, int)
        assert isinstance(b.dimensions.w, int)
        assert isinstance(b.dimensions.l, int)


def test_perimeter_generator_empty_layer(mock_perimeter, mock_board):
    """
    Verifies Perimeter.generate returns an empty dict for unpopulated layers.
    """
    perimeters = mock_perimeter.generate(mock_board, "empty-ghost-layer")
    assert perimeters == {}


@pytest.mark.workflow_compositions
def test_perimeter_extract_crafts_layer_isolation(mock_perimeter, mock_board):
    """
    Verifies Perimeter.extract isolates architecture strictly within the target layer.
    """
    interior_rects = mock_perimeter.extract(mock_board, "house-layer-0")

    assert len(interior_rects) == 2
    assert (0, 0, 128, 96) in interior_rects
    assert (0, 96, 128, 192) in interior_rects
    assert not any(r[0] == 250 and r[1] == 250 for r in interior_rects)


@pytest.mark.workflow_compositions
def test_perimeter_generator_composition_layer(mock_perimeter, mock_board):
    """
    Verifies Perimeter.generate builds boundary hulls partitioned by tier for interior layers.
    """
    boundaries = mock_perimeter.generate(mock_board, "house-layer-0")

    assert isinstance(boundaries, dict)
    assert len(boundaries) > 0
    for tier, tier_bounds in boundaries.items():
        assert len(tier_bounds) > 0
        for b in tier_bounds:
            assert isinstance(b, Boundary)
            assert isinstance(b.position, Position)
            assert isinstance(b.dimensions, Dimensions)
            assert b.dimensions.w > 0 or b.dimensions.l > 0