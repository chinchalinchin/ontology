"""
# Ontology: tests.unit.fixtures.configurations

Mock application configuration fixtures.
"""
# External Libraries
import pytest

from app.config.enums import ( 
    # -------- ASSET COMPONENTS
    FrameRecipe,
    AnimationRecipe,
    # -------- MECHANICS
    Mechanics,
    Executors,
    Relations
)
from app.models.config import (
    # ------ COMPOSITIONS
    CompositionConfiguration, 
    CompositionPseudoState, 
    # ------ RECIPES
    RecipeConfiguration,
    CursorRecipe,
    CraftRecipe,
    WidgetRecipe,
    EffectRecipe,
    ObjectRecipe,
    GeographyRecipe,
    SheetRecipe,
    TileRecipe,
    Recipe,
    # ------- TRANSITION CONFIGURATION
    IntentionConfiguration,
    PlotConfiguration,
    # ------- DEVICES
    MappingConfiguration,
    DeviceMapping,
    WorldMapping,
    # ------- MENUS
    MenuMapping,
    # -------- MECHANICS
    MechanicsInstance,
    MechanicsConfiguration,
    # -------- SCHEMA
    ConfigurationSchema
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
# ------------------------------------------------------ MOCK CONFIGURATIONS
# --------------------------------------------------------------------------


@pytest.fixture
def mock_mapping_configuration() -> MappingConfiguration:
    return MappingConfiguration(
        keyboard = DeviceMapping(
        world=WorldMapping(
                menus = { 
                    'pause': 41 
                },
                intentions={
                    'attack': 44, 
                    'interact': 8
                },
                goals={
                    'up': 26, 
                    'down': 22
                }
            ),
            menu=MenuMapping(
                traversal={
                    'north': 79, 
                    'south': 80
                },
                interactions={
                    'select': 40, 
                    'cancel': 41
                }
            )
        )
    )


@pytest.fixture
def mock_mechanics_configuration() -> MechanicsConfiguration:
    return MechanicsConfiguration(
        core = [],
        world = [
            MechanicsInstance(
                key=Mechanics.TRANSITION.value, 
                executors=[
                    Executors.INTENTION.value
                ],
                relations=[]
            ),
            MechanicsInstance(
                key=Mechanics.MOTION.value,
                executors=[],
                relations=[]
            ),
            MechanicsInstance(
                key=Mechanics.FLUID.value,
                executors=[
                    Executors.ACTUATOR.value
                ],
                relations=[
                    Relations.SHORELINES.value
                ]
            )
        ]
    )

@pytest.fixture
def mock_configurations(
    mock_recipes_configuration, 
    mock_mapping_configuration,
    mock_mechanics_configuration,
    mock_intention_configuration,
    mock_plot_configuration
):
    return ConfigurationSchema(
        mappings=mock_mapping_configuration,
        recipes=mock_recipes_configuration,
        intentions=mock_intention_configuration,
        plots=mock_plot_configuration,
        mechanics=mock_mechanics_configuration
    )

