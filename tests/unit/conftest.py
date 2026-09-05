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
    AssetInstances,
    Intentions,
    Motivations
)
from app.game.board import Board
from app.services.orchestration.constructors import (
    Builder, 
    Orchestrator
)
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
    PlayerState,
    MultiplierState,
    Inventory,
    Equipment,
    Mutators,
    MutatorTriggers,
    MutatorParameters,
    RadialParameters,
    FearParameters,
    Character,
    AnimationState,
    Meters,
    Meter,
    Psyche,
    Goal
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
    return DeviceMapping(
        world=WorldMapping(
            intentions={'attack': 44, 'interact': 8},
            goals={'up': 26, 'down': 22}
        ),
        menu=MenuMapping()
    )

@pytest.fixture
def mock_builder(mock_properties, mock_configurations, mock_state):
    with patch('app.services.orchestration.constructors.Loader') as mock_loader:
        mock_loader.load_properties.return_value = mock_properties
        mock_loader.load_configurations.return_value = mock_configurations
        mock_loader.load_state.return_value = mock_state
        
        yield Builder()

@pytest.fixture
def mock_orchestrator(mock_builder):
    return Orchestrator(mock_builder)

@pytest.fixture
def mock_provider():
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
    # 1. Dynamic Asset (Sprite) - Use primitive strings for taxonomy matching Orchestrator initialization
    sprite_tax = Taxonomy("sprite-1", "npc", AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite_props = SheetProperties(dimensions=Dimensions(w=32, l=32), mass=10)
    sprite_state = SpriteState(
        id="sprite-1", 
        name="npc", 
        layer="0", 
        position=Position(x=10, y=10),
        intention=Intentions.IDLE,
        psyche=Psyche(motivation=Motivations.CONQUEST.value, expression="none", dialogue="none", persona="test"),
        mutators=Mutators(
            triggers=MutatorTriggers(),
            parameters=MutatorParameters(
                fear=FearParameters(radius=50, limit=0.2, enemy=1),
                vision=RadialParameters(radius=100),
                action=RadialParameters(radius=10)
            )
        ),
        inventory=Inventory(equipment=Equipment()),
        animation=AnimationState(frame=0, tick=0)
    )
    sprite = Asset(sprite_tax, sprite_props, sprite_state, DummyFrame(), DummyAnimation())

    # 2. Static Asset (Tile)
    tile_tax = Taxonomy("tile-1", "grass", AssetCategories.TILES.value, AssetInstances.BACK.value)
    tile_props = TileProperties(dimensions=Dimensions(w=32, l=32))
    tile_state = MultiplierState(
        id="tile-1", name="grass", layer="0", position=Position(x=0, y=0), multiple=Multiple(nx=2, ny=2)
    )
    tile = Asset(tile_tax, tile_props, tile_state, DummyFrame(), DummyAnimation())
    
    # 3. Dynamic Asset (Player)
    player_tax = Taxonomy("player-1", "hero", AssetCategories.SHEETS.value, AssetInstances.PLAYERS.value)
    player_props = SheetProperties(dimensions=Dimensions(w=32, l=32), mass=10)
    player_state = PlayerState(
        id="player-1", 
        name="hero", 
        layer="0", 
        position=Position(x=10, y=10),
        inventory=Inventory(equipment=Equipment()),
        mutators=Mutators(triggers=MutatorTriggers()),
        character=Character(speed=5, strength=10, defense=10),
        meters=Meters(health=Meter(current=100, maximum=100), magic=Meter(current=100, maximum=100)),
        animation=AnimationState(frame=0, tick=0)
    )
    player = Asset(player_tax, player_props, player_state, DummyFrame(), DummyAnimation())
    
    return [sprite, tile, player]

@pytest.fixture
def mock_board(mock_board_assets, mock_configurations):
    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={})
    
    with patch('app.game.board.settings.TILE_HASH_SIZE', 32):
        return Board(assets=mock_board_assets, configurations=mock_configurations, equipment=equipment)