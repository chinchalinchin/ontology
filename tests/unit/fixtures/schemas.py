"""
@domain.test
@test.fixture
@app.asset
@app.config
@asset.property
@asset.state

# Ontology: Tests - tests.unit.fixtures.schemas

Loader-backed schema fixtures and lookup factories.
"""
# Standard Libraries
from dataclasses import replace
from typing import Optional

# External Libraries
import pytest

# Application Libraries
from app.config.loader import Loader
from app.models.config import ConfigurationSchema
from app.models.properties import AssetProperties, PropertiesSchema
from app.models.state import AssetState, StateSchema


@pytest.fixture
def mock_properties_schema() -> PropertiesSchema:
    return Loader.load_properties()


@pytest.fixture
def mock_configurations_schema(mock_properties: PropertiesSchema) -> ConfigurationSchema:
    return Loader.load_configurations(properties=mock_properties)


@pytest.fixture
def mock_state_schema(testbed: str) -> StateSchema:
    return Loader.load_state(testbed)


@pytest.fixture
def mock_properties(mock_properties_schema: PropertiesSchema):
    """
    Fixture factory to retrieve an AssetProperties instance by (category, instance, id).
    """
    def _prop(category: str, instance: str, id: Optional[str] = None) -> AssetProperties:
        bucket: dict[str, AssetProperties] = getattr(getattr(mock_properties_schema, category), instance)
        key = id if id is not None else next(iter(bucket.keys()))
        return bucket[key]

    return _prop


@pytest.fixture
def state(mock_state_schema: StateSchema, mock_properties_schema: PropertiesSchema):
    """
    Fixture factory to retrieve an AssetState by (category, instance, id) with optional field overrides.
    """
    def _state(
        category: str,
        instance: str,
        id: Optional[str] = None,
        **overrides,
    ) -> AssetState:
        cat_node = getattr(mock_state_schema, category, None)
        if cat_node is not None and hasattr(cat_node, instance):
            bucket: list[AssetState] = getattr(cat_node, instance)
            base = next((s for s in bucket if id is None or s.id == id), bucket[0])
        return replace(base, **overrides) if overrides else base

    return _state