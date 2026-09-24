"""
# Ontology: tests.unit.conftest
"""
# Standard Libraries
import sys
from pathlib import Path
from unittest.mock import (
    MagicMock, 
    patch
)

# External Libraries
import pytest


# NOTE: Inject the src/ directory into the Python path prior to any local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


# Application Libraries
from app.assets.base import (
    Asset, 
    Taxonomy,
    Frame,
    Animation
)
from app.assets.frames import (
    FluidFrame,
    ShorelineFrame
)
from app.assets.animations import (
    LifecycleAnimation
)
from app.config.enums import ( 
    # -------- ASSET HIERARCHY
    AssetCategories, 
    AssetInstances,
    # -------- ASSET COMPONENTS
    FrameRecipe,
    AnimationRecipe,
    # -------- SPRITE FIELDS
    Intentions,
    Motivations,
    Directions,
    Goals,
    # -------- MENU STRUCTURES
    Bindings,
    # -------- ENGINE SUGAR
    Shortcuts,
)
from app.game.devices import Keyboard
from app.game.board import Board
from app.game.logic.relations import ShorelineIndex
from app.models.properties import (
    # -------- FIELDS
    RGBA,
    Outline,
    Cost,
    Lifecycle,
    # -------- MODELS
    ObjectProperties,
    SheetProperties,
    WidgetProperties,
    TileProperties,
    CraftProperties,
    ObjectProperties,
    GeographyProperties,
    EffectProperties,
    FontProperties,
    # -------- INSTANCES
    CraftPropertyInstances,
    SheetPropertyInstances,
    WidgetPropertyInstances,
    GeographyPropertyInstances,
    ObjectPropertyInstances,
    TilePropertyInstances,
    EffectPropertyInstances,
    # -------- SCHEMA
    PropertiesSchema,
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
    IntentionConfiguration,
    # ------- DEVICES
    MappingConfiguration,
    DeviceMapping,
    WorldMapping,
    # ------- MENUS
    MenuMapping,
    MenuNode,
    GizmoParameters,
    MenuBinding,
    # -------- SCHEMA
    ConfigurationSchema
)
from app.models.state import (
    # -------- SCHEMA
    StateSchema, 
    # -------- INSTANCES
    SheetStateInstances,
    ObjectStateInstances, 
    CraftStateInstances,
    TileStateInstances,
    EffectStateInstances,
    # -------- MODELS
    SpriteState,
    PlayerState,
    DoorState,
    MultiplierState,
    PropertyState,
    PositionalState,
    CollectionState,
    ShorelineState,
    FluidState,
    AnimationState,
    # -------- FIELDS
    Inventory,
    Equipment,
    Mutators,
    MutatorTriggers,
    MutatorParameters,
    RadialParameters,
    FearParameters,
    Character,
    Goal,
    Psyche
)
from app.models.groups import (
    SpawnableGroup,
    EquipmentGroup
)
from app.services.orchestration import (
    Builder, 
    Orchestrator
)
from app.services.generators.menus import (
    Provider,
    Binder
)
from app.services.generators.game import (
    Decomposer
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Multiple,
    Velocity,
    Hitbox,
    Boundary
)
from libs.core.math.space import Space


# ---------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK CLASSES
# ---------------------------------------------------------------------------


class DummyFrame(Frame):
    def channels(self, id, state, properties): return []
    def keys(self, id, state): return [id]
    def index(self, id, properties): return {}


class DummyAnimation(Animation):
    def animate(self, state, properties): return state


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK PROPERTIES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_font_properties() -> FontProperties:
    """FontProperties dataclass fixture for typography testing."""
    return FontProperties(
        size=24,
        alignment="left",
        color=RGBA(
            r=255,
            g=255, 
            b=255, 
            a=255
        ),
        outline=Outline(
            color=RGBA(
                r=0, 
                g=0, 
                b=0, 
                a=255
            ), 
            width=2
        ),
        bold=True,
        italics=False,
        underline=False,
        strikethrough=False,
        margins=0.05
    )


@pytest.fixture
def mock_tile_properties() -> TilePropertyInstances:
    return TilePropertyInstances(
        back = {
            'tile-1': TileProperties(
                dimensions=Dimensions(w=32, l=32)
            ),
            'grass': TileProperties(
                dimensions=Dimensions(w=32, l=32),
                friction=100
            )       
        }
    )


