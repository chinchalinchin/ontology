"""
# Ontology: tests.unit.test_app_services_generators_perimeter.py
"""
import pytest
from unittest.mock import patch

from app.services.generators.perimeter import Perimeter
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
    
    with patch('app.services.generators.perimeter.geometry.contours') as mock_sweep:
        mock_sweep.return_value = mock_boundaries
        
        perimeter = generator.generate(mock_board, "0")
        
        mock_sweep.assert_called_once()
        assert perimeter == mock_boundaries

def test_perimeter_generator_empty_layer(mock_board):
    """
    Verifies the generator short-circuits safely on an empty layer without invoking Cython.
    """
    generator = Perimeter()
    
    with patch('app.services.generators.perimeter.geometry.contours') as mock_sweep:
        perimeter = generator.generate(mock_board, "empty-ghost-layer")
        
        mock_sweep.assert_not_called()
        assert perimeter == []