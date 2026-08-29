"""
# Ontology: tests.unit.conftest.py
"""
# Standard Libraries
import sys
from pathlib import Path
from unittest.mock import patch

# NOTE: Inject the src/ directory into the Python path prior to any local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

# External Libraries
import pytest

# Applicaiton Libraries
from app.models.properties import (
    PropertiesSchema, 
    SheetProperties,
    WidgetProperties
)
from app.models.config import (
    ConfigurationSchema, 
    MappingConfiguration, 
    DeviceMapping,
    WorldMapping,
    MenuMapping,
    RecipeConfiguration,
    CursorRecipe,
    CraftRecipe,
    WidgetRecipe,
    Recipe
)
from app.config.enums import ( 
    FrameRecipe,
    AnimationRecipe
)
from app.models.state import (
    StateSchema, 
    SpriteState
)
from app.hooks.orchestrator import Orchestrator
from app.hooks.provider import Provider
from app.models.groups import SpawnableGroup

from unittest.mock import MagicMock, patch

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position
)

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
        mappings=MappingConfiguration(
            keyboard=DeviceMapping(
                world=WorldMapping(),
                menu=MenuMapping()
            )
        ),
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

@pytest.fixture
def mock_mapping() -> DeviceMapping:
    """
    Provides a mock input mapping configuration.
    """
    return DeviceMapping(
        world=WorldMapping(
            intentions={'attack': 44, 'interact': 8},
            goals={'up': 26, 'down': 22}
        ),
        menu=MenuMapping()
    )

@pytest.fixture
def mock_orchestrator(mock_properties, mock_configurations, mock_state):
    # Patch the loader before initializing the orchestrator so it doesn't touch the filesystem
    with patch('app.hooks.orchestrator.Loader') as mock_loader:
        mock_loader.load_properties.return_value = mock_properties
        mock_loader.load_configurations.return_value = mock_configurations
        mock_loader.load_state.return_value = mock_state
        
        yield Orchestrator(state="world-01")

@pytest.fixture
def mock_provider():
    recipes = WidgetRecipe(
        pages=Recipe(frame=FrameRecipe.SINGLE),
        buttons=Recipe(frame=FrameRecipe.TRAVERSAL, animation=AnimationRecipe.TRAVERSAL),
        meters=Recipe(frame=FrameRecipe.METER, animation=AnimationRecipe.METER),
        panes=Recipe(frame=FrameRecipe.NONE)
    )
    properties = MagicMock()
    properties.pages = {"test-page": WidgetProperties(dimensions=Dimensions(w=100, l=100))}
    properties.buttons = {"test-btn": WidgetProperties(dimensions=Dimensions(w=32, l=32))}
    properties.meters = {"test-meter": WidgetProperties(dimensions=Dimensions(w=50, l=10))}
    properties.panes = {"test-pane": WidgetProperties(dimensions=Dimensions(w=200, l=200))}
    registry = MagicMock()
    
    return Provider(recipes=recipes, properties=properties, registry=registry)
