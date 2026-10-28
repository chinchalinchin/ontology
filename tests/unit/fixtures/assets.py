"""
# Ontology: tests.unit.fixtures.assets

Factory-driven Asset fixtures aligned with world-01 and current AssetProperties.
"""
# Standard Libraries
from dataclasses import fields
from typing import Optional

# External Libraries
import pytest

# Application Libraries
from app.assets.base import Asset
from app.models.state.core import AssetState
from app.services.factories.assets import AssetFactory
from app.static.semantics import AssetCategories

WORLD_ASSET_CATEGORIES = (
    AssetCategories.TILES.value,
    AssetCategories.CRAFTS.value,
    AssetCategories.EFFECTS.value,
    AssetCategories.OBJECTS.value,
    AssetCategories.RESOURCES.value,
    AssetCategories.SHEETS.value,
)

@pytest.fixture
def asset(
    mock_properties,
    mock_state,
    mock_recipes_configuration,
):
    """
    Fixture factory that instantiates an Asset via AssetFactory.asset.
    """
    def _asset(
        category: str,
        instance: str,
        state: Optional[AssetState] = None,
        name: Optional[str] = None,
    ) -> Asset:
        prop_map = getattr(getattr(mock_properties, category), instance)
        recipe = getattr(getattr(mock_recipes_configuration, category), instance)

        if state is None:
            states = getattr(getattr(mock_state, category), instance)
            if name is not None:
                state = next(
                    s for s in states if s.name == name or s.id == name
                )
            else:
                state = states[0]

        properties = prop_map[state.id]
        return AssetFactory.asset(
            category,
            instance,
            properties,
            state,
            recipe,
        )

    return _asset


@pytest.fixture
def mock_assets(asset, mock_state) -> list[Asset]:
    """
    Projects all world-01 StateSchema entities through the `asset` factory fixture.
    """
    assets: list[Asset] = []
    for category in WORLD_ASSET_CATEGORIES:
        category_node = getattr(mock_state, category)
        for instance_field in fields(category_node):
            instance = instance_field.name
            for state in getattr(category_node, instance):
                assets.append(asset(category, instance, state=state))
    return assets