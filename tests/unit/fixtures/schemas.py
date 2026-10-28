"""
@domain.test
@test.fixtures
@app.asset
@app.config
@app.schema
@asset.property
@asset.state
@workflow.injection

# Ontology: Test - tests.unit.fixtures.schemas

Loader-backed schema fixtures and lookup factories.
"""
# Standard Libraries
from dataclasses import fields, replace
from typing import Optional

# External Libraries
import pytest

# Application Libraries
from app.models.config import ConfigurationSchema
from app.models.properties import (
    AssetProperties,
    PropertiesSchema,
)
from app.models.state import (
    AssetState,
    StateSchema,
)
from app.static.loader import Loader


@pytest.fixture
def mock_properties_schema() -> PropertiesSchema:
    properties = Loader.load_properties()
    configurations = Loader.load_configurations(properties=properties)
    actions_map = {a.id: a.data for a in configurations.actions}

    for sheet_field in fields(properties.sheets):
        bucket = getattr(properties.sheets, sheet_field.name)
        for key, prop in bucket.items():
            if prop.actions in actions_map:
                bucket[key] = replace(prop, actions=actions_map[prop.actions])

    return properties


@pytest.fixture
def mock_configurations_schema(
    mock_properties_schema: PropertiesSchema,
) -> ConfigurationSchema:
    return Loader.load_configurations(properties=mock_properties_schema)


@pytest.fixture
def mock_state_schema(testbed: str) -> StateSchema:
    return Loader.load_state(testbed)


@pytest.fixture
def mock_properties(mock_properties_schema: PropertiesSchema):
    """
    Fixture factory to retrieve an AssetProperties instance by (category, instance, id).
    """
    def _prop(
        category: str,
        instance: str,
        id: Optional[str] = None,
    ) -> AssetProperties:
        bucket: dict[str, AssetProperties] = getattr(
            getattr(mock_properties_schema, category), instance
        )
        key = id if id is not None else next(iter(bucket.keys()))
        return bucket[key]

    return _prop


@pytest.fixture
def state(mock_state_schema: StateSchema):
    """
    Fixture factory to retrieve an AssetState by (category, instance, id) with optional field overrides.
    """
    def _state(
        category: str,
        instance: str,
        id: Optional[str] = None,
        **overrides,
    ) -> AssetState:
        cat_node = getattr(mock_state_schema, category)
        bucket: list[AssetState] = getattr(cat_node, instance)
        base = next((s for s in bucket if id is None or s.id == id), bucket[0])
        return replace(base, **overrides) if overrides else base

    return _state