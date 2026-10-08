"""
# Ontology: tests.unit.app.assets.test_hitboxes
"""
# External Libraries
import pytest

# Application Libraries
from app.assets.base import (
    Asset, 
    Taxonomy
)
from app.assets.hitboxes import (
    StaticHitbox, 
    DynamicHitbox, 
    StageHitbox, 
    NoHitbox
)
from app.config.enums import (
    AssetCategories, 
    AssetInstances, 
    PerennialStages
)
from libs.core.models import Position, Dimensions, Hitbox


@pytest.mark.physics
def test_static_hitbox_fallback_on_none(mock_object_properties, mock_positional_state):
    """Undeclared hitboxes fall back to full bounding box dimensions."""
    mock_object_properties.crates["wood-crate"].hitboxes = None
    crate = Asset(
        taxonomy=Taxonomy("wood-crate", "box", AssetCategories.OBJECTS.value, AssetInstances.CRATES.value),
        properties=mock_object_properties.crates["wood-crate"],
        state=mock_positional_state,
        hitbox=StaticHitbox()
    )
    assert len(crate.hitboxes) == 1
    assert crate.hitboxes[0].position.x == 0
    assert crate.hitboxes[0].position.y == 0
    assert crate.hitboxes[0].dimensions.w == crate.dimensions.w
    assert crate.hitboxes[0].dimensions.l == crate.dimensions.l


@pytest.mark.physics
def test_static_hitbox_preserves_explicit_empty_list(mock_object_properties, mock_positional_state):
    """Explicit empty list [] preserves passable entity without bounding-box fallback (Bug B014)."""
    mock_object_properties.crates["wood-crate"].hitboxes = []
    crate = Asset(
        taxonomy=Taxonomy("wood-crate", "box", AssetCategories.OBJECTS.value, AssetInstances.CRATES.value),
        properties=mock_object_properties.crates["wood-crate"],
        state=mock_positional_state,
        hitbox=StaticHitbox()
    )
    assert crate.hitboxes == []


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