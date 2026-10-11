"""
# Ontology: tests.unit.app.services.generators.game.test_perimeter
"""
# External Libraries
import pytest

# Application Libraries
from app.services.generators.game.perimeter import Perimeter

# Cython Libraries
from libs.core.models import (
    Boundary, 
    Position, 
    Dimensions
)


@pytest.mark.services
@pytest.mark.collisions
def test_perimeter_generator_extract(mock_board):
    """
    Verifies Perimeter.extract captures static substrates and architecture,
    while excluding dynamic bodies (mass > 0).
    """
    generator = Perimeter()
    rects = generator.extract(mock_board, "0")

    # 1. Back Tile substrate (pos: 0, 0 | w: 32, l: 32 | nx: 10, ny: 10 -> 320x320)
    assert (0, 0, 320, 320) in rects

    # 2. Static Gate (pos: 170, 180 | w: 32, l: 32 -> 202x212)
    assert (170, 180, 202, 212) in rects

    # 3. Static Strut (pos: 250, 250 | w: 222, l: 133 -> 472x383)
    assert (250, 250, 472, 383) in rects

    # 4. Movable crate (pos: 10, 10 | mass: 5) must be excluded
    assert (10, 10, 42, 42) not in rects


@pytest.mark.services
@pytest.mark.collisions
def test_perimeter_generator_generate(mock_board):
    """
    Verifies Perimeter.generate returns perimeters partitioned by elevation tier.
    """
    generator = Perimeter()
    perimeters = generator.generate(mock_board, "0")

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


@pytest.mark.services
@pytest.mark.collisions
def test_perimeter_generator_empty_layer(mock_board):
    """
    Verifies Perimeter.generate returns an empty dict for unpopulated layers.
    """
    generator = Perimeter()
    perimeters = generator.generate(mock_board, "empty-ghost-layer")
    assert perimeters == {}


@pytest.mark.services
@pytest.mark.compositions
@pytest.mark.collisions
def test_perimeter_extract_crafts_layer_isolation(mock_board):
    """
    Verifies Perimeter.extract isolates architecture strictly within the target layer.
    """
    perimeter = Perimeter()
    interior_rects = perimeter.extract(mock_board, "brick-house-compose-layer")

    # Layer contains interior wall (0, 0, 128, 96) and floor (0, 96, 128, 192)
    assert len(interior_rects) == 2
    assert (0, 0, 128, 96) in interior_rects
    assert (0, 96, 128, 192) in interior_rects

    # Layer 0 castle strut (250, 250, 472, 383) must not leak into interior layer
    assert not any(r[0] == 250 and r[1] == 250 for r in interior_rects)


@pytest.mark.services
@pytest.mark.compositions
@pytest.mark.collisions
def test_perimeter_generator_composition_layer(mock_board):
    """
    Verifies Perimeter.generate builds boundary hulls partitioned by tier for interior layers.
    """
    generator = Perimeter()
    boundaries = generator.generate(mock_board, "brick-house-compose-layer")

    assert isinstance(boundaries, dict)
    assert len(boundaries) > 0
    for tier, tier_bounds in boundaries.items():
        assert len(tier_bounds) > 0
        for b in tier_bounds:
            assert isinstance(b, Boundary)
            assert isinstance(b.position, Position)
            assert isinstance(b.dimensions, Dimensions)
            assert b.dimensions.w > 0 or b.dimensions.l > 0