@pytest.fixture
def mock_craft_properties() -> CraftPropertyInstances:
    return CraftPropertyInstances(
        struts = {
            'frame-brick': CraftProperties(
                dimensions=Dimensions(w=96, l=190),
                cost=[
                    Cost(item="stone", quantity=10)
                ]
            ),
            'frame-wood': CraftProperties(
                dimensions=Dimensions(w=100, l=100),
                cost=[
                    Cost(item="wood", quantity=10)
                ]
            ),
            'wall-blue': CraftProperties(
                dimensions=Dimensions(w=128, l=96),
                cost=[
                    Cost(item="stone", quantity=5)
                ]
            ),
            'floor-wood': CraftProperties(
                dimensions=Dimensions(w=128, l=96),
                cost=[
                    Cost(item="wood", quantity=10)
                ]
            ),
            'strut-castle': CraftProperties(
                dimensions=Dimensions(w=222, l=133), 
                cost=[], 
                mass=0
            ),
            'strut-wall':  CraftProperties(
                dimensions=Dimensions(w=128, l=96), 
                cost=[], 
                mass=0
            ),
            'strut-floor': CraftProperties(
                dimensions=Dimensions(w=128, l=96), 
                cost=[], 
                mass=0
            )
        }
    )


@pytest.fixture
def mock_sheet_properties() -> SheetPropertyInstances:
    hb = Hitbox(Position(21, 23), Dimensions(22, 21))
    return SheetPropertyInstances(
        sprites = {
            "player": SheetProperties(
                dimensions=Dimensions(w=64, l=64),
                mass=7,
                hitboxes=[hb]
            ),
            'jasilynn':  SheetProperties(
                dimensions=Dimensions(w=64, l=64),
                mass=10,
                hitboxes=[hb]
            )
        }
    )


@pytest.fixture
def mock_object_properties() -> ObjectPropertyInstances:
    return ObjectPropertyInstances(
        doors = {
            "door-front": ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 32))],
                mass = -1
            ),
            'door-shadow': ObjectProperties(
                dimensions=Dimensions(w=32, l=48)
            ),
            'door-house': ObjectProperties(
                dimensions=Dimensions(w=32, l=48)
            )
        },
        crates = {
            'wood-crate': ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=5
            ) 
        },
        rafts = {
            'wood-raft': ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=5
            )
        }
    )


@pytest.fixture
def mock_effect_properties() -> EffectPropertyInstances:
    return EffectPropertyInstances(
        fluids = {
            'waterflow-01': EffectProperties(
                dimensions=Dimensions(w=32, l=32),
                count=3,
                mass=-1,
                lifecycle=Lifecycle(delay=60, persist=False)
            )
        }
    )


@pytest.fixture
def mock_widget_properties() -> WidgetPropertyInstances:
    """
    Standard widget properties fixture providing prototype dimensions for
    slot buttons and transparent slot overlay panes.
    """
    return WidgetPropertyInstances(
        icons = {
            "test-icon": WidgetProperties(
                dimensions=Dimensions(w=16, l=16), 
                frames=["sword"]
            ),
            "weapons": WidgetProperties(
                dimensions=Dimensions(w=32, l=32), 
                frames=["shortsword", "dagger"]
            )
        },
        panes={
            "test-pane": WidgetProperties(
                dimensions=Dimensions(w=200, l=200)
            ),
            "transparent-slot": WidgetProperties(
                dimensions=Dimensions(w=40, l=40)
            ),
            "neutral": WidgetProperties(
                dimensions=Dimensions(w=318, l=180)
            )
        },
        pages = {
            "test-page": WidgetProperties(
                dimensions=Dimensions(w=100, l=100) 
            )
        },
        buttons={
            "test-btn": WidgetProperties(
                dimensions=Dimensions(w=32, l=32)
            ),
            "slot": WidgetProperties(
                dimensions=Dimensions(w=40, l=40)
            ),
            "arrow-up": WidgetProperties(
                dimensions=Dimensions(w=24, l=24)
            ),
            "arrow-down": WidgetProperties(
                dimensions=Dimensions(w=24, l=24)
            )
        },
        meters = {
            "test-meter": WidgetProperties(
                dimensions=Dimensions(w=50, l=10)
            )
        }
    )


@pytest.fixture
def mock_geography_properties() -> GeographyPropertyInstances:
    """GeographyProperties dataclass fixture."""
    return GeographyPropertyInstances(
        shorelines = {
            "grassy-shore": GeographyProperties(
                dimensions=Dimensions(w=32, l=32),
                tile="tile-1",
                fluid="waterflow-1",
                thickness=8,
                mass=-1
            )
        }
    )


