"""
# Ontology: tests.unit.fixtures.configurations

Mock application configuration fixtures.
"""
# External Libraries
import pytest


from app.models.config import (
    # ------ COMPOSITIONS
    CompositionConfiguration, 
    CompositionPseudoState, 
)
from app.models.state import (
    # -------- SCHEMA
    StateSchema, 
    # -------- INSTANCES
    ObjectStateInstances, 
    CraftStateInstances,
    # -------- MODELS
    DoorState,
    PropertyState
)
from app.models.groups import (
    SpawnableGroup,
    EquipmentGroup
)

# Cython Libraries
from libs.core.models import Position


# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK GROUPS 
# --------------------------------------------------------------------------


@pytest.fixture
def mock_equipment(mock_sheet_properties) -> EquipmentGroup:
    return EquipmentGroup(
        armor={}, 
        tools={}, 
        utilities={}, 
        weapons=mock_sheet_properties.weapons
    )


@pytest.fixture
def mock_spawnables(
    mock_cursor_properties,
    mock_geography_properties,
    mock_effect_properties,
    mock_craft_properties,
) -> SpawnableGroup:
    return SpawnableGroup(
        projectiles=mock_cursor_properties.projectiles,
        expressions=mock_cursor_properties.expressions,
        collectables=mock_effect_properties.collectables,
        hazards=mock_effect_properties.hazards,
        struts=mock_craft_properties.struts,
        passive=mock_effect_properties.passive,
        shorelines=mock_geography_properties.shorelines
    )
