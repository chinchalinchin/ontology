"""
@domain.test
@test.unit
@app.asset
@asset.frame

# Ontology: Test - tests.unit.app.assets.test_frames

Unit tests for Asset Frame implementations.
"""
# External Libraries
import pytest

# Application Libraries
from app.assets.frames import (
    CardinalFrame,
    IndexFrame,
    NoFrame,
)
from app.models.state import (
    AttachmentState,
    CalendarState,
    Equipment,
    IconState,
    Pool,
    Psyche,
    ShorelineState,
)
from app.static.semantics import (
    Actions,
    AnnualStages,
    AssetCategories,
    AssetInstances,
    ChannelTypes,
    Cycles,
    Directions,
    ExpressionsPalette,
    PerennialStages,
    Seasons,
)
from app.static.settings import SEPARATOR

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position,
)

pytestmark = [
    pytest.mark.app_asset,
    pytest.mark.asset_frame,
]


@pytest.mark.app_core
def test_no_frame(mock_asset):
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    frame = NoFrame()
    assert frame.keys(crate.id, crate.state) == [(crate.id, 0, 0)]
    assert frame.index(crate.id, crate.properties) == {crate.id: (0, 0, 0, 0)}


@pytest.mark.app_core
def test_single_frame(mock_asset):
    canopy = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.CANOPY.value,
    )
    assert canopy.frame.keys(canopy.id, canopy.state) == [(canopy.id, 0, 0)]
    assert canopy.frame.index(canopy.id, canopy.properties) == {
        canopy.id: (0, 0, canopy.dimensions.w, canopy.dimensions.l)
    }


@pytest.mark.category_effects
def test_iterable_frame(mock_asset):
    effect = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    effect.state.animation.frame = 1

    expected_key = f"{effect.id}{SEPARATOR}1"
    assert effect.frame.keys(effect.id, effect.state) == [(expected_key, 0, 0)]

    w, l = effect.dimensions.w, effect.dimensions.l
    index = effect.frame.index(effect.id, effect.properties)
    assert index == {
        f"{effect.id}{SEPARATOR}{i}": (i * w, 0, w, l)
        for i in range(effect.properties.count)
    }


@pytest.mark.category_sheets
def test_state_frame(mock_asset):
    pixie = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PIXIES.value,
    )
    pixie.state.animation.action = Actions.WALK.value
    pixie.state.animation.direction = Directions.DOWN.value
    pixie.state.animation.frame = 2

    expected_key = f"{pixie.id}{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}2"
    assert pixie.frame.keys(pixie.id, pixie.state) == [(expected_key, 0, 0)]

    crops = pixie.frame.index(pixie.id, pixie.properties)
    row = (
        pixie.properties.actions[Actions.WALK.value]
        .directions[Directions.DOWN.value]
        .row
    )
    w, l = pixie.dimensions.w, pixie.dimensions.l
    assert crops[f"{pixie.id}{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}0"] == (
        0,
        row * l,
        w,
        l,
    )
    assert crops[f"{pixie.id}{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}1"] == (
        w,
        row * l,
        w,
        l,
    )


