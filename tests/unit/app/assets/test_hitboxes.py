"""
# Ontology: tests.unit.app.assets.test_hitboxes
"""

import pytest
from app.config.enums import (
    AnnualStages,
    Directions,
    PerennialStages,
)
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)


@pytest.mark.collisions
def test_static_hitbox_fallback_on_none(mock_crate):
    """Undeclared hitboxes fall back to full bounding box dimensions."""
    mock_crate.properties.hitboxes = None

    assert len(mock_crate.hitboxes) == 1
    assert mock_crate.hitboxes[0].position.x == 0
    assert mock_crate.hitboxes[0].position.y == 0
    assert mock_crate.hitboxes[0].dimensions.w == mock_crate.dimensions.w
    assert mock_crate.hitboxes[0].dimensions.l == mock_crate.dimensions.l


@pytest.mark.collisions
def test_static_hitbox_preserves_explicit_empty_list(mock_crate):
    """Explicit empty list [] preserves passable entity without bounding-box fallback (Bug B014)."""
    mock_crate.properties.hitboxes = []

    assert mock_crate.hitboxes == []


@pytest.mark.collisions
def test_static_hitbox_elevation_filtering(mock_crate):
    """StaticHitbox resolves hitboxes at tier 0 and returns empty list on higher tiers."""
    assert mock_crate.hitbox.elevations(mock_crate.properties, mock_crate.state) == [0]
    assert len(mock_crate.hitbox.get(mock_crate.properties, mock_crate.state, elevation=0)) == 1
    assert mock_crate.hitbox.get(mock_crate.properties, mock_crate.state, elevation=1) == []


@pytest.mark.collisions
def test_no_hitbox_unconditionally_empty(mock_environ_tile):
    """NoHitbox strategy always resolves an empty collision list and no elevation tiers."""
    assert mock_environ_tile.hitbox.elevations(mock_environ_tile.properties, mock_environ_tile.state) == []
    assert mock_environ_tile.hitboxes == []


@pytest.mark.collisions
@pytest.mark.fluids
def test_dynamic_hitbox_reads_state_bounds(mock_fluid):
    """DynamicHitbox resolves the mutable state hitbox list rather than static properties."""
    custom_bounds = [Hitbox(Position(0, 0), Dimensions(32, 64))]
    mock_fluid.state.hitboxes = custom_bounds

    assert mock_fluid.hitboxes == custom_bounds


@pytest.mark.collisions
@pytest.mark.fluids
def test_substrate_negative_elevation_collapses_to_tier_zero(mock_fluid, mock_shoreline, mock_bridge):
    """
    Verifies substrate assets with negative elevations (fluids=-3, shorelines=-2, bridges=-1)
    normalize to collision tier 0 when resolving hitboxes and return [] at elevation >= 1.
    """
    fluid_hb = [Hitbox(Position(0, 0), Dimensions(96, 512))]
    shore_hb = [Hitbox(Position(0, 0), Dimensions(32, 8))]
    mock_fluid.state.hitboxes = fluid_hb
    mock_shoreline.state.hitboxes = shore_hb

    assert mock_fluid.elevation == -3
    assert mock_fluid.hitbox.elevations(mock_fluid.properties, mock_fluid.state) == [0]
    assert mock_fluid.hitboxes == fluid_hb
    assert mock_fluid.hitbox.get(mock_fluid.properties, mock_fluid.state, elevation=0) == fluid_hb
    assert mock_fluid.hitbox.get(mock_fluid.properties, mock_fluid.state, elevation=1) == []

    assert mock_shoreline.elevation == -2
    assert mock_shoreline.hitboxes == shore_hb
    assert mock_shoreline.hitbox.get(mock_shoreline.properties, mock_shoreline.state, elevation=1) == []

    assert mock_bridge.elevation == -1
    assert len(mock_bridge.hitboxes) > 0
    assert mock_bridge.hitbox.get(mock_bridge.properties, mock_bridge.state, elevation=1) == []


@pytest.mark.collisions
def test_directed_hitbox_resolves_by_direction_and_elevation(mock_stairs):
    """DirectedHitbox resolves hitboxes matching state.direction at the deployed elevation."""
    mock_stairs.state.elevation = 0
    mock_stairs.state.direction = Directions.UP.value

    expected = mock_stairs.properties.hitboxes.get(Directions.UP.value, [])
    assert mock_stairs.hitbox.elevations(mock_stairs.properties, mock_stairs.state) == [0]
    assert mock_stairs.hitboxes == expected
    assert mock_stairs.hitbox.get(mock_stairs.properties, mock_stairs.state, elevation=1) == []


