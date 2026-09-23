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


# Applicaiton Libraries
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
    # -------- MENU STRUCTURES
    Bindings,
    # -------- ENGINE SUGAR
    Shortcuts,
)
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
    ObjectStateInstances, 
    CraftStateInstances,
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
    Meters,
    Meter,
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
    return

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
                cost=[Cost(item="wood", quantity=10)]
            )
        }
    )


@pytest.fixture
def mock_sheet_properties() -> SheetPropertyInstances:
    return SheetPropertyInstances(
        sprites = {
            "player": SheetProperties(
                dimensions=Dimensions(w=64, l=64),
                mass=7
            )
        }
    )


@pytest.fixture
def mock_object_properties() -> ObjectPropertyInstances:
    return ObjectPropertyInstances(
        doors = {
            "door-front": ObjectProperties(
                dimensions=Dimensions(w=32, l=32)
            ),
            'door-shadow': ObjectProperties(
                dimensions=Dimensions(w=32, l=48)
            ),
            'door-house': ObjectProperties(
                dimensions=Dimensions(w=32, l=48)
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


# --------------------------------------------------------------------------
# ------------------------------------------------------ MOCK CONFIGURATIONS
# --------------------------------------------------------------------------


@pytest.fixture
def mock_composition_configuration():
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
def mock_recipes():
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


# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK ASSETS
# --------------------------------------------------------------------------


@pytest.fixture
def mock_tile() -> Asset:
    tile_tax = Taxonomy(
        "tile-1",
        "grass",
        AssetCategories.TILES.value, 
        AssetInstances.BACK.value
    )
    tile_props = TileProperties(
        dimensions=Dimensions(w=32, l=32)
    )
    tile_state = MultiplierState(
        id="tile-1",
        name="grass",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=10, ny=10)
    )
    return Asset(tile_tax, tile_props, tile_state, DummyFrame(), DummyAnimation())


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK LIBRARIES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_registry() -> MagicMock:
    registry = MagicMock()
    registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 32, 32)
    return registry


# ---------------------------------------------------------------------------
# ------------------------------------------------------------- MOCK SERVICES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_decomposer(
    mock_composition_configuration, 
    mock_properties, 
    mock_recipes
) -> Decomposer:
    # 1. Setup mock properties with costs for aggregation
    return Decomposer(
        compositions=mock_composition_configuration, 
        properties=mock_properties,
        recipes=mock_recipes
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
    mock_recipes, 
    mock_widget_properties
) -> Provider:
    return Provider(
        recipes=mock_recipes.widgets, 
        properties=mock_widget_properties, 
        binder=mock_binder
    )


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK COMPONENTS
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_board(mock_board_assets, mock_configurations, mock_equipment):    
    with patch('app.game.board.settings.TILE_HASH_SIZE', 32):
        return Board(
            assets=mock_board_assets, 
            configurations=mock_configurations, 
            equipment=mock_equipment
        )


@pytest.fixture
def mock_fluid_board(mock_fluid, mock_crate, mock_configurations):
    """
    Board pre-hydrated with a fluid emitter, dynamic crate, and terrain tiles.
    """
    tile_tax = Taxonomy(
        "tile-1",
        "grass",
        AssetCategories.TILES.value, 
        AssetInstances.BACK.value
    )
    tile_props = TileProperties(dimensions=Dimensions(w=32, l=32))
    tile_state = MultiplierState(
        id="tile-1",
        name="grass",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=10, ny=10)
    )
    tile = Asset(tile_tax, tile_props, tile_state, DummyFrame(), DummyAnimation())
    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={}, shields={})

    with patch("app.game.board.settings.TILE_HASH_SIZE", 32):
        board = Board(
            assets=[
                tile, 
                mock_fluid, 
                mock_crate
            ],
            configurations=mock_configurations,
            equipment=equipment
        )
        board.perimeters["0"] = [
            Boundary(Position(0, 0), Dimensions(320, 1)),
            Boundary(Position(0, 319), Dimensions(320, 1)),
            Boundary(Position(0, 0), Dimensions(1, 320)),
            Boundary(Position(319, 0), Dimensions(1, 320))
        ]
        return board