@pytest.mark.category_sheets
def test_sprite_frame(mock_asset):
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite.state.animation.action = Actions.SLASH.value
    sprite.state.animation.direction = Directions.LEFT.value
    sprite.state.animation.frame = 3
    sprite.state.inventory.equipment = Equipment(
        armor="leather_armor",
        utility="lantern",
        tool="pickaxe",
        weapon="sword",
        shield="buckler",
    )
    sprite.state.psyche.expression = AttachmentState(
        id="bubble",
        layer="0",
        icon="loquacity",
        offset=Position(x=10, y=-10),
        ttl=100,
    )

    keys = sprite.frame.keys(sprite.id, sprite.state)

    assert keys[0] == (f"{sprite.id}{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[1] == (f"leather_armor{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[2] == (f"lantern{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[3] == (f"pickaxe{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[4] == (f"sword{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[5] == (f"buckler{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)

    expr_key = f"{ExpressionsPalette.BUBBLES.value}{SEPARATOR}loquacity"
    assert keys[6] == (expr_key, 10, -10)


@pytest.mark.category_widgets
@pytest.mark.workflow_menus
def test_index_frame_indexing(mock_properties):
    frame = IndexFrame()
    props = mock_properties(
        AssetCategories.CURSORS.value,
        AssetInstances.EXPRESSIONS.value,
        "bubbles",
    )
    w, l = props.dimensions.w, props.dimensions.l
    crops = frame.index("bubbles", props)

    for i, frame_name in enumerate(props.frames):
        assert crops[f"bubbles{SEPARATOR}{frame_name}"] == (i * w, 0, w, l)


@pytest.mark.category_widgets
@pytest.mark.workflow_menus
def test_index_frame_suppresses_vacant_slot():
    frame = IndexFrame()

    occupied_state = IconState(id="weapons", icon_function=lambda: "shortsword")
    assert frame.keys("weapons", occupied_state) == [(f"weapons{SEPARATOR}shortsword", 0, 0)]

    empty_state = IconState(id="weapons", icon_function=lambda: "")
    assert frame.keys("weapons", empty_state) == []

    none_state = IconState(id="weapons", icon_function=lambda: None)
    assert frame.keys("weapons", none_state) == []


@pytest.mark.category_sheets
@pytest.mark.workflow_intentions
def test_sprite_frame_player_suppresses_expression(mock_asset):
    """
    Ensure player entities suppress expression attachments in SpriteFrame.keys.
    """
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )
    player.state.animation.action = Actions.WALK.value
    player.state.animation.direction = Directions.DOWN.value
    player.state.animation.frame = 0
    player.state.inventory.equipment = Equipment()
    player.state.psyche = Psyche(
        expression=AttachmentState(
            id="bubble",
            layer="0",
            icon="loquacity",
            offset=Position(x=10, y=-10),
            ttl=100,
        )
    )

    keys = player.frame.keys(player.id, player.state)
    assert keys == [(f"{player.id}{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}0", 0, 0)]


@pytest.mark.category_sheets
@pytest.mark.workflow_intentions
def test_sprite_frame_no_equipment(mock_asset):
    """
    Ensure SpriteFrame handles sprites with empty or None equipment inventories cleanly.
    """
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite.state.animation.action = Actions.WALK.value
    sprite.state.animation.direction = Directions.DOWN.value
    sprite.state.animation.frame = 0
    sprite.state.inventory.equipment = None
    sprite.state.psyche.expression = None

    keys = sprite.frame.keys(sprite.id, sprite.state)
    assert keys == [(f"{sprite.id}{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}0", 0, 0)]


@pytest.mark.category_effects
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_fluid_frame_indexing(mock_asset):
    """
    Verify FluidFrame generates full tile keys and directional forward/reverse
    fractional slices across dimensions and animation frames.
    """
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    w, l = fluid.dimensions.w, fluid.dimensions.l
    crops = fluid.frame.index(fluid.id, fluid.properties)

    # 1. Base full frames
    assert crops[f"{fluid.id}{SEPARATOR}0"] == (0, 0, w, l)
    assert crops[f"{fluid.id}{SEPARATOR}1"] == (w, 0, w, l)

    # 2. Forward vertical slicing: down
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}down{SEPARATOR}10"] == (0, 0, w, 10)
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}down{SEPARATOR}slice{SEPARATOR}10"] == (0, 0, w, 10)

    # 3. Reverse vertical slicing: up (anchored at distal edge l - 10)
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}up{SEPARATOR}10"] == (0, l - 10, w, 10)
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}up{SEPARATOR}slice{SEPARATOR}10"] == (0, l - 10, w, 10)

    # 4. Forward horizontal slicing: right
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}right{SEPARATOR}10"] == (0, 0, 10, l)
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}right{SEPARATOR}slice{SEPARATOR}10"] == (0, 0, 10, l)

    # 5. Reverse horizontal slicing: left (anchored at distal edge w - 10)
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}left{SEPARATOR}10"] == (w - 10, 0, 10, l)
    assert crops[f"{fluid.id}{SEPARATOR}0{SEPARATOR}left{SEPARATOR}slice{SEPARATOR}10"] == (w - 10, 0, 10, l)


