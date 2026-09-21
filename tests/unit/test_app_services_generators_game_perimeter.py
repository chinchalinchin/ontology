"""
# Ontology: tests.unit.test_app_services_generators_perimeter.py
"""
from unittest.mock import patch

from app.services.generators.game.perimeter import Perimeter
from libs.core.models import Boundary, Position, Dimensions

def test_perimeter_generator_extract(mock_board, mock_crate, mock_strut):
    """
    Verifies that the PerimeterGenerator correctly filters and translates 
    TILES, OBJECTS, and CRAFTS into Cython-compatible primitive rectangles.
    """
    mock_board.add([mock_crate, mock_strut])
    generator = Perimeter()
    
    rects = generator.extract(mock_board, "0")
    
    # 1. Evaluate Tile primitive from mock_board_assets 
    # (pos: 0,0 | w:32, l:32 | nx:2, ny:2 -> span is 64x64)
    assert (0, 0, 64, 64) in rects
    
    # 2. Evaluate Object primitive from mock_crate 
    # (pos: 10,10 | w:32, l:32)
    assert (10, 10, 42, 42) in rects
    
    # 3. Evaluate Craft primitive from mock_strut 
    # (pos: 40,40 | w:32, l:32)
    assert (40, 40, 72, 72) in rects

def test_perimeter_generator_generate(mock_board):
    """
    Verifies that the generator safely passes the extracted primitives into 
    the Cython geometry pipeline and returns Boundary lists natively.
    """
    generator = Perimeter()
    
    mock_boundaries = [
        Boundary(Position(0, 0), Dimensions(64, 1)),
        Boundary(Position(64, 0), Dimensions(1, 64))
    ]
    
    with patch('app.services.generators.game.perimeter.geometry.contours') as mock_sweep:
        mock_sweep.return_value = mock_boundaries
        
        perimeter = generator.generate(mock_board, "0")
        
        mock_sweep.assert_called_once()
        assert perimeter == mock_boundaries

def test_perimeter_generator_empty_layer(mock_board):
    """
    Verifies the generator short-circuits safely on an empty layer without invoking Cython.
    """
    generator = Perimeter()
    
    with patch('app.services.generators.game.perimeter.geometry.contours') as mock_sweep:
        perimeter = generator.generate(mock_board, "empty-ghost-layer")
        
        mock_sweep.assert_not_called()
        assert perimeter == []

def test_perimeter_extract_crafts_layer_isolation(mock_multi_layer_board):
    """
    Ensure Perimeter.extract evaluates crafts strictly within the target layer boundary.
    """
    perimeter = Perimeter()

    # Extract boundaries for the tileless composition layer
    interior_rects = perimeter.extract(mock_multi_layer_board, "brick-house-compose-layer")

    # Layer contains only interior wall (0, 0, 128, 96) and floor (0, 96, 128, 192)
    assert len(interior_rects) == 2
    assert (0, 0, 128, 96) in interior_rects
    assert (0, 96, 128, 192) in interior_rects

    # Ensure Layer 0 castle strut (250, 250, 472, 383) is excluded
    assert not any(r[0] == 250 and r[1] == 250 for r in interior_rects)