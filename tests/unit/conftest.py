"""
# Ontology: tests.unit.conftest
"""
# Standard Libraries
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# NOTE: Inject the src/ directory into the Python path prior to any local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

# External Libraries
import pytest

# Applicaiton Libraries
from app.assets.base import (
    Asset, 
    Taxonomy,
    Frame,
    Animation
)
from app.config.enums import ( 
    FrameRecipe,
    AnimationRecipe,
    AssetCategories, 
    AssetInstances
)
from app.game.board import Board
from app.services.constructors import Builder, Orchestrator
from app.services.generators.provider import Provider
from app.models.properties import (
    PropertiesSchema, 
    SheetProperties,
    WidgetProperties,
    TileProperties
)
from app.models.config import (
    ConfigurationSchema, 
    MappingConfiguration, 
    DeviceMapping,
    WorldMapping,
    MenuMapping,
    RecipeConfiguration,
    CursorRecipe,
    CraftRecipe,
    WidgetRecipe,
    Recipe
)
from app.models.state import (
    StateSchema, 
    SpriteState,
    MultiplierState
)
from app.models.groups import (
    SpawnableGroup,
    EquipmentGroup
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Multiple
)

# ---------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK CLASSES

class DummyFrame(Frame):
    def keys(self, id, state): return [id]
    def index(self, id, properties): return {}

class DummyAnimation(Animation):
    def animate(self, state, properties): return state

# ---------------------------------------------------------------------------
# ------------------------------------------------------------------ FIXTURES

@pytest.fixture
def mock_registry():
    registry = MagicMock()
    # By default, pretend every requested frame key exists and returns a dummy crop tuple.
    # Expected format: (TexturePtr, src_x, src_y, src_w, src_l)
    registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 32, 32)
    return registry

@pytest.fixture
def mock_properties():
    props = PropertiesSchema()
    props.sheets.sprites["player"] = SheetProperties(
        dimensions=Dimensions(w=64, l=64),
        mass=7
    )
    return props

@pytest.fixture
def mock_configurations():
    return ConfigurationSchema(
        mappings=MappingConfiguration(
            keyboard=DeviceMapping(
                world=WorldMapping(),
                menu=MenuMapping()
            )
        ),
        recipes=RecipeConfiguration(
            cursors=CursorRecipe(),
            crafts=CraftRecipe()
        )
    )
@pytest.fixture
def mock_state():
    state = StateSchema()
    state.sheets.sprites.append(
        SpriteState(
            id="player",
            name="player_1",
            layer="0",
            position=Position(x=10, y=10)
        )
    )
    return state

@pytest.fixture
def mock_spawnables():
    return SpawnableGroup(
        projectiles={},
        expressions={},
        temporary={},
        struts={}
    )

@pytest.fixture
def mock_mapping() -> DeviceMapping:
    """
    Provides a mock input mapping configuration.
    """
    return DeviceMapping(
        world=WorldMapping(
            intentions={'attack': 44, 'interact': 8},
            goals={'up': 26, 'down': 22}
        ),
        menu=MenuMapping()
    )

@pytest.fixture
def mock_builder(mock_properties, mock_configurations, mock_state):
    # Patch the loader inside the constructors namespace so it doesn't touch the filesystem
    with patch('app.services.constructors.Loader') as mock_loader:
        mock_loader.load_properties.return_value = mock_properties
        mock_loader.load_configurations.return_value = mock_configurations
        mock_loader.load_state.return_value = mock_state
        
        yield Builder()

@pytest.fixture
def mock_orchestrator(mock_builder):
    return Orchestrator(mock_builder)

@pytest.fixture
def mock_provider():
    # Include FrameRecipe.INDEX for isolated Icons
    recipes = WidgetRecipe(
        pages=Recipe(frame=FrameRecipe.SINGLE),
        buttons=Recipe(frame=FrameRecipe.TRAVERSAL, animation=AnimationRecipe.TRAVERSAL),
        meters=Recipe(frame=FrameRecipe.METER, animation=AnimationRecipe.METER),
        panes=Recipe(frame=FrameRecipe.NONE),
        icons=Recipe(frame=FrameRecipe.INDEX)
    )
    properties = MagicMock()
    properties.pages = {"test-page": WidgetProperties(dimensions=Dimensions(w=100, l=100))}
    properties.buttons = {"test-btn": WidgetProperties(dimensions=Dimensions(w=32, l=32))}
    properties.meters = {"test-meter": WidgetProperties(dimensions=Dimensions(w=50, l=10))}
    properties.panes = {"test-pane": WidgetProperties(dimensions=Dimensions(w=200, l=200))}
    properties.icons = {"test-icon": WidgetProperties(dimensions=Dimensions(w=16, l=16), frames=["sword"])}
    registry = MagicMock()
    
    return Provider(recipes=recipes, properties=properties, registry=registry)

@pytest.fixture
def mock_board_assets():
    # 1. Dynamic Asset (Sprite) - Should be placed in renderables and weights
    sprite_tax = Taxonomy("sprite-1", "player", AssetCategories.SHEETS, AssetInstances.SPRITES)
    sprite_props = SheetProperties(dimensions=Dimensions(w=32, l=32), mass=10)
    sprite_state = SpriteState(id="sprite-1", name="player", layer="0", position=Position(x=10, y=10))
    sprite = Asset(sprite_tax, sprite_props, sprite_state, DummyFrame(), DummyAnimation())

    # 2. Static Asset (Tile) - Spans 2x2 grid, should NOT be in renderables or weights
    tile_tax = Taxonomy("tile-1", "grass", AssetCategories.TILES, AssetInstances.BACK)
    tile_props = TileProperties(dimensions=Dimensions(w=32, l=32))
    tile_state = MultiplierState(
        id="tile-1", name="grass", layer="0", position=Position(x=0, y=0), multiple=Multiple(nx=2, ny=2)
    )
    tile = Asset(tile_tax, tile_props, tile_state, DummyFrame(), DummyAnimation())
    
    return [sprite, tile]

@pytest.fixture
def mock_board(mock_board_assets, mock_configurations):
    # Assemble required injection groups from conftest.py's ConfigurationSchema

    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={})
    
    # Patch the global settings to ensure stable spatial math regardless of environment
    with patch('app.game.board.settings.TILE_HASH_SIZE', 32):
        return Board(assets=mock_board_assets, configurations=mock_configurations, equipment=equipment)