"""
# Ontology: tests.unit.conftest
"""
# External Libraries
import pytest

# Application Libraries
from app.assets.base import (
    Asset, 
    Taxonomy
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
)

# Test Libraries
from tests.unit.conftest import (
    DummyAnimation,
    DummyFrame
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
def mock_sprite_alt(
    mock_sheet_properties,
    mock_sprite_state_alt
) -> Asset:
    """
    Sprite asset featuring a standard LPC offset collision hitbox.
    """
    return Asset(
        taxonomy = Taxonomy(
            id = "sprite", 
            name = "npc", 
            category = AssetCategories.SHEETS.value, 
            instance = AssetInstances.SPRITES.value
        ), 
        properties = mock_sheet_properties.sprites.get('sprite'), 
        state = mock_sprite_state_alt, 
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
def mock_projectile(
    mock_cursor_properties,
    mock_motor_state
):
    return Asset(
        taxonomy = Taxonomy(
            id = "arrow-1",
            name = "feathered-arrow",
            category = AssetCategories.CURSORS.value,
            instance = AssetInstances.PROJECTILES.value
        ),
        properties = mock_cursor_properties.projectiles.get('arrow-1'),
        state = mock_motor_state, 
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
def mock_gate(
    mock_object_properties,
    mock_switch_state
) -> Asset:
    return Asset(
        taxonomy = Taxonomy(
            id  = 'castle-gate',
            name = 'cool-gate',
            category = AssetCategories.OBJECTS.value,
            instance = AssetInstances.GATES.value
        ),
        properties = mock_object_properties.gates.get('castle-gate'),
        state = mock_switch_state, 
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
def mock_fluid_alt(
    mock_effect_properties,
    mock_fluid_state_alt
) -> Asset:
    """
    Standard directional fluid emitter asset configured with continuous lifecycle.
    """
    return Asset(
        taxonomy = Taxonomy(
            id = "waterflow-01",
            name = "jasilynns-tears-left",
            category = AssetCategories.EFFECTS.value,
            instance = AssetInstances.FLUIDS.value
        ), 
        properties = mock_effect_properties.fluids.get('waterflow-01'), 
        state = mock_fluid_state_alt, 
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
    mock_sprite_alt,
    mock_back_tile,
    mock_fluid,
    mock_fluid_alt,
    mock_door,
    mock_crate,
    mock_gate,
    mock_strut,
    mock_strut_alt,
    mock_strut_alt2,
    mock_raft
):
    return [
        mock_sprite, 
        mock_sprite_alt,
        mock_back_tile,
        mock_player,
        mock_fluid,
        mock_fluid_alt,
        mock_door,
        mock_gate,
        mock_crate,
        mock_strut,
        mock_strut_alt,
        mock_strut_alt2,
        mock_raft
    ]

