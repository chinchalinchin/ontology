"""
# Ontology: tests.unit.fixtures.state

Mock Asset State Fixtures
"""
# External Libraries
import pytest

# Application Libraries

from app.models.state import (
    # -------- SCHEMA
    StateSchema, 
    # -------- INSTANCES
    SheetStateInstances,
    ObjectStateInstances, 
    CraftStateInstances,
    TileStateInstances,
    EffectStateInstances,
)


# ---------------------------------------------------------- STATE SCHEMAS

@pytest.fixture
def mock_craft_states(
    mock_property_state,
    mock_property_state_alt,
    mock_property_state_alt2,
    mock_bridge_state
) -> CraftStateInstances:
    return CraftStateInstances(
        struts = [
            mock_property_state,
            mock_property_state_alt,
            mock_property_state_alt2
        ],
        bridges = [
            mock_bridge_state
        ]
    )


@pytest.fixture
def mock_effect_states(
    mock_reactable_state,
    mock_fluid_state,
    mock_fluid_state_alt,
    mock_fluid_state_alt2
) -> EffectStateInstances:
    return EffectStateInstances(
        reactables = [ mock_reactable_state ],
        fluids = [ mock_fluid_state, mock_fluid_state_alt, mock_fluid_state_alt2 ],
    )


@pytest.fixture
def mock_sheet_states(
    mock_player_state,
    mock_sprite_state
) -> SheetStateInstances:
    return SheetStateInstances(
        players = [ mock_player_state ],
        sprites = [ mock_sprite_state ]
    )


@pytest.fixture
def mock_tile_states(
    mock_multiplier_state
) -> TileStateInstances:
    return TileStateInstances(
        back = [ mock_multiplier_state ]
    )


@pytest.fixture
def mock_object_states(
    mock_door_state,
    mock_container_state,
    mock_switch_state,
    mock_switch_state_alt
) -> ObjectStateInstances:
    return ObjectStateInstances(
        doors = [ mock_door_state ],
        chests = [ mock_container_state ],
        plates = [ mock_switch_state_alt ],
        gates = [ mock_switch_state ]
    )

# ---------------------------------------------------------------------------------

@pytest.fixture
def mock_state(
    mock_sheet_states,
    mock_tile_states,
    mock_craft_states,
    mock_object_states,
    mock_effect_states
):
    return StateSchema(
        effects = mock_effect_states,
        sheets = mock_sheet_states,
        tiles = mock_tile_states,
        crafts = mock_craft_states,
        objects = mock_object_states,
    )