@pytest.fixture
def mock_properties(
    mock_geography_properties,
    mock_object_properties,
    mock_sheet_properties,
    mock_widget_properties,
    mock_craft_properties,
    mock_tile_properties
) -> PropertiesSchema:
    return PropertiesSchema(
        crafts = mock_craft_properties,
        geography = mock_geography_properties,
        objects = mock_object_properties,
        sheets = mock_sheet_properties,
        widgets = mock_widget_properties,
        tiles = mock_tile_properties
    )


# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK GROUPS 
# --------------------------------------------------------------------------


@pytest.fixture
def mock_equipment() -> EquipmentGroup:
    return EquipmentGroup(armor={}, tools={}, utilities={}, weapons={})


@pytest.fixture
def mock_spawnables(mock_geography_properties) -> SpawnableGroup:
    return SpawnableGroup(
        projectiles={},
        expressions={},
        collectables={},
        hazards={},
        struts={},
        passive={},
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
def mock_intention_configuration():
    """
    Shared mock configurations covering various ISL edge cases.
    """
    return {
        "idle": [
            IntentionConfiguration(next="attack", conditions=["sprite.health < 50"]),
            IntentionConfiguration(next="wander", conditions=["sprite.health >= 50"])
        ],
        "attack": [
            IntentionConfiguration(next="idle", conditions=["sprites['enemy'].dead"])
        ],
        "town-locked": [
            IntentionConfiguration(next="town-unlocked", conditions=["plot.mayor_bribed == True"])
        ],
        "find": [
            # BUGFIX: Route targeting through the standard 'sprites' ISL dictionary namespace 
            # instead of creating a custom root namespace.
            IntentionConfiguration(next="interact", conditions=["functions.is_near(sprite.pos, sprites['target'].pos, 10)"])
        ],
        "bad_syntax": [
            IntentionConfiguration(next="idle", conditions=["sprite.health =="]) # syntax error
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
    mock_intention_configuration
):
    return ConfigurationSchema(
        mappings=mock_mapping_configuration,
        recipes=mock_recipes_configuration,
        intentions=mock_intention_configuration
    )


# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK STATES
# --------------------------------------------------------------------------

@pytest.fixture
def mock_property_state() -> PropertyState:
    return PropertyState(
        id="strut-castle", 
        name="castle", layer="0", 
        position=Position(x=250, y=250)
    )


@pytest.fixture
def mock_property_state_alt() -> PropertyState:
    return PropertyState(
        id="strut-wall",
        name="wall",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=0)
    )


@pytest.fixture
def mock_property_state_alt2() -> PropertyState:
    return PropertyState(
        id="strut-floor",
        name="floor",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=96)
    )


@pytest.fixture
def mock_player_state() -> PlayerState:
    return PlayerState(
        id="player",
        name="player_1",
        layer="0",
        position=Position(x=10, y=10),
        character=Character(
            speed = 10,
            defense = 10,
            strength = 10
        )
    )


@pytest.fixture
def mock_sprite_state() -> SpriteState:
    return SpriteState(
        id="jasilynn",
        name="evil-empress-jasilynn",
        layer="brick-house-compose-layer",
        position=Position(x=175, y=200),
        intention=Intentions.FIND,
        psyche=Psyche(
            motivation=Motivations.CONQUEST.value, 
            persona="empress-jasilynn", 
            dialogue="greeting"
        ),
        mutators=Mutators(
            triggers=MutatorTriggers(vision=True),
            parameters=MutatorParameters(
                vision=RadialParameters(radius=128),
                action=RadialParameters(radius=25),
                fear=FearParameters(radius=128, limit=0.5, enemy=5)
            )
        ),
        inventory=Inventory(equipment=Equipment()),
        animation=AnimationState(frame=0, tick=1)
    )


@pytest.fixture
def mock_sprite_state_alt() -> SpriteState:
    return SpriteState(
        id="sprite", 
        name="npc", 
        layer="0",
        position=Position(60, 50),
        intention=Intentions.FIND,
        goal=Goal(
            name="target1", 
            category=Goals.POSITION.value, 
            layer="0", 
            position=Position(0, 50)
        ),
        character=Character(
            speed=10
        ),
        velocity=Velocity(-10.0, 0.0),
        inventory=Inventory(
            equipment=Equipment()
        ),
        animation=AnimationState()
    )


@pytest.fixture
def mock_multiplier_state() -> MultiplierState:
    return MultiplierState(
        id="tile-1",
        name="grass",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=10, ny=10)
    )