@pytest.mark.collisions
def test_elevated_hitbox_multi_tier_resolution(mock_platform):
    """
    Verifies ElevatedHitbox resolves relative elevation tiers (elevation - state.elevation)
    for base facade (E) and upper deck (E + 1).
    """
    mock_platform.state.elevation = 0

    assert mock_platform.hitbox.elevations(mock_platform.properties, mock_platform.state) == [0, 1]

    tier_0_hbs = mock_platform.hitbox.get(mock_platform.properties, mock_platform.state, elevation=0)
    tier_1_hbs = mock_platform.hitbox.get(mock_platform.properties, mock_platform.state, elevation=1)
    tier_2_hbs = mock_platform.hitbox.get(mock_platform.properties, mock_platform.state, elevation=2)

    assert tier_0_hbs == mock_platform.properties.hitboxes[0]
    assert tier_1_hbs == mock_platform.properties.hitboxes[1]
    assert tier_2_hbs == []

    # Shift base deployment to elevation = 1 -> participates in tiers [1, 2]
    mock_platform.state.elevation = 1
    assert mock_platform.hitbox.elevations(mock_platform.properties, mock_platform.state) == [1, 2]
    assert mock_platform.hitbox.get(mock_platform.properties, mock_platform.state, elevation=0) == []
    assert mock_platform.hitbox.get(mock_platform.properties, mock_platform.state, elevation=1) == mock_platform.properties.hitboxes[0]
    assert mock_platform.hitbox.get(mock_platform.properties, mock_platform.state, elevation=2) == mock_platform.properties.hitboxes[1]


@pytest.mark.seasons
@pytest.mark.collisions
def test_stage_hitbox_annual_crop_transitions(mock_crop_resource):
    """Verifies annual crop stages transition from passable sprout/growth to solid stalk/bloom."""
    mock_crop_resource.state.stage = AnnualStages.SPROUT.value
    assert mock_crop_resource.hitboxes == []

    mock_crop_resource.state.stage = AnnualStages.GROWTH.value
    assert mock_crop_resource.hitboxes == []

    mock_crop_resource.state.stage = AnnualStages.STALK.value
    stalk_hbs = mock_crop_resource.hitboxes
    assert len(stalk_hbs) == 1
    assert stalk_hbs[0].position.x == 6
    assert stalk_hbs[0].position.y == 10
    assert stalk_hbs[0].dimensions.w == 20
    assert stalk_hbs[0].dimensions.l == 12

    mock_crop_resource.state.stage = AnnualStages.BLOOM.value
    bloom_hbs = mock_crop_resource.hitboxes
    assert len(bloom_hbs) == 1
    assert bloom_hbs[0].position.x == 4
    assert bloom_hbs[0].position.y == 6
    assert bloom_hbs[0].dimensions.w == 24
    assert bloom_hbs[0].dimensions.l == 16

    mock_crop_resource.state.stage = AnnualStages.STUMP.value
    assert mock_crop_resource.hitboxes == []


@pytest.mark.seasons
@pytest.mark.collisions
def test_stage_hitbox_perennial_transitions(mock_tree_resource):
    """Verifies adult stage constrains to trunk, sapling is passable, and stump resizes."""
    mock_tree_resource.state.stage = PerennialStages.SAPLING.value
    assert mock_tree_resource.hitboxes == []

    mock_tree_resource.state.stage = PerennialStages.ADULT.value
    hbs = mock_tree_resource.hitboxes
    assert len(hbs) == 1
    assert hbs[0].position.x == 36
    assert hbs[0].position.y == 110
    assert hbs[0].dimensions.w == 22
    assert hbs[0].dimensions.l == 24

    mock_tree_resource.state.stage = PerennialStages.STUMP.value
    stump_hbs = mock_tree_resource.hitboxes
    assert len(stump_hbs) == 1
    assert stump_hbs[0].position.x == 30
    assert stump_hbs[0].position.y == 115
    assert stump_hbs[0].dimensions.w == 34
    assert stump_hbs[0].dimensions.l == 18