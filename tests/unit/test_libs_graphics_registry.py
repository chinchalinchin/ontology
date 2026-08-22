"""
# Ontology: tests.unit.test_libs_graphics_registry.py
"""
import pytest
import dataclasses
from unittest.mock import patch, MagicMock

from libs.graphics.registry import Registry
from app.config.enums import FrameRecipe
from app.models.config import SheetRecipe, EffectRecipe, Recipe
from app.models.properties import Action, Direction, EffectProperties
from libs.core.models import Dimensions


def test_registry_initialization_and_caching(mock_properties, mock_configurations):
    """Test that Registry walks the asset directory and caches textures."""
    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry.load') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['player.png', 'sword.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 64
        mock_tex.l = 64
        mock_load.return_value = mock_tex
        
        registry = Registry(
            dataclasses.asdict(mock_properties), 
            dataclasses.asdict(mock_configurations.recipes)
        )
        
        mock_walk.assert_called_once()
        assert mock_load.call_count == 2
        assert 'player' in registry._textures
        assert 'sword' in registry._textures


def test_registry_indexing_and_retrieval(mock_properties, mock_configurations):
    """Test that Registry correctly indexes StateFrame schemas and retrieves data."""
    mock_configurations.recipes.sheets = SheetRecipe(
        sprites=Recipe(frame=FrameRecipe.STATE)
    )
    
    actions = {
        "walk": Action(count=3, directions={"down": Direction(row=0), "up": Direction(row=1)})
    }
    mock_properties.sheets.sprites["player"].actions = actions
    
    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry.load') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['player.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 64
        mock_tex.l = 128
        mock_load.return_value = mock_tex
        
        registry = Registry(
            dataclasses.asdict(mock_properties), 
            dataclasses.asdict(mock_configurations.recipes)
        )
        
        expected_key_1 = "player-walk-down-0"
        expected_key_2 = "player-walk-up-2"
        
        assert expected_key_1 in registry._frames
        assert expected_key_2 in registry._frames
        
        data = registry.data("player-walk-up-2")
        
        assert data is not None
        assert data[0] == mock_tex
        assert data[1] == 128  # src_x = frame * width = 2 * 64
        assert data[2] == 64   # src_y = row * length = 1 * 64
        assert data[3] == 64   # src_w
        assert data[4] == 64   # src_l


def test_registry_iterable_frame_indexing(mock_properties, mock_configurations):
    """Test IterableFrame indexing for multi-frame animations."""
    mock_properties.effects.temporary["explosion"] = EffectProperties(
        dimensions=Dimensions(w=32, l=32),
        count=3
    )
    mock_configurations.recipes.effects = EffectRecipe(
        temporary=Recipe(frame=FrameRecipe.ITERABLE)
    )
    
    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry.load') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['explosion.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 96
        mock_tex.l = 32
        mock_load.return_value = mock_tex
        
        registry = Registry(
            dataclasses.asdict(mock_properties), 
            dataclasses.asdict(mock_configurations.recipes)
        )
        
        for f in range(3):
            key = f"explosion-{f}"
            assert key in registry._frames
            
            data = registry.data(key)
            assert data is not None
            assert data[1] == f * 32  # src_x
            assert data[2] == 0       # src_y
            assert data[3] == 32      # src_w
            assert data[4] == 32      # src_l


def test_registry_fallback_retrieval(mock_properties, mock_configurations):
    """Test that Registry correctly falls back to raw textures for unindexed assets."""
    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry.load') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['single_frame_tile.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 32
        mock_tex.l = 32
        mock_load.return_value = mock_tex
        
        registry = Registry(
            dataclasses.asdict(mock_properties), 
            dataclasses.asdict(mock_configurations.recipes)
        )
        
        assert "single_frame_tile" not in registry._frames
        
        data = registry.data("single_frame_tile")
        
        assert data is not None
        assert data[0] == mock_tex
        assert data[1] == 0
        assert data[2] == 0
        assert data[3] == 32
        assert data[4] == 32


def test_registry_stack_assembly(mock_properties, mock_configurations):
    """Test that Registry data-driven stacking works correctly."""
    mock_properties.sheets.sprites["player"].stack = ["base_body", "armor", "helmet"]
    
    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry.load') as mock_load, \
         patch('libs.graphics.registry.render.compose') as mock_compose:
         
        mock_composed_tex = MagicMock()
        mock_compose.return_value = mock_composed_tex
        
        mock_walk.return_value = [
            ('/mock/assets', [], ['base_body.png', 'armor.png', 'helmet.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 64
        mock_tex.l = 64
        mock_load.return_value = mock_tex
        
        registry = Registry(
            dataclasses.asdict(mock_properties), 
            dataclasses.asdict(mock_configurations.recipes)
        )
        
        assert registry._textures["player"] == mock_composed_tex
        mock_compose.assert_called_once()
        
        args, _ = mock_compose.call_args
        assert args[0] == registry._textures["base_body"]
        assert len(args[1]) == 2