"""
@domain.test
@test.unit
@app.asset
@asset.hitbox
@workflow.collisions

# Ontology: Test - tests.unit.app.assets.test_hitboxes

Unit tests for Asset Hitbox implementations.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AnnualStages,
    AssetCategories,
    AssetInstances,
    PerennialStages,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position,
)

pytestmark = [
    pytest.mark.app_asset,
    pytest.mark.asset_hitbox,
    pytest.mark.workflow_collisions,
]


@pytest.mark.category_objects
def test_static_hitbox_fallback_on_none(mock_asset):
    """Undeclared hitboxes fall back to full bounding box dimensions."""
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.properties.hitboxes = None

    assert len(crate.hitboxes) == 1
    assert crate.hitboxes[0].position.x == 0
    assert crate.hitboxes[0].position.y == 0
    assert crate.hitboxes[0].dimensions.w == crate.dimensions.w
    assert crate.hitboxes[0].dimensions.l == crate.dimensions.l


@pytest.mark.category_objects
def test_static_hitbox_preserves_explicit_empty_list(mock_asset):
    """Explicit empty list [] preserves passable entity without bounding-box fallback (Bug B014)."""
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.properties.hitboxes = []

    assert crate.hitboxes == []


@pytest.mark.category_objects
def test_static_hitbox_elevation_filtering(mock_asset):
    """StaticHitbox resolves hitboxes at tier 0 and returns empty list on higher tiers."""
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.state.elevation = 0

    assert crate.hitbox.elevations(crate.properties, crate.state) == [0]
    assert len(crate.hitbox.get(crate.properties, crate.state, elevation=0)) == 1
    assert crate.hitbox.get(crate.properties, crate.state, elevation=1) == []


@pytest.mark.category_tiles
def test_no_hitbox_unconditionally_empty(mock_asset):
    """NoHitbox strategy always resolves an empty collision list and no elevation tiers."""
    tile = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.ENVIRON.value,
    )
    assert tile.hitbox.elevations(tile.properties, tile.state) == []
    assert tile.hitboxes == []


@pytest.mark.category_effects
def test_dynamic_hitbox_reads_state_bounds(mock_asset):
    """DynamicHitbox resolves the mutable state hitbox list rather than static properties."""
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    custom_bounds = [Hitbox(Position(0, 0), Dimensions(32, 64))]
    fluid.state.hitboxes = custom_bounds

    assert fluid.hitboxes == custom_bounds


@pytest.mark.category_effects
@pytest.mark.workflow_fluids
def test_substrate_negative_elevation_collapses_to_tier_zero(mock_asset):
    """
    Verifies assets with negative elevations normalize to collision tier 0
    when resolving hitboxes and return [] at elevation >= 1.
    """
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    bridge = mock_asset(
        AssetCategories.CRAFTS.value,
        AssetInstances.BRIDGES.value,
    )

    fluid_hb = [Hitbox(Position(0, 0), Dimensions(96, 512))]
    fluid.state.elevation = -3
    fluid.state.hitboxes = fluid_hb

    bridge.state.elevation = -1

    assert fluid.hitbox.elevations(fluid.properties, fluid.state) == [0]
    assert fluid.hitboxes == fluid_hb
    assert fluid.hitbox.get(fluid.properties, fluid.state, elevation=0) == fluid_hb
    assert fluid.hitbox.get(fluid.properties, fluid.state, elevation=1) == []

    assert bridge.hitbox.elevations(bridge.properties, bridge.state) == [0]
    assert len(bridge.hitboxes) > 0
    assert bridge.hitbox.get(bridge.properties, bridge.state, elevation=1) == []


@pytest.mark.category_crafts
@pytest.mark.modality_material
def test_material_hitbox_resolves_by_blueprint_and_elevation(mock_asset):
    """MaterialHitbox resolves hitboxes matching state.blueprint at the deployed elevation."""
    stairs = mock_asset(
        AssetCategories.CRAFTS.value,
        AssetInstances.STAIRS.value,
    )
    stairs.state.elevation = 0

    expected = stairs.properties.hitboxes.get(stairs.state.blueprint, [])
    assert stairs.hitbox.elevations(stairs.properties, stairs.state) == [0]
    assert stairs.hitboxes == expected
    assert stairs.hitbox.get(stairs.properties, stairs.state, elevation=1) == []


@pytest.mark.category_resources
@pytest.mark.workflow_seasons
def test_stage_hitbox_annual_crop_transitions(mock_asset):
    """Verifies annual crop stages transition from passable sprout/growth to solid stalk/bloom."""
    crop = mock_asset(
        AssetCategories.RESOURCES.value,
        AssetInstances.CROPS.value,
        id="maize",
    )

    crop.state.stage = AnnualStages.STALK.value
    stalk_hbs = crop.hitboxes
    assert len(stalk_hbs) == 1
    assert stalk_hbs[0].position.x == 6
    assert stalk_hbs[0].position.y == 10
    assert stalk_hbs[0].dimensions.w == 20
    assert stalk_hbs[0].dimensions.l == 12

    crop.state.stage = AnnualStages.BLOOM.value
    bloom_hbs = crop.hitboxes
    assert len(bloom_hbs) == 1
    assert bloom_hbs[0].position.x == 4
    assert bloom_hbs[0].position.y == 6
    assert bloom_hbs[0].dimensions.w == 24
    assert bloom_hbs[0].dimensions.l == 16

    crop.state.stage = AnnualStages.STUMP.value
    assert crop.hitboxes == []


@pytest.mark.category_resources
@pytest.mark.workflow_seasons
def test_stage_hitbox_perennial_transitions(mock_asset):
    """Verifies adult stage constrains to trunk, sapling is passable, and stump resizes."""
    tree = mock_asset(
        AssetCategories.RESOURCES.value,
        AssetInstances.TREES.value,
        id="deciduous",
    )

    tree.state.stage = PerennialStages.ADULT.value
    hbs = tree.hitboxes
    assert len(hbs) == 1
    assert hbs[0].position.x == 36
    assert hbs[0].position.y == 110
    assert hbs[0].dimensions.w == 22
    assert hbs[0].dimensions.l == 24

    tree.state.stage = PerennialStages.STUMP.value
    stump_hbs = tree.hitboxes
    assert len(stump_hbs) == 1
    assert stump_hbs[0].position.x == 36
    assert stump_hbs[0].position.y == 120
    assert stump_hbs[0].dimensions.w == 18
    assert stump_hbs[0].dimensions.l == 14