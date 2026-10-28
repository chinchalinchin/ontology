"""
@domain.test
@test.unit
@app.config
@app.asset
@asset.state
@asset.property
@workflow.hydration

# Ontology: Tests - tests.unit.app.static.test_loader

Unit tests verifying YAML loading, Pydantic TypeAdapter validation,
Cython struct coercion, and StateSchema round-trip serialization.
"""
# Standard Libraries
from dataclasses import fields

# External Libraries
import pytest

pytestmark = [
    pytest.mark.app_config,
    pytest.mark.workflow_hydration
]

# Application Libraries
import app.static.settings as settings
from app.static.loader import Loader
from app.static.semantics import AssetCategories
from app.models.config import ConfigurationSchema
from app.models.properties import PropertiesSchema
from app.models.state import StateSchema

# Cython Libraries
from libs.core.models import Dimensions, Hitbox, Position


def test_load_properties_validates_schema_and_cython_structs(
    mock_properties: PropertiesSchema,
):
    """Verifies Loader.load_properties() coerces YAML dicts into PropertiesSchema and Cython Dimensions/Hitbox structs."""
    assert isinstance(mock_properties, PropertiesSchema)

    temperate = mock_properties.tiles.environ["temperate"]
    assert isinstance(temperate.dimensions, Dimensions)
    assert (temperate.dimensions.w, temperate.dimensions.l) == (32, 32)

    player = mock_properties.sheets.players["player"]
    assert player.hitboxes is not None
    assert isinstance(player.hitboxes[0], Hitbox)
    assert isinstance(player.hitboxes[0].position, Position)


def test_load_configurations_compiles_and_validates(
    mock_configurations: ConfigurationSchema,
):
    """Verifies Loader.load_configurations() produces a valid ConfigurationSchema."""
    assert isinstance(mock_configurations, ConfigurationSchema)
    assert mock_configurations.recipes.tiles.environ.frame == "seasonal"
    assert mock_configurations.recipes.crafts.struts.frame == "material"


def test_load_state_referential_integrity_against_properties(
    mock_state: StateSchema,
    mock_properties: PropertiesSchema,
):
    """
    Verifies every entity state loaded from the YAML state test bed references
    a valid prototype ID in PropertiesSchema and coerces Cython Position structs.
    """
    assert isinstance(mock_state, StateSchema)

    for category in (
        AssetCategories.TILES.value,
        AssetCategories.CRAFTS.value,
        AssetCategories.CURSORS.value,
        AssetCategories.EFFECTS.value,
        AssetCategories.OBJECTS.value,
        AssetCategories.RESOURCES.value,
        AssetCategories.SHEETS.value,
    ):
        state_cat = getattr(mock_state, category)
        prop_cat = getattr(mock_properties, category)

        for instance_field in fields(state_cat):
            instance = instance_field.name
            state_list = getattr(state_cat, instance)
            prop_map = getattr(prop_cat, instance)

            for entity_state in state_list:
                assert entity_state.id in prop_map, (
                    f"State {category}.{instance} references unknown property id '{entity_state.id}'"
                )
                if getattr(entity_state, "position", None) is not None:
                    assert isinstance(entity_state.position, Position)


def test_save_and_reload_state_roundtrip(
    mock_state: StateSchema,
    monkeypatch,
):
    """
    Verifies Loader.save_state() serializes Cython structs via PlainSerializer
    and reloads into an equivalent StateSchema.
    """
    slot_dir = settings.SAVE_DIR / "slot-01"
    monkeypatch.setattr("app.static.settings.SAVE_DIR", slot_dir)

    Loader.save_state("state", mock_state)
    assert (slot_dir / "state.yaml").is_file()

    monkeypatch.setattr("app.static.settings.STATE_DIR", settings.SAVE_DIR)
    reloaded = Loader.load_state("slot-01")

    assert isinstance(reloaded, StateSchema)
    assert reloaded.plots.current == mock_state.plots.current
    assert len(reloaded.sheets.players) == len(mock_state.sheets.players)
    assert reloaded.sheets.players[0].position.x == mock_state.sheets.players[0].position.x