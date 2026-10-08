"""# Ontology: tests.unit.app.assets.test_hitboxes."""

import pytest
from app.config.enums import (
    AnnualStages,
    PerennialStages,
)
from libs.core.math import geometry
from libs.core.models import Dimensions, Hitbox, Position


@pytest.mark.physics
def test_static_hitbox_fallback_on_none(mock_crate):
  """Undeclared hitboxes fall back to full bounding box dimensions."""
  mock_crate.properties.hitboxes = None

  assert len(mock_crate.hitboxes) == 1
  assert mock_crate.hitboxes[0].position.x == 0
  assert mock_crate.hitboxes[0].position.y == 0
  assert mock_crate.hitboxes[0].dimensions.w == mock_crate.dimensions.w
  assert mock_crate.hitboxes[0].dimensions.l == mock_crate.dimensions.l


@pytest.mark.physics
def test_static_hitbox_preserves_explicit_empty_list(mock_crate):
  """Explicit empty list [] preserves passable entity without bounding-box fallback (Bug B014)."""
  mock_crate.properties.hitboxes = []

  assert mock_crate.hitboxes == []


@pytest.mark.physics
def test_no_hitbox_unconditionally_empty(mock_back_tile):
  """NoHitbox strategy always resolves an empty collision list."""
  assert mock_back_tile.hitboxes == []


@pytest.mark.physics
@pytest.mark.fluids
def test_dynamic_hitbox_reads_state_bounds(mock_fluid):
  """DynamicHitbox resolves the mutable state hitbox list rather than static properties."""
  custom_bounds = [Hitbox(Position(0, 0), Dimensions(32, 64))]
  mock_fluid.state.hitboxes = custom_bounds

  assert mock_fluid.hitboxes == custom_bounds


@pytest.mark.seasons
@pytest.mark.physics
def test_stage_hitbox_annual_crop_transitions(mock_crop_resource):
  """Verifies annual crop stages transition from passable sprout/growth to solid stalk/bloom."""
  # 1. Sprout stage: Passable
  mock_crop_resource.state.stage = AnnualStages.SPROUT.value
  assert mock_crop_resource.hitboxes == []

  # 2. Growth stage: Passable
  mock_crop_resource.state.stage = AnnualStages.GROWTH.value
  assert mock_crop_resource.hitboxes == []

  # 3. Stalk stage: Physical obstacle
  mock_crop_resource.state.stage = AnnualStages.STALK.value
  stalk_hbs = mock_crop_resource.hitboxes
  assert len(stalk_hbs) == 1
  assert stalk_hbs[0].position.x == 6
  assert stalk_hbs[0].position.y == 10
  assert stalk_hbs[0].dimensions.w == 20
  assert stalk_hbs[0].dimensions.l == 12

  # 4. Bloom stage: Expanded physical footprint
  mock_crop_resource.state.stage = AnnualStages.BLOOM.value
  bloom_hbs = mock_crop_resource.hitboxes
  assert len(bloom_hbs) == 1
  assert bloom_hbs[0].position.x == 4
  assert bloom_hbs[0].position.y == 6
  assert bloom_hbs[0].dimensions.w == 24
  assert bloom_hbs[0].dimensions.l == 16

  # 5. Stump stage: Harvested / Passable
  mock_crop_resource.state.stage = AnnualStages.STUMP.value
  assert mock_crop_resource.hitboxes == []


@pytest.mark.seasons
@pytest.mark.physics
def test_stage_hitbox_perennial_transitions(mock_tree_resource):
  """Verifies adult stage constrains to trunk, sapling is passable, and stump resizes."""
  # 1. Juvenile sapling is passable
  mock_tree_resource.state.stage = PerennialStages.SAPLING.value
  assert mock_tree_resource.hitboxes == []

  # 2. Adult stage constrains to base trunk
  mock_tree_resource.state.stage = PerennialStages.ADULT.value
  hbs = mock_tree_resource.hitboxes
  assert len(hbs) == 1
  assert hbs[0].position.x == 36
  assert hbs[0].position.y == 110
  assert hbs[0].dimensions.w == 22
  assert hbs[0].dimensions.l == 24

  # 3. Stump stage reflects cut base dimensions
  mock_tree_resource.state.stage = PerennialStages.STUMP.value
  stump_hbs = mock_tree_resource.hitboxes
  assert len(stump_hbs) == 1
  assert stump_hbs[0].position.x == 30
  assert stump_hbs[0].position.y == 115
  assert stump_hbs[0].dimensions.w == 34
  assert stump_hbs[0].dimensions.l == 18