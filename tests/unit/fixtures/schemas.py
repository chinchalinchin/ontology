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
import dataclasses
from dataclasses import replace
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
def mock_raw_properties_schema() -> PropertiesSchema:
    return Loader.load_properties()


@pytest.fixture
def mock_configurations_schema(
    mock_raw_properties_schema: PropertiesSchema,
) -> ConfigurationSchema:
    return Loader.load_configurations(properties=mock_raw_properties_schema)


@pytest.fixture
def mock_properties_schema(
    mock_raw_properties_schema: PropertiesSchema,
    mock_configurations_schema: ConfigurationSchema,
) -> PropertiesSchema:
    """
    Loads PropertiesSchema and pre-hydrates Sheet ActionSet references
    matching Builder._actions().
    """
    resolved_sheets = {}
    for sheet_field in dataclasses.fields(mock_raw_properties_schema.sheets):
        sheet_type = sheet_field.name
        sheet_dict = getattr(mock_raw_properties_schema.sheets, sheet_type, {})
        resolved_dict = {}
        for e_id, e_props in sheet_dict.items():
            if isinstance(e_props.actions, str):
                action_data = next(
                    (
                        a.data
                        for a in mock_configurations_schema.actions
                        if a.id == e_props.actions
                    ),
                    {},
                )
                resolved_dict[e_id] = replace(e_props, actions=action_data)
            else:
                resolved_dict[e_id] = e_props
        resolved_sheets[sheet_type] = resolved_dict

    return replace(
        mock_raw_properties_schema,
        sheets=replace(mock_raw_properties_schema.sheets, **resolved_sheets),
    )


@pytest.fixture
def mock_state_schema(testbed: str) -> StateSchema:
    return Loader.load_state(testbed)


@pytest.fixture
def properties(mock_properties_schema: PropertiesSchema):
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
def mock_properties(properties):
    """
    Alias for the properties lookup factory.
    """
    return properties


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
        cat_node = getattr(mock_state_schema, category, None)
        if cat_node is not None and hasattr(cat_node, instance):
            bucket: list[AssetState] = getattr(cat_node, instance)
            base = next(
                (s for s in bucket if id is None or s.id == id), bucket[0]
            )
            return replace(base, **overrides) if overrides else base
        raise KeyError(f"State node not found for ({category}, {instance})")

    return _state