# ---------------------------------------------------------------------------
# ----------------------------------------------- CROSS-LAYER FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_multi_layer_board(mock_configurations):
    """
    Board pre-hydrated across Layer 0 (mixed tiles and crafts) and a tileless interior layer.
    """
    # Layer 0: Tile Asset (Extent: 320x320)
    tile_tax = Taxonomy(
        "tile-grass", 
        "grass", 
        AssetCategories.TILES.value, 
        AssetInstances.BACK.value
    )
    tile_props = TileProperties(dimensions=Dimensions(w=32, l=32))
    tile_state = MultiplierState(
        id="tile-grass",
        name="grass",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=10, ny=10)
    )
    tile = Asset(tile_tax, tile_props, tile_state, DummyFrame(), DummyAnimation())

    # Layer 0: Castle Wall Strut (Extent: 250+222=472, 250+133=383)
    strut0_tax = Taxonomy(
        "strut-castle", 
        "castle",
        AssetCategories.CRAFTS.value,
        AssetInstances.STRUTS.value
    )
    strut0_props = CraftProperties(
        dimensions=Dimensions(w=222, l=133), 
        cost=[], 
        mass=0
    )
    strut0_state = PropertyState(
        id="strut-castle", 
        name="castle", layer="0", 
        position=Position(x=250, y=250)
    )
    strut0 = Asset(
        strut0_tax, 
        strut0_props, 
        strut0_state, 
        DummyFrame(), 
        DummyAnimation()
    )

    # Layer "brick-house-compose-layer": Tileless Wall Strut (Extent: 0+128=128, 0+96=96)
    interior_wall_tax = Taxonomy(
        "strut-wall", 
        "wall", 
        AssetCategories.CRAFTS.value, 
        AssetInstances.STRUTS.value
    )
    interior_wall_props = CraftProperties(
        dimensions=Dimensions(w=128, l=96), 
        cost=[], 
        mass=0
    )
    interior_wall_state = PropertyState(
        id="strut-wall",
        name="wall",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=0)
    )
    interior_wall = Asset(
        interior_wall_tax, 
        interior_wall_props,
        interior_wall_state, 
        DummyFrame(), 
        DummyAnimation()
    )

    # Layer "brick-house-compose-layer": Tileless Floor Strut (Extent: 0+128=128, 96+96=192)
    interior_floor_tax = Taxonomy(
        "strut-floor", 
        "floor", 
        AssetCategories.CRAFTS.value, 
        AssetInstances.STRUTS.value
    )
    interior_floor_props = CraftProperties(
        dimensions=Dimensions(w=128, l=96), 
        cost=[], 
        mass=0
    )
    interior_floor_state = PropertyState(
        id="strut-floor",
        name="floor",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=96)
    )
    interior_floor = Asset(
        interior_floor_tax, 
        interior_floor_props, 
        interior_floor_state, 
        DummyFrame(), 
        DummyAnimation()
    )

    equipment = EquipmentGroup(armor={}, tools={}, utilities={}, weapons={}, shields={})

    with patch("app.game.board.settings.TILE_HASH_SIZE", 32):
        return Board(
            assets=[tile, strut0, interior_wall, interior_floor],
            configurations=mock_configurations,
            equipment=equipment
        )
    
# ---------------------------------------------------------------------------
# ------------------------------------------------------- MOCK CONFIGURATIONS

