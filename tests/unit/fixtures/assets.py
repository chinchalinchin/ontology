"""
# Ontology: tests.unit.fixtures.assets

Mock Asset fixtures.
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
    IterableFrame,
    CardinalFrame,
    SingleFrame,
    SpriteFrame,
    OrientedFrame,
    SeasonalFrame,
    StageFrame
)
from app.assets.hitboxes import (
    StaticHitbox,
    DynamicHitbox,
    StageHitbox,
    AttackHitbox,
    NoHitbox
)
from app.assets.animations import (
    NoAnimation,
    BinaryAnimation,
    LifecycleAnimation,
    SpriteAnimation
)
from app.config.enums import ( 
    AssetCategories, 
    AssetInstances,
)

# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK ASSETS
# --------------------------------------------------------------------------

@pytest.fixture
def mock_tree_resource(
    mock_resource_properties,
    mock_tree_state
) -> Asset:
    return Asset(
        taxonomy=Taxonomy(
            id="deciduous",
            name="the-mighty-oak",
            category=AssetCategories.RESOURCES.value,
            instance=AssetInstances.TREES.value
        ),
        properties=mock_resource_properties.trees.get("deciduous"),
        state=mock_tree_state,
        frame=StageFrame(),
        animation=NoAnimation(),
        hitbox=StageHitbox()
    )


@pytest.fixture
def mock_crop_resource(
    mock_resource_properties,
    mock_crop_state
) -> Asset:
    return Asset(
        taxonomy=Taxonomy(
            id="lettuce",
            name="some-lettuce",
            category=AssetCategories.RESOURCES.value,
            instance=AssetInstances.CROPS.value
        ),
        properties=mock_resource_properties.crops.get("lettuce"),
        state=mock_crop_state,
        frame=StageFrame(),
        animation=NoAnimation(),
        hitbox=StageHitbox()
    )


@pytest.fixture
def mock_back_tile(
    mock_tile_properties,
    mock_multiplier_state
) -> Asset:
    return Asset(
        taxonomy = Taxonomy(
            id = "temperate",
            name = "the-steppe",
            category = AssetCategories.TILES.value, 
            instance = AssetInstances.BACK.value
        ), 
        properties = mock_tile_properties.back.get('temperate'), 
        state = mock_multiplier_state, 
        frame = SeasonalFrame(), 
        animation = NoAnimation(),
        hitbox=NoHitbox()
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
        frame = CardinalFrame(tile_w=32, tile_l=32),
        animation = NoAnimation(),
        hitbox=DynamicHitbox()
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
        frame = SpriteFrame(), 
        animation = SpriteAnimation(),
        hitbox = StaticHitbox()
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
        frame = SpriteFrame(), 
        animation = SpriteAnimation(),
        hitbox = StaticHitbox()
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
        frame = SpriteFrame(), 
        animation = SpriteAnimation(),
        hitbox = StaticHitbox()
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
        frame = SingleFrame(),
        animation = NoAnimation(),
        hitbox = StaticHitbox()
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
        frame = SingleFrame(), 
        animation = NoAnimation(),
        hitbox = StaticHitbox()
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
        frame = SingleFrame(), 
        animation = NoAnimation(),
        hitbox = StaticHitbox()
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
        frame = SingleFrame(), 
        animation = NoAnimation(),
        hitbox = StaticHitbox()
    )


@pytest.fixture
def mock_bridge(
    mock_craft_properties,
    mock_bridge_state
) -> Asset:
    return Asset(
        taxonomy = Taxonomy(
            id = "wood-bridge",
            name = "bridge-main-0",
            category = AssetCategories.CRAFTS.value,
            instance = AssetInstances.BRIDGES.value
        ),
        properties = mock_craft_properties.bridges.get('wood-bridge'),
        state = mock_bridge_state,
        frame = OrientedFrame(),
        animation = NoAnimation(),
        hitbox = StaticHitbox()
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
        frame = SingleFrame(), 
        animation = NoAnimation(),
        hitbox = StaticHitbox()
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
        frame = SingleFrame(), 
        animation = NoAnimation(),
        hitbox = StaticHitbox()
    )


@pytest.fixture
def mock_crate_alt(
    mock_object_properties,
    mock_positional_state_alt2
) -> Asset:
    """
    Secondary crate asset fixture positioned upstream of fluid emitters.
    """
    return Asset(
        taxonomy=Taxonomy(
            id="wood-crate",
            name="box-upstream",
            category=AssetCategories.OBJECTS.value,
            instance=AssetInstances.CRATES.value
        ),
        properties=mock_object_properties.crates.get("wood-crate"),
        state=mock_positional_state_alt2,
        frame=SingleFrame(),
        animation=NoAnimation(),
        hitbox=StaticHitbox() 
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
        frame = IterableFrame(),
        animation = BinaryAnimation(),
        hitbox = StaticHitbox()
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
        animation = LifecycleAnimation(),
        hitbox = DynamicHitbox()
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
        animation = LifecycleAnimation(),
        hitbox = DynamicHitbox()
    )


@pytest.fixture
def mock_fluid_alt2(
    mock_effect_properties,
    mock_fluid_state_alt2
) -> Asset:
    """
    Secondary parallel fluid emitter fixture for boundary occlusion tests.
    """
    return Asset(
        taxonomy=Taxonomy(
            id="waterflow-01",
            name="fluid-adjacent",
            category=AssetCategories.EFFECTS.value,
            instance=AssetInstances.FLUIDS.value
        ),
        properties=mock_effect_properties.fluids.get("waterflow-01"),
        state=mock_fluid_state_alt2,
        frame=FluidFrame(tile_w=32, tile_l=32),
        animation=LifecycleAnimation(),
        hitbox = DynamicHitbox()
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
        frame = SingleFrame(), 
        animation = NoAnimation(),
        hitbox = StaticHitbox()
    )


@pytest.fixture
def mock_chest(
    mock_object_properties,
    mock_container_state
) -> Asset:
    return Asset(
        taxonomy=Taxonomy(
            id="wood-chest",
            name="chest-1",
            category=AssetCategories.OBJECTS.value,
            instance=AssetInstances.CHESTS.value
        ),
        properties=mock_object_properties.chests.get('wood-chest'),
        state=mock_container_state,
        frame=IterableFrame(),
        animation=BinaryAnimation(),
        hitbox = StaticHitbox()
    )


@pytest.fixture
def mock_plate(
    mock_object_properties,
    mock_switch_state_alt
) -> Asset:
    return Asset(
        taxonomy=Taxonomy(
            id="pressure-plate",
            name="plate-1",
            category=AssetCategories.OBJECTS.value,
            instance=AssetInstances.PLATES.value
        ),
        properties=mock_object_properties.plates.get('pressure-plate'),
        state=mock_switch_state_alt,
        frame=IterableFrame(),
        animation=BinaryAnimation(),
        hitbox = StaticHitbox()
    )


@pytest.fixture
def mock_reactable(
    mock_effect_properties,
    mock_reactable_state
) -> Asset:
    return Asset(
        taxonomy=Taxonomy(
            id="reactable-1",
            name="reactable-1",
            category=AssetCategories.EFFECTS.value,
            instance=AssetInstances.REACTABLES.value
        ),
        properties=mock_effect_properties.reactables.get('reactable-1'),
        state=mock_reactable_state,
        frame=IterableFrame(),
        animation=LifecycleAnimation(),
        hitbox = StaticHitbox()
    )


@pytest.fixture
def mock_assets(
    mock_back_tile,
    mock_player,
    mock_sprite,
    mock_sprite_alt,
    mock_fluid,
    mock_fluid_alt,
    mock_reactable,
    mock_door,
    mock_chest,
    mock_plate,
    mock_crate,
    mock_gate,
    mock_strut,
    mock_strut_alt,
    mock_strut_alt2,
    mock_raft,
    mock_bridge
):
    return [
        mock_back_tile,
        mock_sprite, 
        mock_sprite_alt,
        mock_player,
        mock_fluid,
        mock_fluid_alt,
        mock_reactable,
        mock_door,
        mock_chest,
        mock_plate,
        mock_gate,
        mock_crate,
        mock_strut,
        mock_strut_alt,
        mock_strut_alt2,
        mock_raft,
        mock_bridge
    ]
