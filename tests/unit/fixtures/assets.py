"""
@domain.test
@test.fixtures

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
from app.models.config import (
    ConfigurationSchema,
    MenuNode,
)
from app.models.properties import (
    AssetProperties,
    PropertiesSchema,
)
from app.models.state import (
    AssetState,
    IconState,
    MeterState,
    PaneState,
    StateSchema,
    TraversalState,
)
from app.services.factories.assets import AssetFactory
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Statuses,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Multiple,
)

STATE_CATEGORIES = (
    AssetCategories.TILES.value,
    AssetCategories.CRAFTS.value,
    AssetCategories.CURSORS.value,
    AssetCategories.EFFECTS.value,
    AssetCategories.OBJECTS.value,
    AssetCategories.RESOURCES.value,
    AssetCategories.SHEETS.value,
)


def _default_widget_state(
    instance: str,
    asset_id: str,
    properties: AssetProperties,
) -> AssetState:
    if instance == AssetInstances.PANES.value:
        return PaneState(
            id=asset_id,
            name=asset_id,
            multiple=Multiple(0, 0),
            span=Dimensions(
                2 * (properties.dimensions.w // 3),
                2 * (properties.dimensions.l // 3),
            ),
        )
    if instance == AssetInstances.BUTTONS.value:
        return TraversalState(
            id=asset_id,
            name=asset_id,
            status=Statuses.IDLE.value,
        )
    if instance == AssetInstances.METERS.value:
        return MeterState(
            id=asset_id,
            name=asset_id,
            reading_function=lambda: 50,
            unit_function=lambda: 100,
        )
    if instance == AssetInstances.ICONS.value:
        frames = getattr(properties, "frames", None) or []
        first_icon = frames[0] if frames else ""
        return IconState(
            id=asset_id,
            name=asset_id,
            icon_function=lambda: first_icon,
        )
    raise ValueError(f"Unsupported widget instance: '{instance}'")


@pytest.fixture
def mock_asset(
    mock_properties_schema: PropertiesSchema,
    mock_configurations_schema: ConfigurationSchema,
    mock_material_index: MaterialIndex,
    mock_state,
):
    """
    Instantiates an Asset (or Widget for category='widgets') via AssetFactory from the YAML-loaded schemas.
    """
    def _asset(
        category: str,
        instance: str,
        id: Optional[str] = None,
        asset_state: Optional[AssetState] = None,
    ) -> Asset:
        recipe = getattr(
            getattr(mock_configurations_schema.recipes, category),
            instance,
        )
        substrate = mock_material_index.substrate(instance)

        if instance != AssetInstances.PLAYERS.value:
            prop_map = getattr(
                getattr(mock_properties_schema, category),
                instance,
            )
        else:
            prop_map = getattr(
                getattr(mock_properties_schema, category),
                AssetInstances.SPRITES.value,
            )

        if category == AssetCategories.WIDGETS.value:
            if asset_state is None:
                resolved_id = id if id is not None else next(iter(prop_map.keys()))
                properties = prop_map[resolved_id]
                resolved_state = _default_widget_state(instance, resolved_id, properties)
            else:
                properties = prop_map[asset_state.id]
                resolved_state = asset_state

            node = MenuNode(
                id=resolved_state.id,
                name=resolved_state.name or resolved_state.id,
                instance=instance,
            )
            return AssetFactory.widget(
                node,
                properties,
                resolved_state,
                recipe,
                None,
            )

        resolved_state = asset_state or mock_state(category, instance, id=id)
        properties = prop_map[resolved_state.id]

        return AssetFactory.asset(
            category,
            instance,
            properties,
            resolved_state,
            recipe,
            substrate=substrate,
        )

    return _asset


@pytest.fixture
def mock_assets(
    mock_asset,
    mock_state_schema: StateSchema,
) -> list[Asset]:
    """
    Materializes all entities declared in the YAML state test bed into Asset instances.
    """
    assets: list[Asset] = []
    for category in STATE_CATEGORIES:
        category_node = getattr(mock_state_schema, category)
        for instance_field in fields(category_node):
            instance = instance_field.name
            for entity_state in getattr(category_node, instance):
                assets.append(
                    mock_asset(category, instance, asset_state=entity_state)
                )
    return assets