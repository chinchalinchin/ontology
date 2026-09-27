"""
# Ontology: tests.unit.conftest
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Actions,
    Directions
)
from app.models.properties import (
    # -------- FIELDS
    Action,
    Direction,
    RGBA,
    Outline,
    Cost,
    Lifecycle,
    # -------- MODELS
    ObjectProperties,
    SheetProperties,
    WidgetProperties,
    CursorProperties,
    TileProperties,
    CraftProperties,
    ObjectProperties,
    GeographyProperties,
    EffectProperties,
    FontProperties,
    # -------- INSTANCES
    CraftPropertyInstances,
    CursorPropertyInstances,
    SheetPropertyInstances,
    WidgetPropertyInstances,
    GeographyPropertyInstances,
    ObjectPropertyInstances,
    TilePropertyInstances,
    EffectPropertyInstances,
    # -------- SCHEMA
    PropertiesSchema,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Hitbox
)

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
    lpc_hitbox = Hitbox(Position(21, 23), Dimensions(22, 21))
    weapon_hitbox = Hitbox(Position(10, 15), Dimensions(20, 25))

    return SheetPropertyInstances(
        sprites = {
            "player": SheetProperties(
                dimensions = Dimensions(w=64, l=64),
                mass = 7,
                hitboxes = [ lpc_hitbox ]
            ),
            'jasilynn':  SheetProperties(
                dimensions =Dimensions(w=64, l=64),
                mass = 10,
                hitboxes = [ lpc_hitbox ]
            ),
            'sprite':  SheetProperties(
                dimensions = Dimensions(w=64, l=64),
                mass = 10,
                hitboxes = [lpc_hitbox]
            )
        },
        weapons = {
            'shortsword': SheetProperties(
                dimensions = Dimensions(64, 64),
                attackboxes = {
                    "slash-right-3": [ weapon_hitbox ] 
                },
                actions = {
                    Actions.SLASH.value: Action(
                        count = 6,
                        directions = {
                            Directions.UP.value: Direction(row=12),
                            Directions.LEFT.value: Direction(row=13),
                            Directions.DOWN.value: Direction(row=14),
                            Directions.RIGHT.value: Direction(row=15)
                        }
                    )
                }
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
        },
        gates = {
            'castle-gate': ObjectProperties(
                dimensions=Dimensions(w=32, l=32), 
                mass=0
            )
        }
    )


@pytest.fixture
def mock_cursor_properties() -> CursorPropertyInstances:
    return CursorPropertyInstances(
        projectiles = {
            'arrow-1': CursorProperties(dimensions=Dimensions(w=16, l=16))
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
        },
        passive = {
            "splash": EffectProperties(
                dimensions=Dimensions(w=16, l=16), 
                count=3, 
                mass=-1
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
                fluid="waterflow-01",
                thickness=8,
                mass=-1
            )
        }
    )


@pytest.fixture
def mock_properties(
    mock_cursor_properties,
    mock_geography_properties,
    mock_object_properties,
    mock_sheet_properties,
    mock_widget_properties,
    mock_craft_properties,
    mock_tile_properties
) -> PropertiesSchema:
    return PropertiesSchema(
        cursors = mock_cursor_properties,
        crafts = mock_craft_properties,
        geography = mock_geography_properties,
        objects = mock_object_properties,
        sheets = mock_sheet_properties,
        widgets = mock_widget_properties,
        tiles = mock_tile_properties
    )

