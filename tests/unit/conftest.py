import sys
from pathlib import Path

# Inject the src/ directory into the Python path prior to any local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import pytest
from app.models.properties import PropertiesSchema, SheetProperties
from app.models.config import (
    ConfigurationSchema, 
    MappingConfiguration, 
    Mapping,
    RecipeConfiguration,
    CursorRecipe,
    CraftRecipe
)
from app.models.state import StateSchema, SpriteState
from app.models.groups import SpawnableGroup
from libs.core.models import Dimensions, Position

@pytest.fixture
def mock_properties():
    props = PropertiesSchema()
    props.sheets.sprites["player"] = SheetProperties(
        dimensions=Dimensions(w=64, l=64),
        mass=7
    )
    return props

@pytest.fixture
def mock_configurations():
    return ConfigurationSchema(
        mappings=MappingConfiguration(keyboard=Mapping()),
        recipes=RecipeConfiguration(
            cursors=CursorRecipe(),
            crafts=CraftRecipe()
        )
    )

@pytest.fixture
def mock_state():
    state = StateSchema()
    state.sheets.sprites.append(
        SpriteState(
            id="player",
            name="player_1",
            layer="0",
            position=Position(x=10, y=10)
        )
    )
    return state

@pytest.fixture
def mock_spawnables():
    return SpawnableGroup(
        projectiles={},
        expressions={},
        temporary={},
        struts={}
    )