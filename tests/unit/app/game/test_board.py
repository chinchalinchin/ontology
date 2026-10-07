"""
# Ontology: tests.unit.app.game.board
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Directions
)
from app.game.board import predicates

# Cython Libraries
from libs.core.models import Position

# ---------------------------------------------------------------------------
# --------------------------------------------------------------------- TESTS

@pytest.mark.main
def test_board_initial_caching(mock_board):
    # 1. New Architecture: Board initializes with loaded = False until Migrator finishes
    assert mock_board.loaded is False
    
    # Layer Indexing
    assets_layer_0 = mock_board.assets('0')
    assert len(assets_layer_0) == 13
    
    sprites = mock_board.categories(AssetCategories.SHEETS.value, '0')
    tiles = mock_board.categories(AssetCategories.TILES.value, '0')
    assert len(sprites) == 2
    assert len(tiles) == 1
    
    # Inner Render Loop Indexing (Tiles bypassed)
    renderables = mock_board.renderables('0')
    assert len(renderables) == 12
    assert renderables[0].category == AssetCategories.SHEETS.value
    
    # Physics Caching
    weights = mock_board.weights('0')
    assert len(weights) == 6


@pytest.mark.main
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


@pytest.mark.main
def test_board_spatial_hashing(mock_board):
    """
    Tile placed at (0,0) with 32x32 dimensions and 10x10 multiplier spans area (0->320, 0->32-).
    """
    # Quad 1: (0,0) - Contains position 10, 10
    tile_q1 = mock_board.tile('0', Position(x=10, y=10))
    assert tile_q1 is not None
    assert tile_q1.name == "the-steppe"
    
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


@pytest.mark.main
@pytest.mark.compositions
def test_board_size_tileless_layer(mock_board):
    """
    Verify layer extents derive from crafts and physical entities when no tiles are present.
    """
    sizes = mock_board.size("brick-house-compose-layer")
    assert len(sizes) == 1
    assert sizes[0].w == 239
    assert sizes[0].l == 264


@pytest.mark.main
def test_board_size_mixed_layer(mock_board):
    """
    Verify layer extents expand beyond tile boundaries when craft structures exceed terrain.
    """
    sizes = mock_board.size("0")
    assert len(sizes) == 1
    assert sizes[0].w == 472
    assert sizes[0].l == 383


@pytest.mark.main
def test_board_size_empty_layer(mock_board):
    """
    Ensure querying an unpopulated or missing layer returns zero dimensions without raising errors.
    """
    sizes = mock_board.size("unpopulated-layer")
    assert len(sizes) == 1
    assert sizes[0].w == 0
    assert sizes[0].l == 0


# ---------------------------------------------------------------------------
# ----------------------------------------------- GOAL 10 MODULARIZATION TESTS

@pytest.mark.main
def test_board_predicates_classification(mock_crate, mock_shoreline, mock_gate):
    """
    Validates pure predicates for physical weights and navigational obstacles.
    """
    # Weight qualification
    assert predicates.is_weight(mock_crate) is True
    assert predicates.is_weight(mock_shoreline) is False

    # Obstacle qualification
    assert predicates.is_obstacle(mock_gate) is True
    assert predicates.is_obstacle(mock_crate) is True
    assert predicates.is_obstacle(mock_shoreline) is False


@pytest.mark.main
def test_board_predicates_fluid_containment(mock_fluid):
    """
    Tests pure stream and pool containment predicates without referencing Board.
    """
    # Stream is at (64, 64), 32x32 dimensions, DOWN, length=96
    mock_fluid.state.position = Position(64, 64)
    mock_fluid.state.source = Directions.DOWN.value
    mock_fluid.state.length = 96
    mock_fluid.state.pool = None
    mock_fluid.state.branches = []

    # Inside stream corridor (x in [64, 96], y in [64, 160])
    inside_pos = Position(70, 80)
    assert predicates.in_stream(inside_pos, mock_fluid) is True
    assert predicates.in_fluid(inside_pos, mock_fluid) is True

    # Outside stream corridor
    outside_pos = Position(120, 80)
    assert predicates.in_stream(outside_pos, mock_fluid) is False
    assert predicates.in_fluid(outside_pos, mock_fluid) is False


@pytest.mark.main
def test_board_fluid_spatial_query(mock_board, mock_fluid):
    """
    Tests O(1) broad-phase spatial hash lookups on Board for fluid intersection.
    """
    mock_fluid.state.layer = "0"
    mock_fluid.state.position = Position(64, 64)
    mock_fluid.state.source = Directions.DOWN.value
    mock_fluid.state.length = 96
    mock_board.update_fluid_cache("0")

    # Positive intersection
    assert mock_board.fluid("0", Position(70, 80)) is True

    # Negative intersection
    assert mock_board.fluid("0", Position(200, 200)) is False

    # Positive with exclusion
    assert mock_board.fluid("0", Position(70, 80), exclude=mock_fluid.name) is False


@pytest.mark.main
def test_board_add_and_remove_lifecycle(mock_board, mock_crate_alt, mock_shoreline):
    """
    Validates batch entity additions, evictions, and confirms Bug B012 remediation.
    """
    mock_shoreline.state.layer = "0"
    mock_crate_alt.state.layer = "0"

    initial_assets = len(mock_board.assets("0"))
    initial_weights = len(mock_board.weights("0"))

    # Add entities
    mock_board.add([mock_crate_alt, mock_shoreline])
    assert len(mock_board.assets("0")) == initial_assets + 2
    assert len(mock_board.weights("0")) == initial_weights + 1
    assert mock_shoreline in mock_board.shorelines("0")

    # Remove entities (verifies no method collision in Board.remove)
    mock_board.remove([mock_crate_alt, mock_shoreline])
    assert len(mock_board.assets("0")) == initial_assets
    assert len(mock_board.weights("0")) == initial_weights
    assert mock_shoreline not in mock_board.shorelines("0")


@pytest.mark.main
def test_board_clear_lifecycle(mock_board):
    """
    Validates full board database wipe and confirms Bug B012 remediation on clear.
    """
    assert len(mock_board.assets()) > 0
    mock_board.clear()

    assert len(mock_board.assets()) == 0
    assert len(mock_board.layers()) == 0
    assert len(mock_board.shorelines()) == 0
    assert len(mock_board.menus) == 0
    assert len(mock_board.overlays) == 0