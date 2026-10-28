"""
@domain.test
@test.fixtures
@app.asset
@modality.material
@workflow.injection

# Ontology: Test - tests.unit.fixtures.assets

Loader-backed Asset factory and aggregate fixtures.
"""
# Standard Libraries
from dataclasses import fields
from typing import Optional

# External Libraries
import pytest

# Application Libraries
from app.assets.base import Asset
from app.game.logic.relations import MaterialIndex
from app.models.config import ConfigurationSchema
from app.models.properties import PropertiesSchema
from app.models.state import (
    AssetState,
    StateSchema,
)
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
    mock_properties_schema: PropertiesSchema,
    mock_configurations_schema: ConfigurationSchema,
    mock_material_index: MaterialIndex,
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
        substrate: Optional[int] = None,
        **state_overrides,
    ) -> Asset:
        resolved_state = asset_state or state(
            category, instance, id=id, **state_overrides
        )
        prop_map = getattr(getattr(mock_properties_schema, category), instance)
        recipe = getattr(
            getattr(mock_configurations_schema.recipes, category), instance
        )
        properties = prop_map[resolved_state.id]
        resolved_substrate = (
            substrate
            if substrate is not None
            else mock_material_index.substrate(category, instance)
        )

        return AssetFactory.asset(
            category,
            instance,
            properties,
            resolved_state,
            recipe,
            substrate=resolved_substrate,
        )

    return _asset


@pytest.fixture
def mock_assets(
    asset,
    mock_state_schema: StateSchema,
) -> list[Asset]:
    """
    Materializes all entities declared in the YAML state test bed into Asset instances.
    """
    assets: list[Asset] = []
    for category in STATE_CATEGORIES:
        category_node = getattr(mock_state_schema, category, None)
        if category_node is None:
            continue
        for instance_field in fields(category_node):
            instance = instance_field.name
            for entity_state in getattr(category_node, instance):
                assets.append(
                    asset(category, instance, asset_state=entity_state)
                )
    return assets