"""
# Ontology: tests.unit.test_app_game_board
"""
from app.config.enums import AssetCategories, AssetInstances
from libs.core.models import Position

# ---------------------------------------------------------------------------
# --------------------------------------------------------------------- TESTS

def test_board_initial_caching(mock_board):
    # 1. New Architecture: Board initializes with loaded = False until Migrator finishes
    assert mock_board.loaded is False
    
    # Layer Indexing
    assets_layer_0 = mock_board.assets('0')
    assert len(assets_layer_0) == 7
    
    sprites = mock_board.categories(AssetCategories.SHEETS.value, '0')
    tiles = mock_board.categories(AssetCategories.TILES.value, '0')
    assert len(sprites) == 1
    assert len(tiles) == 1
    
    # Inner Render Loop Indexing (Tiles bypassed)
    renderables = mock_board.renderables('0')
    assert len(renderables) == 6
    assert renderables[0].category == AssetCategories.SHEETS.value
    
    # Physics Caching
    weights = mock_board.weights('0')
    assert len(weights) == 4


def test_board_relayering_synchronization(mock_board):
    player = mock_board.player()
    
    # Apply relocation via DoorMechanics equivalent
    mock_board.relayer(player, '1')
    assert player.state.layer == '1'
    
    # 1. Verify purged from origin layer caches
    assert player not in mock_board.assets('0')
    assert player not in mock_board.categories(AssetCategories.SHEETS.value, '0')
    assert player not in mock_board.renderables('0')
    assert player not in mock_board.weights('0')
    
    # 2. Verify appended to destination layer caches
    assert player in mock_board.assets('1')
    assert player in mock_board.categories(AssetCategories.SHEETS.value, '1')
    assert player in mock_board.renderables('1')
    assert player in mock_board.weights('1')


def test_board_spatial_hashing(mock_board):
    """
    Tile placed at (0,0) with 32x32 dimensions and 10x10 multiplier spans area (0->320, 0->32-).
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
    assert mock_board.tile('0', Position(x=370, y=370)) is None


def test_board_size_tileless_layer(mock_board):
    """
    Verify layer extents derive from crafts and physical entities when no tiles are present.
    """
    sizes = mock_board.size("brick-house-compose-layer")
    assert len(sizes) == 1
    assert sizes[0].w == 239
    assert sizes[0].l == 264


def test_board_size_mixed_layer(mock_board):
    """
    Verify layer extents expand beyond tile boundaries when craft structures exceed terrain.
    """
    sizes = mock_board.size("0")
    assert len(sizes) == 1
    assert sizes[0].w == 472
    assert sizes[0].l == 383


def test_board_size_empty_layer(mock_board):
    """
    Ensure querying an unpopulated or missing layer returns zero dimensions without raising errors.
    """
    sizes = mock_board.size("unpopulated-layer")
    assert len(sizes) == 1
    assert sizes[0].w == 0
    assert sizes[0].l == 0