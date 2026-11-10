"""
@domain.test
@test.unit
@app.service
@workflow.generation
@workflow.collisions

# Ontology: Tests - tests.unit.app.services.generators.game.test_perimeter

Unit tests for the Perimeter class.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_service,
    pytest.mark.workflow_generation,
    pytest.mark.workflow_collisions,
]

# -----------------------------------------------------


@pytest.mark.workflow_collisions
def test_perimeter_generator_extract(mock_perimeter, mock_board):
    """
    Verifies Perimeter.extract captures static tile substrates and static
    architecture as (x1, y1, x2, y2) bounding boxes, while excluding dynamic
    bodies (mass > 0), bridges, and stairs from Tier 0 hulls.
    """
    environ = mock_board.instances(AssetInstances.ENVIRON.value, "0")[0]
    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    obstacle = mock_board.instances(AssetInstances.OBSTACLES.value, "0")[0]
    sign = mock_board.instances(AssetInstances.SIGNS.value, "0")[0]
    strut = mock_board.asset("test-strut", "0")

    crate = mock_board.instances(AssetInstances.CRATES.value, "0")[0]
    chest = mock_board.instances(AssetInstances.CHESTS.value, "0")[0]
    raft = mock_board.instances(AssetInstances.RAFTS.value, "0")[0]
    bridge = mock_board.instances(AssetInstances.BRIDGES.value, "0")[0]
    stairs = mock_board.instances(AssetInstances.STAIRS.value, "0")[0]

    rects = mock_perimeter.extract(mock_board, "0")

    assert (
        int(environ.state.position.x),
        int(environ.state.position.y),
        int(environ.state.position.x) + environ.properties.dimensions.w * environ.state.multiple.nx,
        int(environ.state.position.y) + environ.properties.dimensions.l * environ.state.multiple.ny,
    ) in rects

    for static_obj in (gate, obstacle, sign, strut):
        assert (
            int(static_obj.state.position.x),
            int(static_obj.state.position.y),
            int(static_obj.state.position.x) + static_obj.dimensions.w,
            int(static_obj.state.position.y) + static_obj.dimensions.l,
        ) in rects

    for excluded_obj in (crate, chest, raft, bridge, stairs):
        assert (
            int(excluded_obj.state.position.x),
            int(excluded_obj.state.position.y),
            int(excluded_obj.state.position.x) + excluded_obj.dimensions.w,
            int(excluded_obj.state.position.y) + excluded_obj.dimensions.l,
        ) not in rects


@pytest.mark.category_tiles
def test_perimeter_extract_tile_instance_filtering(mock_perimeter, mock_board):
    """
    Verifies Perimeter.extract includes ENVIRON and CANOPY tiles at Tier 0
    and ignores GRID overlay tiles.
    """
    environ = mock_board.instances(AssetInstances.ENVIRON.value, "0")[0]
    tile_rect = (
        int(environ.state.position.x),
        int(environ.state.position.y),
        int(environ.state.position.x) + environ.properties.dimensions.w * environ.state.multiple.nx,
        int(environ.state.position.y) + environ.properties.dimensions.l * environ.state.multiple.ny,
    )

    environ.taxonomy.instance = AssetInstances.CANOPY.value
    assert tile_rect in mock_perimeter.extract(mock_board, "0", elevation=0)

    environ.taxonomy.instance = AssetInstances.GRID.value
    assert tile_rect not in mock_perimeter.extract(mock_board, "0", elevation=0)


@pytest.mark.category_crafts
def test_perimeter_extract_elevation_partitioning_and_stairs(mock_perimeter, mock_board):
    """
    Verifies Perimeter.extract partitions static architecture by elevation tier,
    collapses negative elevations into Tier 0, and maps stair incline hitboxes
    at their target upper elevation (base_e + delta).
    """
    stairs = mock_board.instances(AssetInstances.STAIRS.value, "0")[0]
    strut = mock_board.asset("test-strut", "0")
    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]

    strut.state.elevation = 1
    gate.state.elevation = -1

    strut_rect = (
        int(strut.state.position.x),
        int(strut.state.position.y),
        int(strut.state.position.x) + strut.dimensions.w,
        int(strut.state.position.y) + strut.dimensions.l,
    )
    gate_rect = (
        int(gate.state.position.x),
        int(gate.state.position.y),
        int(gate.state.position.x) + gate.dimensions.w,
        int(gate.state.position.y) + gate.dimensions.l,
    )
    hb = stairs.hitboxes[0]
    stair_hb_rect = (
        int(stairs.state.position.x) + hb.position.x,
        int(stairs.state.position.y) + hb.position.y,
        int(stairs.state.position.x) + hb.position.x + hb.dimensions.w,
        int(stairs.state.position.y) + hb.position.y + hb.dimensions.l,
    )

    tier_0_rects = mock_perimeter.extract(mock_board, "0", elevation=0)
    assert gate_rect in tier_0_rects
    assert strut_rect not in tier_0_rects
    assert stair_hb_rect not in tier_0_rects

    tier_1_rects = mock_perimeter.extract(mock_board, "0", elevation=1)
    assert strut_rect in tier_1_rects
    assert stair_hb_rect in tier_1_rects
    assert gate_rect not in tier_1_rects
    assert (0, 0, 3200, 3200) not in tier_1_rects


@pytest.mark.category_crafts
def test_perimeter_extract_stairs_dimension_fallback(mock_perimeter, mock_board):
    """
    Verifies Perimeter.extract falls back to full stair dimensions when a stair
    asset has no hitboxes configured for its active blueprint.
    """
    stairs = mock_board.instances(AssetInstances.STAIRS.value, "0")[0]
    stairs.properties.hitboxes.clear()

    tier_1_rects = mock_perimeter.extract(mock_board, "0", elevation=1)

    assert (
        int(stairs.state.position.x),
        int(stairs.state.position.y),
        int(stairs.state.position.x) + stairs.dimensions.w,
        int(stairs.state.position.y) + stairs.dimensions.l,
    ) in tier_1_rects


@pytest.mark.workflow_compositions
def test_perimeter_extract_crafts_layer_isolation(mock_perimeter, mock_board):
    """
    Verifies Perimeter.extract isolates decomposed composition architecture
    strictly within the namespaced interior layer ('house-layer-1').
    """
    interior_rects = mock_perimeter.extract(mock_board, "house-layer-1")

    assert len(interior_rects) == 3
    assert (10, 10, 106, 106) in interior_rects
    assert (10, 106, 106, 202) in interior_rects
    assert (42, 154, 74, 202) in interior_rects
    assert not any(r[0] == 250 and r[1] == 100 for r in interior_rects)
    assert (0, 0, 3200, 3200) not in interior_rects


@pytest.mark.workflow_generation
def test_perimeter_generator_generate(mock_perimeter, mock_board):
    """
    Verifies Perimeter.generate returns contour boundaries partitioned by
    active elevation tiers.
    """
    strut = mock_board.asset("test-strut", "0")
    strut.state.elevation = 1

    perimeters = mock_perimeter.generate(mock_board, "0")

    assert set(perimeters.keys()) == {0, 1}
    assert len(perimeters[0]) == 4
    assert len(perimeters[1]) > 0


@pytest.mark.workflow_generation
def test_perimeter_generator_empty_layer(mock_perimeter, mock_board):
    """
    Verifies Perimeter.generate returns an empty dict for unpopulated layers.
    """
    perimeters = mock_perimeter.generate(mock_board, "empty-ghost-layer")
    assert perimeters == {}


@pytest.mark.workflow_compositions
def test_perimeter_generator_composition_layer(mock_perimeter, mock_board):
    """
    Verifies Perimeter.generate merges contiguous interior composition struts and
    projected doors on 'house-layer-1' into a single rectangular boundary hull.
    """
    boundaries = mock_perimeter.generate(mock_board, "house-layer-1")

    assert set(boundaries.keys()) == {0}
    assert len(boundaries[0]) == 4

    hull_segments = {
        (b.position.x, b.position.y, b.dimensions.w, b.dimensions.l)
        for b in boundaries[0]
    }
    assert (10, 10, 96, 1) in hull_segments
    assert (10, 202, 96, 1) in hull_segments
    assert (10, 10, 1, 192) in hull_segments
    assert (106, 10, 1, 192) in hull_segments