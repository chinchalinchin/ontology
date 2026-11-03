"""
@domain.test
@test.unit
@app.board
@app.core
@app.component
@workflow.main

# Ontology: Tests - tests.unit.app.game.board.test_board_core

Unit tests for the Board class.
"""
# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
    Shortcuts,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_board,
    pytest.mark.app_core,
    pytest.mark.app_component,
]

# -----------------------------------------------------


@pytest.mark.workflow_main
@pytest.mark.workflow_hydration
def test_board_initial_caching(mock_board):
    # 1. Board initializes with loaded = False until Migrator finishes
    assert mock_board.loaded is False

    # Layer Indexing (42 on layer '0', 45 total)
    assets_layer_0 = mock_board.assets("0")
    assert len(assets_layer_0) == 42
    assert len(mock_board.assets()) == 45

    sheets = mock_board.categories(AssetCategories.SHEETS.value, "0")
    tiles = mock_board.categories(AssetCategories.TILES.value, "0")
    assert len(sheets) == 4
    assert len(tiles) == 1

    # Inner Render Loop Indexing (Tiles bypassed)
    renderables = mock_board.renderables("0")
    assert len(renderables) == 41
    assert all(a.category != AssetCategories.TILES.value for a in renderables)

    # Physics Caching
    weights = mock_board.weights("0")
    assert len(weights) == 15
    assert len(mock_board.weights()) == 17


@pytest.mark.workflow_main
def test_board_relayering_synchronization(mock_board):
    player = mock_board.player()

    # Apply relocation via DoorMechanics equivalent
    mock_board.relayer(player, "1")
    assert player.state.layer == "1"

    # 1. Verify purged from origin layer caches
    assert player not in mock_board.assets("0")
    assert player not in mock_board.categories(AssetCategories.SHEETS.value, "0")
    assert player not in mock_board.renderables("0")
    assert player not in mock_board.weights("0")

    # 2. Verify appended to destination layer caches
    assert player in mock_board.assets("1")
    assert player in mock_board.categories(AssetCategories.SHEETS.value, "1")
    assert player in mock_board.renderables("1")
    assert player in mock_board.weights("1")


@pytest.mark.workflow_main
@pytest.mark.physics_space
def test_board_spatial_hashing(mock_board):
    """
    Tile placed at (0,0) with 32x32 dimensions and 100x100 multiplier spans area (0->3200, 0->3200).
    """
    # Quad 1: (0,0) - Contains position 10, 10
    tile_q1 = mock_board.tile("0", Position(x=10, y=10))
    assert tile_q1 is not None
    assert tile_q1.name == "test-tiles"

    # Quad 2: (1,0) - Contains position 40, 10
    tile_q2 = mock_board.tile("0", Position(x=40, y=10))
    assert tile_q2 is not None

    # Quad 3: (0,1) - Contains position 10, 40
    tile_q3 = mock_board.tile("0", Position(x=10, y=40))
    assert tile_q3 is not None

    # Quad 4: (1,1) - Contains position 40, 40
    tile_q4 = mock_board.tile("0", Position(x=40, y=40))
    assert tile_q4 is not None

    # Out of Bounds: Beyond 3200x3200 tile extent
    assert mock_board.tile("0", Position(x=3300, y=3300)) is None


@pytest.mark.workflow_main
@pytest.mark.workflow_compositions
def test_board_size_tileless_layer(mock_board):
    """
    Verify layer extents derive from physical entities when no tiles are present.
    """
    sizes = mock_board.size("house-layer-1")
    assert len(sizes) == 1
    assert sizes[0].w == 106
    assert sizes[0].l == 202


@pytest.mark.workflow_main
def test_board_size_mixed_layer(mock_board):
    """
    Verify layer extents expand beyond tile boundaries when entities exceed terrain.
    """
    crate = mock_board.instances(AssetInstances.CRATES.value, "0")[0]
    crate.state.position = Position(x=3500, y=3600)

    sizes = mock_board.size("0")
    assert len(sizes) == 1
    assert sizes[0].w == 3532
    assert sizes[0].l == 3632


