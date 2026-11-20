"""
@domain.test
@test.fixtures

# Ontology: Tests - tests.unit.fixtures.structures

Relational indices, property groups, and spatial structure fixtures.
"""
# Standard Libraries
from dataclasses import fields
from typing import Any

# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.assets.base import (
    Asset,
    Taxonomy,
)
from app.game.logic.modules.fields import MoistureField
from app.game.logic.relations import (
    MaterialIndex,
    ProjectileIndex,
    ShorelineIndex,
)
from app.models.config import ConfigurationSchema
from app.models.groups import (
    EquipmentGroup,
    SpawnableGroup,
)
from app.models.properties import PropertiesSchema
from app.models.state import NoState
from app.services.factories import AssetFactory
from app.static.semantics import (
    AssetCategories,
    Relations,
)

# Cython Libraries
from libs.core.math.space import Space
from libs.core.models import (
    Boundary,
    Dimensions,
    Position,
)

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
def mock_projectile_index(
    mock_properties_schema: PropertiesSchema,
) -> ProjectileIndex:
    return ProjectileIndex.from_properties(
        mock_properties_schema.cursors.projectiles
    )


@pytest.fixture
def mock_relations(
    mock_shoreline_index: ShorelineIndex,
    mock_material_index: MaterialIndex,
    mock_projectile_index: ProjectileIndex,
) -> dict[str, Any]:
    return {
        Relations.SHORELINES.value: mock_shoreline_index,
        Relations.MATERIALS.value: mock_material_index,
        Relations.PROJECTILES.value: mock_projectile_index,
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
    mock_configurations_schema: ConfigurationSchema,
) -> EquipmentGroup:
    sheets_props = mock_properties_schema.sheets
    sheets_recipes = mock_configurations_schema.recipes.sheets
    equipment_groups = {}

    for eq_field in fields(EquipmentGroup):
        instance = eq_field.name
        props_dict = getattr(sheets_props, instance, {}) or {}
        recipe = getattr(sheets_recipes, instance)
        equipment_groups[instance] = {
            eq_id: Asset(
                taxonomy=Taxonomy(
                    id=eq_id,
                    name=eq_id,
                    category=AssetCategories.SHEETS.value,
                    instance=instance,
                ),
                properties=eq_props,
                state=NoState(),
                frame=AssetFactory.frame(recipe.frame),
                animation=AssetFactory.animation(recipe.animation),
                hitbox=AssetFactory.hitbox(recipe.hitbox),
            )
            for eq_id, eq_props in props_dict.items()
        }

    return EquipmentGroup(**equipment_groups)


# ---------------------------------------------------------------------------
# ---------------------------------------------- SPATIAL & FIELD STRUCTURES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_space_grid() -> Space:
    return Space(cell_size=64, max_entities=100)


@pytest.fixture
def mock_boundary() -> Boundary:
    return Boundary(Position(10, 20), Dimensions(30, 40))


@pytest.fixture
def mock_moisture_field() -> MoistureField:
    return MoistureField(
        sigma=settings.MOISTURE_DECAY_SIGMA,
        phi_0=settings.BASE_MOISTURE_POTENTIAL,
    )