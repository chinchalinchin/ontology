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
    """Test that Registry walks the asset directory and caches filepaths lazily."""
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['player.png', 'sword.png'])
        ]
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        mock_walk.assert_called_once()
        # With lazy loading, textures are not loaded at boot
        assert mock_load.call_count == 0
        assert 'player' in registry._filepaths
        assert 'sword' in registry._filepaths
        assert 'player' in registry._pending_assets
        assert 'sword' in registry._pending_assets
        assert len(registry._textures) == 0


def test_registry_indexing_and_retrieval(mock_properties, mock_configurations):
    """Test that Registry correctly indexes StateFrame schemas and retrieves data JIT."""
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
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
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
        assert mock_load.call_count == 1


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
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
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
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
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
    """Test that Registry data-driven stacking works correctly via JIT compilation."""
    mock_properties.sheets.sprites["player"].stack = ["base_body", "armor", "helmet"]
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry._sys_load_image') as mock_load, \
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
        
        # FIX: Stack recipe is now mapped to _stacks
        assert isinstance(registry._stacks["player"], list)
        assert "player" not in registry._textures
        
        # Trigger JIT
        registry.image("player")
        
        assert "player" in registry._textures
        assert registry._textures["player"] == mock_composed_tex
        mock_compose.assert_called_once()
        
        args, _ = mock_compose.call_args
        assert args[0] == registry._textures["base_body"]
        assert len(args[1]) == 2


def test_registry_cyclic_stack_resolution(mock_properties, mock_configurations):
    """Test that Registry breaks cyclic stack dependencies to prevent C-stack overflow."""
    # Create a cyclic dependency: player stacks an aura ON TOP of itself
    mock_properties.sheets.sprites["player"].stack = ["player", "player-aura"]
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry._sys_load_image') as mock_load, \
         patch('libs.graphics.registry.render.compose') as mock_compose:
         
        mock_composed_tex = MagicMock()
        mock_compose.return_value = mock_composed_tex
        
        mock_walk.return_value = [
            ('/mock/assets', [], ['player.png', 'player-aura.png'])
        ]
        
        # Mock load returning different textures so we can track them
        mock_base_tex = MagicMock()
        mock_aura_tex = MagicMock()
        mock_load.side_effect = [mock_base_tex, mock_aura_tex]
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        # Both the stack and the raw file exist for 'player'
        assert "player" in registry._filepaths
        assert "player" in registry._stacks
        
        # Trigger JIT image retrieval
        registry.image("player")
        
        # Assert compose was called correctly, proving recursion was broken
        mock_compose.assert_called_once()
        args, _ = mock_compose.call_args
        assert args[0] == mock_base_tex  # Base pointer should be the raw 'player.png'
        assert args[1] == [mock_aura_tex] # Feature pointer should be the 'player-aura.png'
        assert registry._textures["player"] == mock_composed_tex
        

def test_registry_prewarm_budget(mock_properties, mock_configurations):
    """Test that prewarming exhausts the queue or yields to the time budget."""
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry._sys_load_image') as mock_load, \
         patch('libs.graphics.registry.time.perf_counter') as mock_time:
         
        # Provide multiple files to populate the pending queue
        mock_walk.return_value = [
            ('/mock/assets', [], ['asset1.png', 'asset2.png', 'asset3.png'])
        ]
        
        mock_load.return_value = MagicMock()
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        assert registry.maximum == 3
        assert registry.current == 0
        
        # Simulate an immediate time budget breach
        # Call 1: start timer. Call 2: check inside loop.
        mock_time.side_effect = [0.0, 0.020] 
        
        # Budget is 10ms. 20ms delta should trigger an early exit returning False.
        done = registry.prewarm(budget_ms=10)
        assert done is False
        assert registry.current == 0 # Queue shouldn't have popped
        assert len(registry._pending_assets) == 3
        
        # Simulate plenty of time to process everything
        # Call 1: start. Call 2,3,4: loop checks (0 delta)
        mock_time.side_effect = [0.0, 0.001, 0.001, 0.001, 0.001]
        
        done = registry.prewarm(budget_ms=10)
        assert done is True
        assert registry.current == 3
        assert len(registry._pending_assets) == 0


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
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
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
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
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
    """Test that Registry correctly loads and retrieves fonts lazily."""
    mock_properties.fonts["arial"] = FontProperties(
        alignment="left",
        bold=True,
        italics=False,
        margins=0.05,
        color=RGBA(255, 255, 255, 255)
    )
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})
    
    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry._sys_load_font') as mock_font:
         
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
        
        assert "arial" in registry._filepaths
        assert "arial" not in registry._fonts
        
        retrieved_font = registry.font("arial")
        assert retrieved_font == mock_font_obj
        assert "arial" in registry._fonts


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
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
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
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
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


def test_registry_index_frame_indexing(mock_properties, mock_configurations):
    """Test IndexFrame correctly maps a list of keys to horizontal sprite crops."""
    from app.models.properties import WidgetProperties
    from app.models.config import WidgetRecipe
    from app.config.enums import FrameRecipe
    from libs.core.models import Dimensions
    import dataclasses
    from unittest.mock import patch, MagicMock
    from libs.graphics.registry import Registry

    mock_properties.widgets.icons["items_sheet"] = WidgetProperties(
        dimensions=Dimensions(w=16, l=16),
        frames=["sword", "shield", "potion"]
    )
    mock_configurations.recipes.widgets = WidgetRecipe(
        icons=Recipe(frame=FrameRecipe.INDEX)
    )
    
    properties_dict = dataclasses.asdict(mock_properties)
    fonts_dict = properties_dict.pop("fonts", {})

    with patch('libs.graphics.registry.os.walk') as mock_walk, \
         patch('libs.graphics.registry._sys_load_image') as mock_load:
         
        mock_walk.return_value = [
            ('/mock/assets', [], ['items_sheet.png'])
        ]
        
        mock_tex = MagicMock()
        mock_load.return_value = mock_tex
        
        registry = Registry(
            properties_dict, 
            dataclasses.asdict(mock_configurations.recipes),
            fonts_dict
        )
        
        assert "sword" in registry._frames
        assert "shield" in registry._frames
        assert "potion" in registry._frames
        
        data_shield = registry.image("shield")
        assert data_shield is not None
        assert data_shield[1] == 16  # src_x = index(1) * 16 (where w=16)
        assert data_shield[2] == 0
        assert data_shield[3] == 16
        assert data_shield[4] == 16