@pytest.mark.workflow_main
def test_board_size_empty_layer(mock_board):
    """
    Ensure querying an unpopulated or missing layer returns zero dimensions without raising errors.
    """
    sizes = mock_board.size("unpopulated-layer")
    assert len(sizes) == 1
    assert sizes[0].w == 0
    assert sizes[0].l == 0


@pytest.mark.workflow_main
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_board_fluid_spatial_query(mock_board):
    """
    Tests O(1) broad-phase spatial hash lookups on Board for fluid intersection.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.position = Position(64, 64)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 96
    mock_board.update_fluid_cache("0")

    # Positive intersection
    assert mock_board.fluid("0", Position(70, 80)) is True

    # Negative intersection
    assert mock_board.fluid("0", Position(200, 200)) is False

    # Positive with exclusion
    assert mock_board.fluid("0", Position(70, 80), exclude=fluid.name) is False


@pytest.mark.workflow_main
def test_board_add_and_remove_frequency(mock_board, mock_asset):
    """
    Validates batch entity additions, evictions, and confirms Bug B012 remediation.
    """
    crate_alt = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    crate_alt.state.name = "test-crate-alt"
    crate_alt.state.layer = "0"

    sign_alt = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.SIGNS.value)
    sign_alt.state.name = "test-sign-alt"
    sign_alt.state.layer = "0"

    initial_assets = len(mock_board.assets("0"))
    initial_weights = len(mock_board.weights("0"))

    # Add entities
    mock_board.add([crate_alt, sign_alt])
    assert len(mock_board.assets("0")) == initial_assets + 2
    assert len(mock_board.weights("0")) == initial_weights + 1
    assert crate_alt in mock_board.instances(AssetInstances.CRATES.value, "0")
    assert sign_alt in mock_board.instances(AssetInstances.SIGNS.value, "0")

    # Remove entities (verifies no method collision in Board.remove)
    mock_board.remove([crate_alt, sign_alt])
    assert len(mock_board.assets("0")) == initial_assets
    assert len(mock_board.weights("0")) == initial_weights
    assert crate_alt not in mock_board.instances(AssetInstances.CRATES.value, "0")
    assert sign_alt not in mock_board.instances(AssetInstances.SIGNS.value, "0")


@pytest.mark.workflow_main
def test_board_clear_frequency(mock_board):
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
    assert mock_board.player() is None


@pytest.mark.workflow_main
def test_board_elevation_and_entity_getters(mock_board):
    """
    Validate elevation-filtered queries and entity lookup interfaces on Board.
    """
    player = mock_board.player()
    assert mock_board.player(slot=99) is player
    assert mock_board.asset(player.name) is player
    assert mock_board.asset(player.name, layer="0") is player
    assert mock_board.character(player.name) is player.state
    assert player.name in mock_board.characters()

    crate = mock_board.instances(AssetInstances.CRATES.value, "0")[0]
    crate.state.elevation = 2

    assert crate in mock_board.assets("0", elevation=2)
    assert crate not in mock_board.assets("0", elevation=0)
    assert crate in mock_board.categories(AssetCategories.OBJECTS.value, "0", elevation=2)
    assert crate in mock_board.instances(AssetInstances.CRATES.value, "0", elevation=2)
    assert crate in mock_board.weights("0", elevation=2)

    obstacles_e0 = mock_board.obstacles("0", elevation=0)
    assert len(obstacles_e0) > 0
    assert len(mock_board.bridges("0")) >= 1
    assert len(mock_board.shorelines("0")) == len(mock_board.shorelines())


@pytest.mark.workflow_main
@pytest.mark.workflow_ecology
def test_board_moisture_and_serialization(mock_board):
    """
    Validate scalar moisture queries across layers and state serialization to SAVE_DIR.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    assert mock_board.moisture("0", fluid.state.position.x, fluid.state.position.y) >= 0.0
    assert mock_board.moisture("nonexistent-layer", 0, 0) == 0.0

    mock_board.serialize("test-world", "slot-1")
    save_file = settings.SAVE_DIR / "test-world" / "slot-1.yaml"
    assert save_file.exists() or (settings.SAVE_DIR / "test-world").exists()