@pytest.mark.category_effects
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_fluid_frame_keys_downward_stream(mock_asset):
    """
    Verify downward stream emits full tile keys plus fractional terminal slice.
    """
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    fluid.state.animation.frame = 0
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 48
    fluid.state.pool = None
    fluid.state.branches = []
    fluid.state._keys.clear()

    keys = fluid.frame.keys(fluid.id, fluid.state)

    assert len(keys) == 2
    assert keys[0] == (f"{fluid.id}{SEPARATOR}0", 0, 0)
    assert keys[1] == (f"{fluid.id}{SEPARATOR}0{SEPARATOR}down{SEPARATOR}16", 0, 32)


@pytest.mark.category_effects
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_fluid_frame_keys_upward_stream(mock_asset):
    """
    Verify upward stream emits negative Y-coordinate offsets and reverse slice keys.
    """
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    fluid.state.animation.frame = 0
    fluid.state.source = Directions.UP.value
    fluid.state.length = 48
    fluid.state.pool = None
    fluid.state.branches = []
    fluid.state._keys.clear()

    keys = fluid.frame.keys(fluid.id, fluid.state)

    assert len(keys) == 2
    assert keys[0] == (f"{fluid.id}{SEPARATOR}0", 0, -32)
    assert keys[1] == (f"{fluid.id}{SEPARATOR}0{SEPARATOR}up{SEPARATOR}16", 0, -48)


@pytest.mark.category_effects
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_fluid_frame_keys_lateral_streams(mock_asset):
    """
    Verify lateral streams emit X-axis offsets for right and left flow vectors.
    """
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    fluid.state.animation.frame = 0
    fluid.state.length = 48
    fluid.state.pool = None
    fluid.state.branches = []

    # Right flow
    fluid.state.source = Directions.RIGHT.value
    fluid.state._keys.clear()
    keys_right = fluid.frame.keys(fluid.id, fluid.state)
    assert keys_right[0] == (f"{fluid.id}{SEPARATOR}0", 0, 0)
    assert keys_right[1] == (f"{fluid.id}{SEPARATOR}0{SEPARATOR}right{SEPARATOR}16", 32, 0)

    # Left flow
    fluid.state.source = Directions.LEFT.value
    fluid.state._keys.clear()
    keys_left = fluid.frame.keys(fluid.id, fluid.state)
    assert keys_left[0] == (f"{fluid.id}{SEPARATOR}0", -32, 0)
    assert keys_left[1] == (f"{fluid.id}{SEPARATOR}0{SEPARATOR}left{SEPARATOR}16", -48, 0)


@pytest.mark.category_effects
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_fluid_frame_keys_with_annular_pool(mock_asset):
    """
    Verify annular pool hitboxes translate to grid-spaced frame key offsets.
    """
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    stream_hb = Hitbox(Position(0, 0), Dimensions(32, 64))
    flank_hb = Hitbox(Position(-32, 64), Dimensions(96, 32))

    fluid.state.animation.frame = 0
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 64
    fluid.state.pool = Pool(x=38, y=64, w=96, l=64)
    fluid.state.hitboxes = [stream_hb, flank_hb]
    fluid.state.branches = []
    fluid.state._keys.clear()

    keys = fluid.frame.keys(fluid.id, fluid.state)

    # Stream corridor (2 full 32px tiles)
    assert (f"{fluid.id}{SEPARATOR}0", 0, 0) in keys
    assert (f"{fluid.id}{SEPARATOR}0", 0, 32) in keys

    # Flank corridor (3 horizontal 32px steps along 96px width)
    assert (f"{fluid.id}{SEPARATOR}0", -32, 64) in keys
    assert (f"{fluid.id}{SEPARATOR}0", 0, 64) in keys
    assert (f"{fluid.id}{SEPARATOR}0", 32, 64) in keys


@pytest.mark.category_sheets
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_sprite_frame_channels_dry(mock_asset):
    """
    Verify SpriteFrame.channels returns an empty list when sprite is not submerged.
    """
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )
    player.state.mutators.triggers.submerged = False

    directives = player.frame.channels(player.id, player.state, player.properties)
    assert directives == []


