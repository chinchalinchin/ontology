"""
@domain.test
@app.asset
@test.fixtures

# Ontology: Tests - tests.unit.fixtures.assets

Loader-backed Asset factory and aggregate fixtures.
"""
# Standard Libraries
from dataclasses import fields
from typing import Optional

# External Libraries
import pytest

# Application Libraries
from app.assets.base import Asset
from app.models.config import RecipeConfiguration
from app.models.properties import PropertiesSchema
from app.models.state import AssetState, StateSchema
from app.services.factories.assets import AssetFactory
from app.static.semantics import AssetCategories

STATE_CATEGORIES = (
    AssetCategories.TILES.value,
    AssetCategories.CRAFTS.value,
    AssetCategories.CURSORS.value,
    AssetCategories.EFFECTS.value,
    AssetCategories.OBJECTS.value,
    AssetCategories.RESOURCES.value,
    AssetCategories.SHEETS.value,
)


@pytest.fixture
def asset(
    mock_properties: PropertiesSchema,
    mock_recipes_configuration: RecipeConfiguration,
    state,
):
    """
    Instantiates an Asset via AssetFactory.asset from the YAML-loaded schemas.
    """
    def _asset(
        category: str,
        instance: str,
        id: Optional[str] = None,
        asset_state: Optional[AssetState] = None,
        **state_overrides,
    ) -> Asset:
        resolved_state = asset_state or state(category, instance, id=id, **state_overrides)
        prop_map = getattr(getattr(mock_properties, category), instance)
        recipe = getattr(getattr(mock_recipes_configuration, category), instance)
        properties = prop_map[resolved_state.id]

        return AssetFactory.asset(
            category,
            instance,
            properties,
            resolved_state,
            recipe,
        )

    return _asset


@pytest.fixture
def mock_assets(asset, mock_state: StateSchema) -> list[Asset]:
    """
    Materializes all entities declared in the YAML state test bed into Asset instances.
    """
    assets: list[Asset] = []
    for category in STATE_CATEGORIES:
        category_node = getattr(mock_state, category)
        for instance_field in fields(category_node):
            instance = instance_field.name
            for entity_state in getattr(category_node, instance):
                assets.append(asset(category, instance, asset_state=entity_state))
    return assets