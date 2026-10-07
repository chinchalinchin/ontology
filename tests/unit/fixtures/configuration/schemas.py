"""
# Ontology: tests.unit.fixtures.configurations

Mock application configuration fixtures.
"""
# External Libraries
import pytest

from app.config.enums import ( 
    # -------- MECHANICS
    Mechanics,
    Executors,
    Relations
)
from app.models.config import (
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
    mock_plot_configuration,
    mock_stage_configuration
):
    return ConfigurationSchema(
        mappings=mock_mapping_configuration,
        recipes=mock_recipes_configuration,
        intentions=mock_intention_configuration,
        plots=mock_plot_configuration,
        mechanics=mock_mechanics_configuration,
        stages=mock_stage_configuration
    )