@pytest.mark.category_sheets
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_sprite_frame_channels_submerged(mock_asset):
    """
    Verify SpriteFrame.channels emits SUBMERGE directive with half-length split
    and aquatic modulation payload when sprite is submerged.
    """
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )
    player.state.mutators.triggers.submerged = True

    directives = player.frame.channels(player.id, player.state, player.properties)
    assert directives == [
        (
            ChannelTypes.SUBMERGE.value,
            (player.dimensions.l // 2, 40, 110, 180, 170),
        )
    ]


@pytest.mark.category_geography
@pytest.mark.workflow_geology
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_shoreline_frame_indexing(mock_properties):
    """
    Verify CardinalFrame indexes 4 cardinal rows across 4 calendar seasons
    and forward fractional remainder slices.
    """
    frame = CardinalFrame()
    props = mock_properties(
        AssetCategories.GEOGRAPHY.value,
        AssetInstances.SHORELINES.value,
    )
    crops = frame.index("grassy-shore", props)

    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}up"] == (0, 0, 32, 32)
    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}left"] == (0, 32, 32, 32)
    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}down"] == (0, 64, 32, 32)
    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}right"] == (0, 96, 32, 32)

    assert crops[f"grassy-shore{SEPARATOR}summer{SEPARATOR}up"] == (32, 0, 32, 32)
    assert crops[f"grassy-shore{SEPARATOR}autumn{SEPARATOR}up"] == (64, 0, 32, 32)
    assert crops[f"grassy-shore{SEPARATOR}winter{SEPARATOR}up"] == (96, 0, 32, 32)

    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}up{SEPARATOR}16"] == (0, 0, 16, 32)
    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}down{SEPARATOR}16"] == (0, 64, 16, 32)
    assert crops[f"grassy-shore{SEPARATOR}summer{SEPARATOR}up{SEPARATOR}16"] == (32, 0, 16, 32)

    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}left{SEPARATOR}16"] == (0, 32, 32, 16)
    assert crops[f"grassy-shore{SEPARATOR}spring{SEPARATOR}right{SEPARATOR}16"] == (0, 96, 32, 16)
    assert crops[f"grassy-shore{SEPARATOR}winter{SEPARATOR}right{SEPARATOR}16"] == (96, 96, 32, 16)


@pytest.mark.category_geography
@pytest.mark.workflow_geology
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_shoreline_frame_keys_horizontal_full_and_slice():
    """
    Verify horizontal banks (UP/DOWN) emit full-tile keys along width and a terminal remainder.
    """
    frame = CardinalFrame(tile_w=32, tile_l=32)
    state = ShorelineState(
        id="grassy-shore",
        orientation=Directions.UP.value,
        season=Seasons.SPRING.value,
        length=80,
    )
    keys = frame.keys("grassy-shore", state)

    assert len(keys) == 3
    assert keys[0] == (f"grassy-shore{SEPARATOR}spring{SEPARATOR}up", 0, 0)
    assert keys[1] == (f"grassy-shore{SEPARATOR}spring{SEPARATOR}up", 32, 0)
    assert keys[2] == (f"grassy-shore{SEPARATOR}spring{SEPARATOR}up{SEPARATOR}16", 64, 0)


@pytest.mark.category_geography
@pytest.mark.workflow_geology
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_shoreline_frame_keys_vertical_full_and_slice():
    """
    Verify vertical banks (LEFT/RIGHT) emit full-tile keys along length and a terminal remainder.
    """
    frame = CardinalFrame(tile_w=32, tile_l=32)
    state = ShorelineState(
        id="grassy-shore",
        orientation=Directions.LEFT.value,
        season=Seasons.SPRING.value,
        length=80,
    )
    keys = frame.keys("grassy-shore", state)

    assert len(keys) == 3
    assert keys[0] == (f"grassy-shore{SEPARATOR}spring{SEPARATOR}left", 0, 0)
    assert keys[1] == (f"grassy-shore{SEPARATOR}spring{SEPARATOR}left", 0, 32)
    assert keys[2] == (f"grassy-shore{SEPARATOR}spring{SEPARATOR}left{SEPARATOR}16", 0, 64)


@pytest.mark.category_geography
@pytest.mark.workflow_geology
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_shoreline_frame_keys_zero_length():
    frame = CardinalFrame()
    state = ShorelineState(id="grassy-shore", length=0)
    assert frame.keys("grassy-shore", state) == []


