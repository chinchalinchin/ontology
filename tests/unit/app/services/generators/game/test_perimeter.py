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
def test_perimeter_generator_extract(mock_board):
    """
    Verifies that the PerimeterGenerator correctly filters and translates 
    TILES, OBJECTS, and CRAFTS into Cython-compatible primitive rectangles.
    """
    generator = Perimeter()
    
    rects = generator.extract(mock_board, "0")
    
    # 1. Evaluate Tile primitive from mock_board_assets 
    # (pos: 0,0 | w:32, l:32 | nx:10, ny:10 -> span is 320x320)
    assert (0, 0, 320, 320) in rects
    
    # 2. Evaluate Object primitive from mock_crate 
    # (pos: 10,10 | w:32, l:32)
    assert (10, 10, 42, 42) in rects
    
    # 3. Evaluate Craft primitive from mock_strut 
    # (pos: 250, 250 | w:222, l:133)
    assert (250, 250, 472, 383) in rects


@pytest.mark.services
def test_perimeter_generator_generate(mock_board):
    """
    Verifies that the generator passes extracted primitives into the Cython 
    geometry pipeline and unpacks directed tuples into typed Boundary instances.
    """
    generator = Perimeter()
    perimeter = generator.generate(mock_board, "0")

    assert len(perimeter) > 0
    for b in perimeter:
        assert isinstance(b, Boundary)
        assert isinstance(b.position, Position)
        assert isinstance(b.dimensions, Dimensions)
        assert isinstance(b.position.x, int)
        assert isinstance(b.position.y, int)
        assert isinstance(b.dimensions.w, int)
        assert isinstance(b.dimensions.l, int)


@pytest.mark.services
def test_perimeter_generator_empty_layer(mock_board):
    """
    Verifies the generator short-circuits safely on an empty layer without invoking Cython.
    """
    generator = Perimeter()
    perimeter = generator.generate(mock_board, "empty-ghost-layer")
    assert perimeter == []


@pytest.mark.services
def test_perimeter_extract_crafts_layer_isolation(mock_board):
    """
    Ensure Perimeter.extract evaluates crafts strictly within the target layer boundary.
    """
    perimeter = Perimeter()

    # Extract boundaries for the tileless composition layer
    interior_rects = perimeter.extract(mock_board, "brick-house-compose-layer")

    # Layer contains only interior wall (0, 0, 128, 96), floor (0, 96, 128, 192), and door (47, 142, 79, 190)
    assert len(interior_rects) == 3
    assert (0, 0, 128, 96) in interior_rects
    assert (0, 96, 128, 192) in interior_rects

    # Ensure Layer 0 castle strut (250, 250, 472, 383) is excluded
    assert not any(r[0] == 250 and r[1] == 250 for r in interior_rects)


@pytest.mark.services
def test_perimeter_generator_composition_layer(mock_board):
    """
    Verify Perimeter.generate derives a closed boundary hull for a multi-strut layer.
    """
    generator = Perimeter()
    boundaries = generator.generate(mock_board, "brick-house-compose-layer")

    assert len(boundaries) > 0
    for b in boundaries:
        assert isinstance(b, Boundary)
        assert isinstance(b.position, Position)
        assert isinstance(b.dimensions, Dimensions)
        assert b.dimensions.w > 0 or b.dimensions.l > 0