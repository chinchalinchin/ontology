"""
@domain.test
@test.fixtures
@app.relations
@modality.material
@physics.fields
@physics.space
@workflow.injection

# Ontology: Test - tests.unit.fixtures.structures

Relational indices, property groups, and spatial structure fixtures.
"""
# Standard Libraries
from typing import Any

# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.game.board.modules.fields import MoistureField
from app.game.logic.relations import (
    MaterialIndex,
    ShorelineIndex,
)
from app.models.config import ConfigurationSchema
from app.models.groups import (
    EquipmentGroup,
    SpawnableGroup,
)
from app.models.properties import PropertiesSchema
from app.static.semantics import Relations

# Cython Libraries
from libs.core.math.space import Space

# ---------------------------------------------------------------------------
# -------------------------------------------------------- RELATIONAL INDICES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_shoreline_index(
    mock_properties_schema: PropertiesSchema,
) -> ShorelineIndex:
    return ShorelineIndex.from_properties(
        mock_properties_schema.geography.shorelines
    )


@pytest.fixture
def mock_material_index(
    mock_configurations_schema: ConfigurationSchema,
) -> MaterialIndex:
    return MaterialIndex.from_configuration(
        mock_configurations_schema.materials
    )


@pytest.fixture
def mock_relations(
    mock_shoreline_index: ShorelineIndex,
    mock_material_index: MaterialIndex,
) -> dict[str, Any]:
    return {
        Relations.SHORELINES.value: mock_shoreline_index,
        Relations.MATERIALS.value: mock_material_index,
    }


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- PROPERTY GROUPS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_spawnables(
    mock_properties_schema: PropertiesSchema,
) -> SpawnableGroup:
    return SpawnableGroup(
        projectiles=mock_properties_schema.cursors.projectiles,
        expressions=mock_properties_schema.cursors.expressions,
        collectables=mock_properties_schema.effects.collectables,
        hazards=mock_properties_schema.effects.hazards,
        passive=mock_properties_schema.effects.passive,
        struts=mock_properties_schema.crafts.struts,
        shorelines=mock_properties_schema.geography.shorelines,
    )


@pytest.fixture
def mock_equipment(
    mock_properties_schema: PropertiesSchema,
) -> EquipmentGroup:
    return EquipmentGroup(
        armor=mock_properties_schema.sheets.armor,
        weapons=mock_properties_schema.sheets.weapons,
        tools=mock_properties_schema.sheets.tools,
        utilities=mock_properties_schema.sheets.utilities,
        shields=mock_properties_schema.sheets.shields,
    )


# ---------------------------------------------------------------------------
# ---------------------------------------------- SPATIAL & FIELD STRUCTURES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_space_grid() -> Space:
    return Space(cell_size=64, max_entities=100)


@pytest.fixture
def mock_moisture_field() -> MoistureField:
    return MoistureField(
        sigma=settings.MOISTURE_DECAY_SIGMA,
        phi_0=settings.BASE_MOISTURE_POTENTIAL,
    )