@pytest.mark.category_geography
@pytest.mark.workflow_geology
@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_shoreline_frame_channels(mock_properties):
    """
    Verify CardinalFrame inherits universal Frame.channels behavior.
    """
    frame = CardinalFrame()
    state = ShorelineState(id="grassy-shore")
    props = mock_properties(
        AssetCategories.GEOGRAPHY.value,
        AssetInstances.SHORELINES.value,
    )

    assert frame.channels("grassy-shore", state, props) == []

    state.mutators.triggers.submerged = True
    assert frame.channels("grassy-shore", state, props) == [
        (ChannelTypes.SUBMERGE.value, (props.dimensions.l // 2, 40, 110, 180, 170))
    ]


@pytest.mark.category_tiles
@pytest.mark.workflow_seasons
def test_seasonal_frame_indexing(mock_asset):
    """Verify SeasonalFrame generates a complete 36-cell atlas index."""
    tile = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.ENVIRON.value,
        id="temperate",
    )
    crops = tile.frame.index(tile.id, tile.properties)

    assert len(crops) == 36
    assert crops[f"temperate{SEPARATOR}spring{SEPARATOR}onset{SEPARATOR}0"] == (0, 0, 32, 32)
    assert crops[f"temperate{SEPARATOR}spring{SEPARATOR}decline{SEPARATOR}2"] == (256, 0, 32, 32)
    assert crops[f"temperate{SEPARATOR}winter{SEPARATOR}decline{SEPARATOR}2"] == (256, 96, 32, 32)


@pytest.mark.category_tiles
@pytest.mark.workflow_seasons
def test_seasonal_frame_eras(mock_asset):
    """
    Verify SeasonalFrame.eras maps calendar state to the canonical frame key.
    """
    tile = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.ENVIRON.value,
        id="temperate",
    )
    calendar = CalendarState(
        season=Seasons.AUTUMN.value,
        cycle=Cycles.PEAK.value,
        period=2,
    )

    keys = tile.frame.eras(tile.id, calendar)
    assert keys == [(f"temperate{SEPARATOR}autumn{SEPARATOR}peak{SEPARATOR}2", 0, 0)]


@pytest.mark.category_tiles
@pytest.mark.workflow_seasons
def test_seasonal_frame_keys_fallback(mock_asset):
    """
    Verify SeasonalFrame.keys returns the default spring-onset-0 frame key.
    """
    tile = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.ENVIRON.value,
        id="temperate",
    )
    keys = tile.frame.keys(tile.id, tile.state)
    assert keys == [(f"temperate{SEPARATOR}spring{SEPARATOR}onset{SEPARATOR}0", 0, 0)]


@pytest.mark.category_resources
@pytest.mark.workflow_seasons
def test_stage_frame_indexing_annual(mock_asset):
    """Verify StageFrame dynamically indexes horizontal cells for annual crops."""
    crop = mock_asset(
        AssetCategories.RESOURCES.value,
        AssetInstances.CROPS.value,
        id="lettuce",
    )
    crops = crop.frame.index(crop.id, crop.properties)

    assert len(crops) == len(AnnualStages)
    for i, stage in enumerate(AnnualStages):
        key = f"lettuce{SEPARATOR}{stage.value}"
        assert crops[key] == (i * 32, 0, 32, 22)


@pytest.mark.category_resources
@pytest.mark.workflow_seasons
def test_stage_frame_indexing_perennial(mock_asset):
    """Verify StageFrame dynamically indexes horizontal cells for perennial trees."""
    tree = mock_asset(
        AssetCategories.RESOURCES.value,
        AssetInstances.TREES.value,
        id="deciduous",
    )
    crops = tree.frame.index(tree.id, tree.properties)

    assert len(crops) == len(PerennialStages)
    for i, stage in enumerate(PerennialStages):
        key = f"deciduous{SEPARATOR}{stage.value}"
        assert crops[key] == (i * 94, 0, 94, 137)


@pytest.mark.category_resources
@pytest.mark.workflow_seasons
def test_stage_frame_keys(mock_asset):
    """
    Verify StageFrame resolves frame keys reflexively from state.stage.
    """
    tree = mock_asset(
        AssetCategories.RESOURCES.value,
        AssetInstances.TREES.value,
        id="deciduous",
    )
    tree.state.stage = PerennialStages.ADULT.value
    keys = tree.frame.keys(tree.id, tree.state)

    assert keys == [(f"deciduous{SEPARATOR}{PerennialStages.ADULT.value}", 0, 0)]