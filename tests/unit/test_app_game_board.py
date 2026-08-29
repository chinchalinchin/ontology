"""
# Ontology: tests.unit.test_app_game_board
"""
import pytest
from unittest.mock import patch

from app.game.board import Board
from app.assets.base import Asset, Taxonomy, Frame, Animation
from app.config.enums import AssetCategories, AssetInstances
from app.models.properties import SheetProperties, TileProperties
from app.models.state import SpriteState, MultiplierState
from app.models.groups import ConfigurationGroup, EquipmentGroup
from libs.core.models import Position, Dimensions, Multiple

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
    configs = ConfigurationGroup(
        recipes=mock_configurations.recipes,
        mappings=mock_configurations.mappings,
        intentions={},
        actions=[]
    )
    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={})
    
    # Patch the global settings to ensure stable spatial math regardless of environment
    with patch('app.game.board.settings.TILE_HASH_SIZE', 32):
        return Board(assets=mock_board_assets, configurations=configs, equipment=equipment)

# ---------------------------------------------------------------------------
# --------------------------------------------------------------------- TESTS

def test_board_initial_caching(mock_board):
    assert mock_board.loaded is True
    
    # Layer Indexing
    assets_layer_0 = mock_board.assets('0')
    assert len(assets_layer_0) == 2
    
    # Category Indexing
    sprites = mock_board.categories(AssetCategories.SHEETS, '0')
    tiles = mock_board.categories(AssetCategories.TILES, '0')
    assert len(sprites) == 1
    assert len(tiles) == 1
    
    # Inner Render Loop Indexing (Tiles bypassed)
    renderables = mock_board.renderables('0')
    assert len(renderables) == 1
    assert renderables[0].category == AssetCategories.SHEETS
    
    # Physics Caching
    weights = mock_board.weights('0')
    assert len(weights) == 1
    assert weights[0].name == "player"

def test_board_relayering_synchronization(mock_board):
    player = mock_board.instances(AssetInstances.SPRITES, '0')[0]
    
    # Apply relocation via DoorMechanics equivalent
    mock_board.relayer(player, '1')
    assert player.state.layer == '1'
    
    # 1. Verify purged from origin layer caches
    assert player not in mock_board.assets('0')
    assert player not in mock_board.categories(AssetCategories.SHEETS, '0')
    assert player not in mock_board.renderables('0')
    assert player not in mock_board.weights('0')
    
    # 2. Verify appended to destination layer caches
    assert player in mock_board.assets('1')
    assert player in mock_board.categories(AssetCategories.SHEETS, '1')
    assert player in mock_board.renderables('1')
    assert player in mock_board.weights('1')

def test_board_spatial_hashing(mock_board):
    """
    Tile placed at (0,0) with 32x32 dimensions and 2x2 multiplier spans area (0->64, 0->64).
    With a TILE_HASH_SIZE of 32, this must populate EXACTLY grid cells: 
    (0,0), (0,1), (1,0), (1,1).
    """
    # Quad 1: (0,0) - Contains position 10, 10
    tile_q1 = mock_board.tile('0', Position(x=10, y=10))
    assert tile_q1 is not None
    assert tile_q1.name == "grass"
    
    # Quad 2: (1,0) - Contains position 40, 10
    tile_q2 = mock_board.tile('0', Position(x=40, y=10))
    assert tile_q2 is not None
    
    # Quad 3: (0,1) - Contains position 10, 40
    tile_q3 = mock_board.tile('0', Position(x=10, y=40))
    assert tile_q3 is not None
    
    # Quad 4: (1,1) - Contains position 40, 40
    tile_q4 = mock_board.tile('0', Position(x=40, y=40))
    assert tile_q4 is not None
    
    # Out of Bounds: Cell (2,2) - Contains position 70, 70
    assert mock_board.tile('0', Position(x=70, y=70)) is None