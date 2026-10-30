"""
@domain.test
@test.unit
@app.services
@workflow.generation
@workflow.collisions

# Ontology: Tests - tests.unit.app.services.generators.game.test_perimeter

Unit tests for the Perimeter class
"""
# External Libraries
import pytest

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
    rects = mock_perimeter.extract(mock_board, "0")

    # 1. Environ Tile substrate (pos: 0, 0 | w: 32, l: 32 | nx: 10, ny: 10 -> 320x320)
    assert (0, 0, 320, 320) in rects

    # 2. Static Gate (pos: 170, 180 | w: 32, l: 32 -> 202x212)
    assert (170, 180, 202, 212) in rects

    # 3. Static Strut (pos: 250, 250 | w: 222, l: 133 -> 472x383)
    assert (250, 250, 472, 383) in rects

    # 4. Movable crate (pos: 10, 10 | mass: 5) must be excluded
    assert (10, 10, 42, 42) not in rects


def test_perimeter_generator_extract_platform_elevated_deck(mock_perimeter, mock_board, mock_platform):
    """
    Verifies Perimeter.extract excludes platforms from Tier 0 hulls while synthesizing
    walkable substrate bounds from platform decks at E > base_e.
    """
    if not mock_board.asset(mock_platform.name):
        mock_board.add([mock_platform])

    mock_platform.elevation = 0
    mock_platform.state.position = Position(350, 50)
    expected_rect = (350, 50, 350 + mock_platform.dimensions.w, 50 + mock_platform.dimensions.l)

    rects_e0 = mock_perimeter.extract(mock_board, "0", elevation=0)
    rects_e1 = mock_perimeter.extract(mock_board, "0", elevation=1)

    assert expected_rect not in rects_e0
    assert expected_rect in rects_e1


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