@pytest.fixture
def mock_mapping() -> DeviceMapping:
    """Base keyboard mapping."""
    return DeviceMapping(
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


@pytest.fixture
def mock_configurations(mock_recipes, mock_mapping):
    return ConfigurationSchema(
        mappings=mock_mapping,
        recipes=mock_recipes
    )


@pytest.fixture
def mock_spawnables(mock_geography_properties):
    return SpawnableGroup(
        projectiles={},
        expressions={},
        collectables={},
        hazards={},
        struts={},
        passive={},
        shorelines={
            "grassy-shore": mock_geography_properties
        }
    )


@pytest.fixture
def mock_isl_configs():
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


# ---------------------------------------------------------------------------
# ------------------------------------------------------ MOCK DATA STRUCTURES

@pytest.fixture
def mock_shoreline_index(mock_geography_properties):
    """ShorelineIndex fixture compiled from mock properties."""
    return ShorelineIndex.from_properties({
        "grassy-shore": mock_geography_properties
    })

@pytest.fixture
def mock_shoreline():
    """Shoreline sensor asset fixture."""
    tax = Taxonomy(
        "grassy-shore",
        "shoreline-1",
        AssetCategories.GEOGRAPHY.value,
        AssetInstances.SHORELINES.value
    )
    props = GeographyProperties(
        dimensions=Dimensions(w=32, l=32),
        tile="tile-1",
        fluid="waterflow-1",
        thickness=8,
        mass=-1
    )
    hb = Hitbox(Position(0, 0), Dimensions(32, 8))
    state = ShorelineState(
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
        hitboxes=[hb]
    )
    return Asset(tax, props, state, ShorelineFrame(tile_w=32, tile_l=32), DummyAnimation())

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
def mock_boundary():
    """Boundary spatial constraint fixture."""
    return Boundary(Position(10, 20), Dimensions(30, 40))


@pytest.fixture
def mock_board_assets():
    # 1. Dynamic Asset (Sprite) - Use primitive strings for taxonomy matching Orchestrator initialization
    sprite_tax = Taxonomy("sprite-1", "npc", AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    sprite_props = SheetProperties(dimensions=Dimensions(w=32, l=32), mass=10)
    sprite_state = SpriteState(
        id="sprite-1", 
        name="npc", 
        layer="0", 
        position=Position(x=10, y=10),
        intention=Intentions.IDLE,
        psyche=Psyche(motivation=Motivations.CONQUEST.value, expression="none", dialogue="none", persona="test"),
        mutators=Mutators(
            triggers=MutatorTriggers(),
            parameters=MutatorParameters(
                fear=FearParameters(radius=50, limit=0.2, enemy=1),
                vision=RadialParameters(radius=100),
                action=RadialParameters(radius=10)
            )
        ),
        inventory=Inventory(equipment=Equipment()),
        animation=AnimationState(frame=0, tick=0)
    )
    sprite = Asset(sprite_tax, sprite_props, sprite_state, DummyFrame(), DummyAnimation())

    # 2. Static Asset (Tile)
    tile_tax = Taxonomy("tile-1", "grass", AssetCategories.TILES.value, AssetInstances.BACK.value)
    tile_props = TileProperties(dimensions=Dimensions(w=32, l=32))
    tile_state = MultiplierState(
        id="tile-1", name="grass", layer="0", position=Position(x=0, y=0), multiple=Multiple(nx=2, ny=2)
    )
    tile = Asset(tile_tax, tile_props, tile_state, DummyFrame(), DummyAnimation())
    
    # 3. Dynamic Asset (Player)
    player_tax = Taxonomy("player-1", "hero", AssetCategories.SHEETS.value, AssetInstances.PLAYERS.value)
    player_props = SheetProperties(dimensions=Dimensions(w=32, l=32), mass=10)
    player_state = PlayerState(
        id="player-1", 
        name="hero", 
        layer="0", 
        position=Position(x=10, y=10),
        inventory=Inventory(equipment=Equipment()),
        mutators=Mutators(triggers=MutatorTriggers()),
        character=Character(speed=5, strength=10, defense=10),
        meters=Meters(health=Meter(current=100, maximum=100), magic=Meter(current=100, maximum=100)),
        animation=AnimationState(frame=0, tick=0)
    )
    player = Asset(player_tax, player_props, player_state, DummyFrame(), DummyAnimation())
    
    return [sprite, tile, player]


@pytest.fixture
def mock_crate():
    """
    Generic crate asset to support mechanics tests utilizing frictive motion.
    """
    tax = Taxonomy("crate-1", "box", AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    props = SheetProperties(dimensions=Dimensions(w=32, l=32), mass=5) 
    state = PositionalState(
        id="crate-1", layer="0", position=Position(x=10, y=10), velocity=Velocity(vx=0.0, vy=0.0)
    )
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())

@pytest.fixture
def mock_raft():
    """
    Raft asset fixture for testing hydrodynamic drift and surface interception.
    """
    tax = Taxonomy(
        "raft-1",
        "wood-raft",
        AssetCategories.OBJECTS.value,
        AssetInstances.RAFTS.value
    )
    props = ObjectProperties(dimensions=Dimensions(w=32, l=32), mass=5)
    state = PositionalState(
        id="raft-1",
        layer="0",
        position=Position(x=70, y=50),
        velocity=Velocity(vx=0.0, vy=0.0)
    )
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())

@pytest.fixture
def mock_space_grid():
    """
    Fixture providing an initialized Cython Space grid for testing 
    O(1) bucket lookups and broad-phase physics.
    """
    return Space(cell_size=64, max_entities=100)


@pytest.fixture
def mock_strut():
    """
    Generic strut asset to support perimeter generator tests for CRAFTS.
    """
    tax = Taxonomy("strut-1", "wall", AssetCategories.CRAFTS.value, AssetInstances.STRUTS.value)
    props = CraftProperties(dimensions=Dimensions(w=32, l=32), cost=[], mass=0) 
    state = PropertyState(
        id="strut-1", layer="0", position=Position(x=40, y=40), owner="player"
    )
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())


