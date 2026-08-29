"""
# Ontology: tests.unit.test_libs_graphics_registry.py
"""
import pytest
import dataclasses
from unittest.mock import patch, MagicMock

from libs.graphics.registry import Registry, TTFFont
from app.config.enums import FrameRecipe
from app.models.config import SheetRecipe, EffectRecipe, ObjectRecipe, Recipe
from app.models.properties import Action, Direction, EffectProperties, ObjectProperties, FontProperties, RGBA
from libs.core.models import Dimensions


def test_registry_initialization_and_caching(mock_properties, mock_configurations):
    """Test that Registry walks the asset directory and caches textures."""
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['player.png', 'sword.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 64
        mock_tex.l = 64
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
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
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['player.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 64
        mock_tex.l = 128
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        expected_key_1 = "player-walk-down-0"
        expected_key_2 = "player-walk-up-2"
        
        assert expected_key_1 in registry._frames
        assert expected_key_2 in registry._frames
        
        data = registry.image("player-walk-up-2")
        
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
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['explosion.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 96
        mock_tex.l = 32
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        for f in range(3):
            key = f"explosion-{f}"
            assert key in registry._frames
            
            data = registry.image(key)
            assert data is not None
            assert data[1] == f * 32  # src_x
            assert data[2] == 0       # src_y
            assert data[3] == 32      # src_w
            assert data[4] == 32      # src_l


def test_registry_fallback_retrieval(mock_properties, mock_configurations):
    """Test that Registry correctly falls back to raw textures for unindexed assets."""
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['single_frame_tile.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 32
        mock_tex.l = 32
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        assert "single_frame_tile" not in registry._frames
        
        data = registry.image("single_frame_tile")
        
        assert data is not None
        assert data[0] == mock_tex
        assert data[1] == 0
        assert data[2] == 0
        assert data[3] == 32
        assert data[4] == 32


def test_registry_stack_assembly(mock_properties, mock_configurations):
    """Test that Registry data-driven stacking works correctly."""
    mock_properties.sheets.sprites["player"].stack = ["base_body", "armor", "helmet"]
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load, \
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
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        assert registry._textures["player"] == mock_composed_tex
        mock_compose.assert_called_once()
        
        args, _ = mock_compose.call_args
        assert args[0] == registry._textures["base_body"]
        assert len(args[1]) == 2


def test_registry_noframe_indexing(mock_properties, mock_configurations):
    """Test NoFrame indexing returns a zeroed crop."""
    mock_configurations.recipes.objects = ObjectRecipe(
        chests=Recipe(frame=FrameRecipe.NONE)
    )
    mock_properties.objects.chests["invisible_chest"] = ObjectProperties(
        dimensions=Dimensions(w=32, l=32)
    )

    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['invisible_chest.png'])
        ]
        
        mock_tex = MagicMock()
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        assert "invisible_chest" in registry._frames
        data = registry.image("invisible_chest")
        
        assert data is not None
        assert data[1] == 0
        assert data[2] == 0
        assert data[3] == 0
        assert data[4] == 0


def test_registry_spriteframe_indexing(mock_properties, mock_configurations):
    """Test SpriteFrame correctly inherits StateFrame indexing rules."""
    mock_configurations.recipes.sheets = SheetRecipe(
        sprites=Recipe(frame=FrameRecipe.SPRITE)
    )
    
    actions = {
        "slash": Action(count=6, directions={"left": Direction(row=2)})
    }
    mock_properties.sheets.sprites["player"].actions = actions
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['player.png'])
        ]
        
        mock_tex = MagicMock()
        mock_tex.w = 64
        mock_tex.l = 64
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        expected_key = "player-slash-left-5"
        assert expected_key in registry._frames
        
        data = registry.image(expected_key)
        assert data[1] == 320  # src_x = frame(5) * w(64)
        assert data[2] == 128  # src_y = row(2) * l(64)
        assert data[3] == 64
        assert data[4] == 64


def test_registry_font_loading_and_retrieval(mock_properties, mock_configurations):
    """Test that Registry correctly loads and retrieves fonts."""
    mock_properties.fonts["arial"] = FontProperties(
        alignment="left",
        bold=True,
        italics=False,
        margin=0.05,
        color=RGBA(255, 255, 255, 255)
    )
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})
    
    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_font') as mock_font:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['arial.ttf'])
        ]
        
        # Instantiate real extension type to bypass Cython type checking
        mock_font_obj = TTFFont()
        mock_font.return_value = mock_font_obj
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        assert "arial" in registry._fonts
        
        retrieved_font = registry.font("arial")
        assert retrieved_font == mock_font_obj


def test_registry_missing_font(mock_properties, mock_configurations):
    """Test font retrieval for missing font returns None."""
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})
    
    with patch('libs.graphics.registry.os.walk') as mock_walk:
        mock_walk.return_value = []
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
    
    assert registry.font("missing_font") is None

def test_registry_traversal_frame_indexing(mock_properties, mock_configurations):
    """Test TraversalFrame indexing for UI buttons."""
    from app.models.properties import WidgetProperties
    from app.models.config import WidgetRecipe
    
    mock_properties.widgets.buttons["ui_btn"] = WidgetProperties(
        dimensions=Dimensions(w=32, l=32)
    )
    mock_configurations.recipes.widgets = WidgetRecipe(
        buttons=Recipe(frame=FrameRecipe.TRAVERSAL)
    )
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['ui_btn.png'])
        ]
        
        mock_tex = MagicMock()
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        expected_keys = ["ui_btn-idle", "ui_btn-active", "ui_btn-selected", "ui_btn-disabled"]
        for key in expected_keys:
            assert key in registry._frames
            
        data = registry.image("ui_btn-active")
        assert data is not None
        assert data[1] == 32  # w(32) * 1
        assert data[2] == 0
        assert data[3] == 32
        assert data[4] == 32

def test_registry_meter_frame_indexing(mock_properties, mock_configurations):
    """Test MeterFrame indexing for HUD gauges."""
    from app.models.properties import WidgetProperties
    from app.models.config import WidgetRecipe
    
    mock_properties.widgets.meters["health_bar"] = WidgetProperties(
        dimensions=Dimensions(w=100, l=10)
    )
    mock_configurations.recipes.widgets = WidgetRecipe(
        meters=Recipe(frame=FrameRecipe.METER)
    )
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry.Registry._load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['health_bar.png'])
        ]
        
        mock_tex = MagicMock()
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        assert "health_bar-0" in registry._frames
        assert "health_bar-50" in registry._frames
        assert "health_bar-100" in registry._frames
        
        data_50 = registry.image("health_bar-50")
        assert data_50 is not None
        assert data_50[1] == 100 # sx offset by 1 full width for 'filled' crop
        assert data_50[2] == 0
        assert data_50[3] == 50  # int(100 * 50 / 100)
        assert data_50[4] == 10