"""
@domain.test
@test.unit
@app.asset
@asset.frame
@workflow.rendering

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
from app.assets.frames.core import (
    DirectedFrame,
    OrientedFrame,
    SingleFrame,
)
from app.assets.frames.crafts import MaterialFrame
from app.assets.frames.objects import (
    BinaryFrame,
    ObjectFrame,
)
from app.assets.frames.widgets import (
    MeterFrame,
    TraversalFrame,
)
from app.models.state import (
    AttachmentState,
    CalendarState,
    ContainerState,
    CraftState,
    DoorState,
    Equipment,
    IconState,
    Pool,
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
    Gauges,
    LayerProjections,
    Orientations,
    PerennialStages,
    Seasons,
    Statuses,
    Switches,
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
    pytest.mark.workflow_rendering,
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
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    frame = SingleFrame()
    w, l = crate.dimensions.w, crate.dimensions.l
    assert frame.keys(crate.id, crate.state) == [(crate.id, 0, 0)]
    assert frame.index(crate.id, crate.properties) == {crate.id: (0, 0, w, l)}


@pytest.mark.app_core
def test_oriented_frame(mock_properties):
    frame = OrientedFrame()
    props = mock_properties(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    w, l = props.dimensions.w, props.dimensions.l
    crops = frame.index("beam", props)

    for i, orientation in enumerate(Orientations):
        assert crops[f"beam{SEPARATOR}{orientation.value}"] == (i * w, 0, w, l)

    state = ShorelineState(id="beam", orientation=Orientations.HORIZONTAL.value)
    assert frame.keys("beam", state) == [
        (f"beam{SEPARATOR}{Orientations.HORIZONTAL.value}", 0, 0)
    ]


@pytest.mark.app_core
def test_directed_frame(mock_properties):
    frame = DirectedFrame()
    props = mock_properties(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    w, l = props.dimensions.w, props.dimensions.l
    crops = frame.index("arrow", props)

    for i, direction in enumerate(Directions):
        assert crops[f"arrow{SEPARATOR}{direction.value}"] == (i * w, 0, w, l)


@pytest.mark.category_objects
def test_object_frame(mock_asset):
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    assert crate.frame.keys(crate.id, crate.state) == [
        (f"{crate.id}-{crate.state.material}", 0, 0)
    ]
    assert (
        0, 0, crate.dimensions.w, crate.dimensions.l
    ) in crate.frame.index(crate.id, crate.properties).values()


@pytest.mark.category_objects
def test_object_frame_door_out_projection_channels(mock_properties):
    frame = ObjectFrame()
    props = mock_properties(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    w, l = props.dimensions.w, props.dimensions.l

    in_state = DoorState(
        id="door",
        outlayer="0",
        out=Position(0, 0),
        projection=LayerProjections.IN.value,
    )
    assert frame.channels("door", in_state, props) == []

    out_state = DoorState(
        id="door",
        outlayer="0",
        out=Position(0, 0),
        projection=LayerProjections.OUT.value,
    )
    assert frame.channels("door", out_state, props) == [
        (ChannelTypes.TINT.value, (0, 0, w, l, 0, 0, 0, 110))
    ]


@pytest.mark.category_objects
def test_binary_frame(mock_properties, mock_material_index):
    frame = BinaryFrame()
    props = mock_properties(
        AssetCategories.OBJECTS.value,
        AssetInstances.CHESTS.value,
    )
    w, l = props.dimensions.w, props.dimensions.l
    materials = mock_material_index.materials(props.material.genus)
    crops = frame.index("chest", props)

    for r_idx in range(props.count):
        for c_idx, mat in enumerate(materials):
            key = f"chest{SEPARATOR}{mat}{SEPARATOR}{r_idx}"
            assert crops[key] == (c_idx * w, r_idx * l, w, l)

    mat = materials[0]
    closed_state = ContainerState(id="chest", material=mat, switch=False, content=[])
    open_state = ContainerState(id="chest", material=mat, switch=True, content=[])

    assert frame.keys("chest", closed_state) == [
        (f"chest{SEPARATOR}{mat}{SEPARATOR}{Switches.OFF.value}", 0, 0)
    ]
    assert frame.keys("chest", open_state) == [
        (f"chest{SEPARATOR}{mat}{SEPARATOR}{Switches.ON.value}", 0, 0)
    ]


@pytest.mark.category_crafts
def test_material_frame(mock_properties, mock_material_index):
    frame = MaterialFrame()
    props = mock_properties(
        AssetCategories.CRAFTS.value,
        AssetInstances.STRUTS.value,
    )
    w, l = props.dimensions.w, props.dimensions.l
    rows = mock_material_index.blueprints(props.blueprints)
    cols = mock_material_index.materials(props.material.genus)
    crops = frame.index("strut", props)

    for r_idx, bp in enumerate(rows):
        for c_idx, mat in enumerate(cols):
            assert crops[f"strut{SEPARATOR}{bp}{SEPARATOR}{mat}"] == (
                c_idx * w,
                r_idx * l,
                w,
                l,
            )

    state = CraftState(id="strut", blueprint=rows[0], material=cols[0])
    assert frame.keys("strut", state) == [
        (f"strut{SEPARATOR}{rows[0]}{SEPARATOR}{cols[0]}", 0, 0)
    ]


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
def test_index_frame_suppresses_vacant_slot():
    frame = IndexFrame()

    occupied_state = IconState(id="weapons", icon_function=lambda: "shortsword")
    assert frame.keys("weapons", occupied_state) == [(f"weapons{SEPARATOR}shortsword", 0, 0)]

    empty_state = IconState(id="weapons", icon_function=lambda: "")
    assert frame.keys("weapons", empty_state) == []

    none_state = IconState(id="weapons", icon_function=lambda: None)
    assert frame.keys("weapons", none_state) == []


@pytest.mark.category_widgets
def test_traversal_frame_indexing_and_keys(mock_properties, mock_state):
    frame = TraversalFrame()
    props = mock_properties(
        AssetCategories.WIDGETS.value,
        "buttons",
    )
    w, l = props.dimensions.w, props.dimensions.l
    crops = frame.index("ui_btn", props)

    assert crops[f"ui_btn{SEPARATOR}{Statuses.IDLE.value}"] == (0, 0, w, l)
    assert crops[f"ui_btn{SEPARATOR}{Statuses.ACTIVE.value}"] == (w, 0, w, l)
    assert crops[f"ui_btn{SEPARATOR}{Statuses.SELECTED.value}"] == (2 * w, 0, w, l)
    assert crops[f"ui_btn{SEPARATOR}{Statuses.DISABLED.value}"] == (3 * w, 0, w, l)

    state = mock_state(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    state.animation.action = Statuses.ACTIVE.value
    assert frame.keys("ui_btn", state) == [
        (f"ui_btn{SEPARATOR}{Statuses.ACTIVE.value}", 0, 0)
    ]


@pytest.mark.category_widgets
def test_meter_frame_indexing_and_keys(mock_properties, mock_state):
    frame = MeterFrame()
    props = mock_properties(
        AssetCategories.WIDGETS.value,
        "meters",
    )
    w, l = props.dimensions.w, props.dimensions.l
    crops = frame.index("health_bar", props)

    assert crops[f"health_bar{SEPARATOR}{Gauges.EMPTY.value}"] == (0, 0, w, l)
    assert crops[f"health_bar{SEPARATOR}50"] == (w, 0, int(w * 0.5), l)
    assert crops[f"health_bar{SEPARATOR}100"] == (w, 0, w, l)

    state = mock_state(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    state.animation.frame = 50
    assert frame.keys("health_bar", state) == [
        (f"health_bar{SEPARATOR}{Gauges.EMPTY.value}", 0, 0),
        (f"health_bar{SEPARATOR}50", 0, 0),
    ]


@pytest.mark.category_sheets
@pytest.mark.modality_intention
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
    fluid.frame.index(fluid.id, fluid.properties)
    w = fluid.dimensions.w
    rem = 16

    fluid.state.animation.frame = 0
    fluid.state.length = w + rem
    fluid.state.pool = None
    fluid.state.branches = []

    # Right flow
    fluid.state.source = Directions.RIGHT.value
    fluid.state._keys.clear()
    keys_right = fluid.frame.keys(fluid.id, fluid.state)
    assert keys_right[0] == (f"{fluid.id}{SEPARATOR}0", 0, 0)
    assert keys_right[1] == (
        f"{fluid.id}{SEPARATOR}0{SEPARATOR}right{SEPARATOR}{rem}",
        w,
        0,
    )

    # Left flow
    fluid.state.source = Directions.LEFT.value
    fluid.state._keys.clear()
    keys_left = fluid.frame.keys(fluid.id, fluid.state)
    assert keys_left[0] == (f"{fluid.id}{SEPARATOR}0", -w, 0)
    assert keys_left[1] == (
        f"{fluid.id}{SEPARATOR}0{SEPARATOR}left{SEPARATOR}{rem}",
        -(w + rem),
        0,
    )


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
    fluid.frame.index(fluid.id, fluid.properties)
    w, l = fluid.dimensions.w, fluid.dimensions.l

    stream_hb = Hitbox(Position(0, 0), Dimensions(w, 2 * l))
    flank_hb = Hitbox(Position(-w, 2 * l), Dimensions(3 * w, l))

    fluid.state.animation.frame = 0
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 2 * l
    fluid.state.pool = Pool(x=38, y=2 * l, w=3 * w, l=2 * l)
    fluid.state.hitboxes = [stream_hb, flank_hb]
    fluid.state.branches = []
    fluid.state._keys.clear()

    keys = fluid.frame.keys(fluid.id, fluid.state)

    # Stream corridor (2 full vertical tiles of length l)
    assert (f"{fluid.id}{SEPARATOR}0", 0, 0) in keys
    assert (f"{fluid.id}{SEPARATOR}0", 0, l) in keys

    # Flank corridor (3 horizontal steps of width w)
    assert (f"{fluid.id}{SEPARATOR}0", -w, 2 * l) in keys
    assert (f"{fluid.id}{SEPARATOR}0", 0, 2 * l) in keys
    assert (f"{fluid.id}{SEPARATOR}0", w, 2 * l) in keys


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
    id = "temperate-banks"
    props = mock_properties(
        AssetCategories.GEOGRAPHY.value,
        AssetInstances.SHORELINES.value,
    )
    crops = frame.index(id, props)

    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}up"] == (
        0, 0, props.dimensions.w, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}left"] == (
        0, props.dimensions.l, props.dimensions.w, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}down"] == (
        0, 2 * props.dimensions.l, props.dimensions.w, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}right"] == (
        0, 3 * props.dimensions.l, props.dimensions.w, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}summer{SEPARATOR}up"] == (
        props.dimensions.w, 0, props.dimensions.w, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}autumn{SEPARATOR}up"] == (
        2 * props.dimensions.w, 0, props.dimensions.w, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}winter{SEPARATOR}up"] == (
        3 * props.dimensions.w, 0, props.dimensions.w, props.dimensions.l
    )

    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}up{SEPARATOR}16"] == (
        0, 0, 16, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}down{SEPARATOR}16"] == (
        0, 2 * props.dimensions.w, 16, props.dimensions.l
    )
    assert crops[f"{id}{SEPARATOR}summer{SEPARATOR}up{SEPARATOR}16"] == (
        props.dimensions.w, 0, 16, props.dimensions.l
    )

    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}left{SEPARATOR}16"] == (
        0, props.dimensions.l, props.dimensions.w, 16
    )
    assert crops[f"{id}{SEPARATOR}spring{SEPARATOR}right{SEPARATOR}16"] == (
        0, 3 * props.dimensions.l, props.dimensions.w, 16
    )
    assert crops[f"{id}{SEPARATOR}winter{SEPARATOR}right{SEPARATOR}16"] == (
        3 * props.dimensions.w, 3 * props.dimensions.l, props.dimensions.w, 16
    )


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
        id="maize",
    )
    crops = crop.frame.index(crop.id, crop.properties)

    assert len(crops) == len(AnnualStages)
    for i, stage in enumerate(AnnualStages):
        key = f"maize{SEPARATOR}{stage.value}"
        assert crops[key] == (
            i * 32, 0, crop.properties.dimensions.w, crop.properties.dimensions.l
        )


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