@pytest.fixture
def mock_fluid():
    """
    Standard directional fluid emitter asset configured with continuous lifecycle.
    """
    tax = Taxonomy(
        "waterflow-1",
        "jasilynns-tears",
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value
    )
    props = EffectProperties(
        dimensions=Dimensions(w=32, l=32),
        count=3,
        mass=-1,
        lifecycle=Lifecycle(delay=60, persist=False)
    )
    state = FluidState(
        id="waterflow-1",
        name="jasilynns-tears",
        layer="0",
        position=Position(x=70, y=0),
        source=Directions.DOWN.value,
        flow=2,
        length=0,
        dirty=True
    )
    return Asset(tax, props, state, FluidFrame(tile_w=32, tile_l=32), LifecycleAnimation())

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


@pytest.fixture
def mock_sprite_with_hitbox():
    """
    Sprite asset featuring a standard LPC offset collision hitbox.
    """
    tax = Taxonomy("sprite-jasilynn", "evil-empress-jasilynn", AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    hb = Hitbox(Position(21, 23), Dimensions(22, 21))
    props = SheetProperties(
        dimensions=Dimensions(w=64, l=64),
        mass=10,
        hitboxes=[hb]
    )
    state = SpriteState(
        id="sprite-jasilynn",
        name="evil-empress-jasilynn",
        layer="brick-house-compose-layer",
        position=Position(x=175, y=200),
        intention=Intentions.FIND,
        psyche=Psyche(motivation=Motivations.CONQUEST.value, persona="empress-jasilynn", dialogue="greeting"),
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
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())


@pytest.fixture
def mock_door_asset():
    """
    Door asset transitioning from layer '0' to layer 'brick-house-compose-layer'.
    """
    tax = Taxonomy("door-1", "wood-door", AssetCategories.OBJECTS.value, AssetInstances.DOORS.value)
    hb = Hitbox(Position(0, 0), Dimensions(32, 32))
    props = ObjectProperties(
        dimensions=Dimensions(w=32, l=32),
        hitboxes=[hb],
        mass=-1
    )
    state = DoorState(
        id="door-1",
        layer="0",
        outlayer="brick-house-compose-layer",
        position=Position(x=100, y=100),
        out=Position(x=20, y=20)
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