@pytest.fixture
def mock_shoreline_state() -> ShorelineState:
    return ShorelineState(
        id="grassy-shore",
        name="shoreline-1",
        layer="0",
        position=Position(x=70, y=0),
        height=0,
        depth=0,
        orientation=Directions.LEFT.value,
        length=32,
        thickness=8,
        bidirectional=True,
        parent_fluid="jasilynns-tears",
        hitboxes=[
            Hitbox(Position(0, 0), Dimensions(32, 8))
        ]
    )


@pytest.fixture
def mock_positional_state() -> PositionalState:
    return PositionalState(
        id="wood-crate", 
        layer="0", 
        position=Position(x=10, y=10), 
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_positional_state_alt() -> PositionalState:
    return PositionalState(
        id="wood-raft",
        layer="0",
        position=Position(x=70, y=50),
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_door_state() -> DoorState:
    return DoorState(
        id="door-front",
        layer="0",
        outlayer="brick-house-compose-layer",
        position=Position(x=100, y=100),
        out=Position(x=20, y=20)
    )


@pytest.fixture
def mock_fluid_state() -> FluidState:
    return FluidState(
        id="waterflow-1",
        name="jasilynns-tears",
        layer="0",
        position=Position(x=70, y=0),
        source=Directions.DOWN.value,
        flow=2,
        length=0,
        dirty=True
    )


@pytest.fixture
def mock_craft_states(
    mock_property_state,
    mock_property_state_alt,
    mock_property_state_alt2
) -> CraftStateInstances:
    return CraftStateInstances(
        struts = [
            mock_property_state,
            mock_property_state_alt,
            mock_property_state_alt2
        ]
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
    mock_back_tile
) -> TileStateInstances:
    return TileStateInstances(
        back = [ mock_back_tile ]
    )


@pytest.fixture
def mock_state(
    mock_sheet_states,
    mock_tile_states,
    mock_craft_states
):
    return StateSchema(
        sheets = mock_sheet_states,
        tiles = mock_tile_states,
        crafts = mock_craft_states
    )


# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK ASSETS
# --------------------------------------------------------------------------


@pytest.fixture
def mock_back_tile(
    mock_tile_properties,
    mock_multiplier_state
) -> Asset:
    return Asset(
        taxonomy = Taxonomy(
            id = "tile-1",
            name = "grass",
            category = AssetCategories.TILES.value, 
            instance = AssetInstances.BACK.value
        ), 
        properties = mock_tile_properties.back.get('tile-1'), 
        state = mock_multiplier_state, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_shoreline(
    mock_geography_properties,
    mock_shoreline_state
) -> Asset:
    """Shoreline sensor asset fixture."""
    return Asset(
        taxonomy = Taxonomy(
            id = "grassy-shore",
            name = "shoreline-1",
            category = AssetCategories.GEOGRAPHY.value,
            instance = AssetInstances.SHORELINES.value
        ), 
        properties = mock_geography_properties.shorelines.get('grassy-shore'), 
        state = mock_shoreline_state, 
        frame = ShorelineFrame(tile_w=32, tile_l=32),
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_sprite(
    mock_sheet_properties,
    mock_sprite_state
) -> Asset:
    """
    Sprite asset featuring a standard LPC offset collision hitbox.
    """
    return Asset(
        taxonomy = Taxonomy(
            id = "jasilynn", 
            name = "evil-empress-jasilynn", 
            category = AssetCategories.SHEETS.value, 
            instance = AssetInstances.SPRITES.value
        ), 
        properties = mock_sheet_properties.sprites.get('jasilynn'), 
        state = mock_sprite_state, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_player(
    mock_sheet_properties,
    mock_player_state
) -> Asset:
    return Asset(
        taxonomy=  Taxonomy(
            id = "player",
            name = "fakename",
            category = AssetCategories.SHEETS.value, 
            instance = AssetInstances.PLAYERS.value
        ), 
        properties = mock_sheet_properties.sprites.get('player'), 
        state = mock_player_state, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_strut(
    mock_craft_properties,
    mock_property_state
) -> Asset:
    return Asset(
        taxonomy = Taxonomy(
            id = "strut-castle", 
            name = "castle",
            category = AssetCategories.CRAFTS.value,
            instance = AssetInstances.STRUTS.value
        ), 
        properties = mock_craft_properties.struts.get('strut-castle'), 
        state = mock_property_state, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_strut_alt(
    mock_craft_properties,
    mock_property_state_alt
) -> Asset:
    # Layer "brick-house-compose-layer": Tileless Wall Strut (Extent: 0+128=128, 0+96=96)
    return Asset(
        taxonomy = Taxonomy(
            id = "strut-wall", 
            name = "wall", 
            category = AssetCategories.CRAFTS.value, 
            instance = AssetInstances.STRUTS.value
        ), 
        properties = mock_craft_properties.struts.get('strut-wall'),
        state = mock_property_state_alt, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_strut_alt2(
    mock_craft_properties,
    mock_property_state_alt2
) -> Asset:
    # Layer "brick-house-compose-layer": Tileless Floor Strut (Extent: 0+128=128, 96+96=192)
    return Asset(
        taxonomy = Taxonomy(
            id = "strut-floor", 
            name = "floor", 
            category = AssetCategories.CRAFTS.value, 
            instance = AssetInstances.STRUTS.value
        ), 
        properties = mock_craft_properties.struts.get('strut-floor'), 
        state = mock_property_state_alt2, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_raft(
    mock_object_properties,
    mock_positional_state_alt
):
    """
    Raft asset fixture for testing hydrodynamic drift and surface interception.
    """
    return Asset(
        taxonomy = Taxonomy(
            "raft-1",
            "wood-raft",
            AssetCategories.OBJECTS.value,
            AssetInstances.RAFTS.value
        ), 
        properties = mock_object_properties.rafts.get('wood-raft'), 
        state = mock_positional_state_alt, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_crate(
    mock_object_properties,
    mock_positional_state
):
    """
    Generic crate asset to support mechanics tests utilizing frictive motion.
    """
    return Asset(
        taxonomy = Taxonomy(
            id = "wood-crate", 
            name = "box", 
            category = AssetCategories.OBJECTS.value, 
            instance = AssetInstances.CRATES.value
        ), 
        properties = mock_object_properties.crates.get('wood-crate'),
        state = mock_positional_state, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )



@pytest.fixture
def mock_fluid(
    mock_effect_properties,
    mock_fluid_state
) -> Asset:
    """
    Standard directional fluid emitter asset configured with continuous lifecycle.
    """
    return Asset(
        taxonomy = Taxonomy(
            id = "waterflow-01",
            name = "jasilynns-tears",
            category = AssetCategories.EFFECTS.value,
            instance = AssetInstances.FLUIDS.value
        ), 
        properties = mock_effect_properties.fluids.get('waterflow-01'), 
        state = mock_fluid_state, 
        frame = FluidFrame(tile_w=32, tile_l=32), 
        animation = LifecycleAnimation()
    )


@pytest.fixture
def mock_door(
    mock_object_properties,
    mock_door_state
) -> Asset:
    """
    Door asset transitioning from layer '0' to layer 'brick-house-compose-layer'.
    """
    return Asset(
        taxonomy = Taxonomy(
            id = "door-front", 
            name = "wood-door", 
            category = AssetCategories.OBJECTS.value, 
            instance = AssetInstances.DOORS.value
        ), 
        properties = mock_object_properties.doors.get('door-front'), 
        state = mock_door_state, 
        frame = DummyFrame(), 
        animation = DummyAnimation()
    )


@pytest.fixture
def mock_assets(
    mock_player,
    mock_sprite,
    mock_back_tile,
    mock_fluid,
    mock_door,
    mock_crate,
    mock_strut,
    mock_strut_alt,
    mock_strut_alt2
):
    return [
        mock_sprite, 
        mock_back_tile,
        mock_player,
        mock_fluid,
        mock_door,
        mock_crate,
        mock_crate,
        mock_strut,
        mock_strut_alt,
        mock_strut_alt2
    ]


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK LIBRARIES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_registry() -> MagicMock:
    registry = MagicMock()
    registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 32, 32)
    return registry


@pytest.fixture
def mock_boundary() -> Boundary:
    """Boundary spatial constraint fixture."""
    return Boundary(Position(10, 20), Dimensions(30, 40))


@pytest.fixture
def mock_space_grid() -> Space:
    """
    Fixture providing an initialized Cython Space grid for testing 
    O(1) bucket lookups and broad-phase physics.
    """
    return Space(cell_size=64, max_entities=100)


# ---------------------------------------------------------------------------
# ------------------------------------------------------------- MOCK SERVICES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_decomposer(
    mock_composition_configuration, 
    mock_recipes_configuration,
    mock_properties,
) -> Decomposer:
    # 1. Setup mock properties with costs for aggregation
    return Decomposer(
        compositions=mock_composition_configuration, 
        properties=mock_properties,
        recipes=mock_recipes_configuration
    )


@pytest.fixture
def mock_binder(mock_registry) -> Binder:
    return Binder(
        registry=mock_registry, 
        library=MagicMock()
    )


@pytest.fixture
def mock_builder(
    mock_properties, 
    mock_configurations, 
    mock_state
):
    with patch('app.services.orchestration.builder.Loader') as mock_loader:
        mock_loader.load_properties.return_value = mock_properties
        mock_loader.load_configurations.return_value = mock_configurations
        mock_loader.load_state.return_value = mock_state
        
        yield Builder()


@pytest.fixture
def mock_orchestrator(mock_builder) -> Orchestrator:
    return Orchestrator(mock_builder)


@pytest.fixture
def mock_provider(
    mock_binder, 
    mock_recipes_configuration, 
    mock_widget_properties
) -> Provider:
    return Provider(
        recipes=mock_recipes_configuration.widgets, 
        properties=mock_widget_properties, 
        binder=mock_binder
    )


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK COMPONENTS
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_board(
    mock_assets, 
    mock_configurations, 
    mock_equipment
) -> Board:    
    with patch('app.game.board.settings.TILE_HASH_SIZE', 32):
        board = Board(
            assets=mock_assets, 
            configurations=mock_configurations, 
            equipment=mock_equipment
        )
        board.perimeters["0"] = [
            Boundary(Position(0, 0), Dimensions(320, 1)),
            Boundary(Position(0, 319), Dimensions(320, 1)),
            Boundary(Position(0, 0), Dimensions(1, 320)),
            Boundary(Position(319, 0), Dimensions(1, 320))
        ]
        return board


@pytest.fixture
def mock_keyboard(
    mock_mapping_configuration
) -> Keyboard:
    return Keyboard(mock_mapping_configuration.keyboard)

@pytest.fixture
def mock_shoreline_index(mock_geography_properties):
    """ShorelineIndex fixture compiled from mock properties."""
    return ShorelineIndex.from_properties(mock_geography_properties.shorelines)


# -----------------------------------------------------------------------------
# -------------------------------------------------------- PATHFINDING FIXTURES

@pytest.fixture
def mock_offset_hitbox_asset():
    """
    Asset with single offset collision hitbox and mass=0 (e.g. wall-blue).
    """
    tax = Taxonomy("wall-blue-1", "blue-wall", AssetCategories.CRAFTS.value, AssetInstances.STRUTS.value)
    hb = Hitbox(Position(6, 17), Dimensions(116, 54))
    props = CraftProperties(
        dimensions=Dimensions(w=128, l=96),
        cost=[],
        mass=0,
        hitboxes=[hb]
    )
    state = PropertyState(
        id="wall-blue-1",
        layer="brick-house-compose-layer",
        position=Position(x=150, y=150),
        owner="player"
    )
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())


@pytest.fixture
def mock_multi_hitbox_asset():
    """
    Asset with multiple discrete hitboxes and mass=0 (e.g. wall-castle).
    """
    tax = Taxonomy("wall-castle-1", "castle-wall", AssetCategories.CRAFTS.value, AssetInstances.STRUTS.value)
    hb1 = Hitbox(Position(178, 102), Dimensions(25, 12))
    hb2 = Hitbox(Position(17, 102), Dimensions(25, 12))
    hb3 = Hitbox(Position(5, 39), Dimensions(203, 63))
    props = CraftProperties(
        dimensions=Dimensions(w=222, l=133),
        cost=[],
        mass=0,
        hitboxes=[hb1, hb2, hb3]
    )
    state = PropertyState(
        id="wall-castle-1",
        layer="0",
        position=Position(x=250, y=250),
        owner="player"
    )
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())


# -----------------------------------------------------------------------------
# -------------------------------------------------------- MOCK MENU COMPONENTS

@pytest.fixture
def mock_gizmo_node():
    return MenuNode(
        id="weapons",
        name="inventory-pack-grid",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(
            schema=Bindings.COLLECTION.value,
            target={"source": "context.inventory.pack"}
        ),
        parameters=GizmoParameters(
            capacity=8,
            columns=4,
            pane="transparent-slot",
            button="slot",
            gap=5
        )
    )


@pytest.fixture
def mock_collection_state():
    return CollectionState(
        collection_function=lambda: ["shortsword", "dagger", "buckler"],
        capacity=8,
        columns=4,
        offset=0
    )