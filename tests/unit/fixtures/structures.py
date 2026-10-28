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
from typing import Any, Optional

# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.game.board.modules.cache import Cache
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
    """
    ShorelineIndex compiled from application geography properties.
    """
    return ShorelineIndex.from_properties(
        mock_properties_schema.geography.shorelines
    )


@pytest.fixture
def mock_material_index(
    mock_configurations_schema: ConfigurationSchema,
) -> MaterialIndex:
    """
    MaterialIndex compiled from application material configurations.
    """
    return MaterialIndex.from_configuration(
        mock_configurations_schema.materials
    )


@pytest.fixture
def mock_relations(
    mock_shoreline_index: ShorelineIndex,
    mock_material_index: MaterialIndex,
) -> dict[str, Any]:
    """
    Assembled relational index mapping matching Builder.build_relations().
    """
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
    """
    SpawnableGroup aggregating dynamic runtime asset properties for Cradle.
    """
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
    """
    EquipmentGroup aggregating sheet equipment properties for Board.
    """
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
def space():
    """
    Fixture factory initializing a Cython Space broad-phase partitioning grid.
    """
    def _space(cell_size: int = 64, max_entities: int = 200) -> Space:
        return Space(cell_size=cell_size, max_entities=max_entities)

    return _space


@pytest.fixture
def mock_space_grid(space) -> Space:
    """
    Default initialized Cython Space grid instance.
    """
    return space()


@pytest.fixture
def moisture_field():
    """
    Fixture factory initializing an unmutated hydrological MoistureField.
    """
    def _moisture_field(
        sigma: float = settings.MOISTURE_DECAY_SIGMA,
        phi_0: float = settings.BASE_MOISTURE_POTENTIAL,
    ) -> MoistureField:
        return MoistureField(sigma=sigma, phi_0=phi_0)

    return _moisture_field


@pytest.fixture
def mock_moisture_field(moisture_field) -> MoistureField:
    """
    Default unmutated MoistureField instance configured with runtime settings.
    """
    return moisture_field()


@pytest.fixture
def cache():
    """
    Fixture factory initializing a Board Cache with optional initial asset indexing.
    """
    def _cache(assets: Optional[list[Asset]] = None) -> Cache:
        instance = Cache()
        if assets:
            instance.index_batch(assets)
        return instance

    return _cache


@pytest.fixture
def mock_cache(cache) -> Cache:
    """
    Default empty Board Cache instance.
    """
    return cache()