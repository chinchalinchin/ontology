"""
# Ontology: tests.unit.conftest
"""
# External Libraries
import pytest

from app.config.enums import ( 
    # -------- ASSET COMPONENTS
    FrameRecipe,
    AnimationRecipe,
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


# --------------------------------------------------------------------------
# ------------------------------------------------------ MOCK CONFIGURATIONS
# --------------------------------------------------------------------------

@pytest.fixture
def mock_composition_configuration() -> CompositionConfiguration:
    return {
        "test-house": CompositionConfiguration(
            root=CompositionPseudoState(
                strut=PropertyState(
                    id="frame-wood", 
                    name="base_house"
                ),
                components=StateSchema(
                    objects=ObjectStateInstances(
                        doors=[
                            DoorState(
                                id="door-front",
                                name="entrance",
                                position=Position(x=20, y=20),
                                out=Position(x=5, y=5),
                                outlayer="bind(root.layer)"
                            )
                        ]
                    )
                )
            ),
            branches=[
                CompositionPseudoState(
                    strut=PropertyState(
                        id="wall-blue", 
                        name="interior",
                        position=Position(x=10, y=10),
                        owner="bind(parent.owner)"
                    ),
                    components=StateSchema()
                )
            ]
        ),
        'brick-house': CompositionConfiguration(
            root=CompositionPseudoState(
                strut=PropertyState(id="frame-brick", name="house"),
                components=StateSchema(
                    objects=ObjectStateInstances(
                        doors=[
                            DoorState(
                                id="door-house",
                                name="entrance",
                                layer="0",
                                outlayer="brick-house-compose-layer",
                                position=Position(x=32, y=118),
                                out=Position(x=82, y=143)
                            )
                        ]
                    )
                )
            ),
            branches=[
                CompositionPseudoState(
                    strut=PropertyState(
                        id="wall-blue",
                        name="house-interior",
                        layer="brick-house-compose-layer",
                        position=Position(x=0, y=0),
                        owner="bind(root.owner)"
                    ),
                    components=StateSchema(
                        crafts=CraftStateInstances(
                            struts=[
                                PropertyState(
                                    id="floor-wood",
                                    name="house-floor",
                                    layer="brick-house-compose-layer",
                                    position=Position(x=0, y=96),
                                    owner="bind(root.owner)"
                                )
                            ]
                        ),
                        objects=ObjectStateInstances(
                            doors=[
                                DoorState(
                                    id="door-shadow",
                                    name="house-doorframe",
                                    layer="brick-house-compose-layer",
                                    outlayer="bind(root.layer)",
                                    position=Position(x=47, y=142),
                                    out=Position(x=43, y=163)
                                )
                            ]
                        )
                    )
                )
            ]
        )
    }


@pytest.fixture
def mock_recipes_configuration() -> RecipeConfiguration:
    """Complete RecipeConfiguration matching native engine schemas."""
    return RecipeConfiguration(
        cursors=CursorRecipe(
            projectiles=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            expressions=Recipe(
                frame=FrameRecipe.INDEX.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        crafts=CraftRecipe(
            struts=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        effects=EffectRecipe(
            collectables=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            ),
            hazards=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            ),
            passive=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            ),
            reactables=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.LIFECYCLE.value
            )
        ),
        objects=ObjectRecipe(
            chests=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.BINARY.value
            ),
            crates=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            doors=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            gates=Recipe(
                frame=FrameRecipe.ITERABLE.value, 
                animation=AnimationRecipe.BINARY.value
            ),
            plates=Recipe(
                frame=FrameRecipe.ITERABLE, 
                animation=AnimationRecipe.BINARY.value
            ),
            signs=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        sheets=SheetRecipe(
            sprites=Recipe(
                frame=FrameRecipe.SPRITE.value, 
                animation=AnimationRecipe.SPRITE.value
            ),
            players=Recipe(
                frame=FrameRecipe.SPRITE.value, 
                animation=AnimationRecipe.SPRITE.value
            ),
            pixies=Recipe(
                frame=FrameRecipe.STATE.value, 
                animation=AnimationRecipe.STATE.value
            )
        ),
        widgets=WidgetRecipe(
            pages=Recipe(
                frame=FrameRecipe.SINGLE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            buttons=Recipe(
                frame=FrameRecipe.TRAVERSAL.value, 
                animation=AnimationRecipe.TRAVERSAL.value
            ),
            meters=Recipe(
                frame=FrameRecipe.METER.value, 
                animation=AnimationRecipe.METER.value
            ),
            panes=Recipe(
                frame=FrameRecipe.NONE.value, 
                animation=AnimationRecipe.NONE.value
            ),
            icons=Recipe(
                frame=FrameRecipe.INDEX.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
        geography=GeographyRecipe(
            shorelines=Recipe(
                frame=FrameRecipe.SHORELINE.value, 
                animation=AnimationRecipe.NONE.value
            )
        ),
    )


@pytest.fixture 
def mock_plot_configuration():
    """
    """
    return {
        'town-locked': [
            PlotConfiguration(
                next='town-unlocked',
                conditions = ['plot.mayor_bribed' ]
            )
        ]   
    }


@pytest.fixture
def mock_intention_configuration():
    """
    Shared mock configurations covering various ISL edge cases.
    """
    return {
        "idle": [
            IntentionConfiguration(
                next="attack", 
                conditions=["sprite.health < 50"]
            ),
            IntentionConfiguration(
                next="wander", 
                conditions=["sprite.health >= 50"]
            )
        ],
        "attack": [
            IntentionConfiguration(
                next="idle", 
                conditions=["sprites['enemy'].dead"]
            )
        ],
        "find": [
            IntentionConfiguration(
                next="interact",
                conditions=["functions.is_near(sprite.pos, sprites['target'].pos, 10)"])
        ],
        "bad_syntax": [
            IntentionConfiguration(
                next="idle", 
                conditions=["sprite.health =="]
            ) # syntax error
        ]
    }


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
def mock_configurations(
    mock_recipes_configuration, 
    mock_mapping_configuration,
    mock_intention_configuration,
    mock_plot_configuration
):
    return ConfigurationSchema(
        mappings=mock_mapping_configuration,
        recipes=mock_recipes_configuration,
        intentions=mock_intention_configuration,
        plots=mock_plot_configuration
    )

