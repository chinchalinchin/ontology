"""
# Ontology: tests.unit.test_app_assets_frames
"""
# Application Libraries
from app.config.settings import SEPARATOR
from app.assets.frames import (
    NoFrame, 
    SingleFrame, 
    IterableFrame, 
    StateFrame, 
    SpriteFrame,
    IndexFrame,
    FluidFrame
)
from app.models.properties import (
    ObjectProperties,
    TileProperties,
    SheetProperties,
    WidgetProperties,
    EffectProperties,
    Action,
    Direction
)
from app.models.state import (
    AnimationState, 
    SpriteState, 
    Inventory, 
    Equipment, 
    Psyche,
    IconState,
    AttachmentState,
    FluidState, 
    Pool
)
from app.config.enums import (
    Directions,
    RequiredAssets,
    ExpressionsPalette,
    ChannelTypes
)

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions,
    Hitbox
)


def test_no_frame():
    frame = NoFrame()
    assert frame.keys("test", None) == [("test", 0, 0)]
    props = ObjectProperties(dimensions=Dimensions(w=0, l=0))
    assert frame.index("test", props) == {"test": (0, 0, 0, 0)}


def test_single_frame():
    frame = SingleFrame()
    assert frame.keys("test", None) == [("test", 0, 0)]
    props = TileProperties(dimensions=Dimensions(w=32, l=32))
    assert frame.index("test", props) == {"test": (0, 0, 32, 32)}


def test_iterable_frame():
    frame = IterableFrame()
    state = SpriteState(id="test")
    state.animation.frame = 1
    
    expected_key = f"test{SEPARATOR}1"
    assert frame.keys("test", state) == [(expected_key, 0, 0)]
    
    props = ObjectProperties(dimensions=Dimensions(w=32, l=32), count=2)
    index = frame.index("test", props)
    assert index == {
        f"test{SEPARATOR}0": (0, 0, 32, 32),
        f"test{SEPARATOR}1": (32, 0, 32, 32)
    }


def test_state_frame():
    frame = StateFrame()
    state = SpriteState(id="test")
    state.animation.action = "walk"
    state.animation.direction = "down"
    state.animation.frame = 2
    
    expected_key = f"test{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}2"
    assert frame.keys("test", state) == [(expected_key, 0, 0)]

    props = SheetProperties(
        dimensions=Dimensions(w=32, l=32),
        actions={
            "walk": Action(count=2, directions={"down": Direction(row=0)})
        }
    )
    expected_index = {
        f"test{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}0": (0, 0, 32, 32),
        f"test{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}1": (32, 0, 32, 32)
    }
    assert frame.index("test", props) == expected_index


def test_sprite_frame():
    frame = SpriteFrame()
    
    equipment = Equipment(
        armor="leather_armor",
        utility="lantern",
        tool="pickaxe",
        weapon="sword",
        shield="buckler"
    )
    
    state = SpriteState(id="npc")
    state.animation = AnimationState(action="slash", direction="left", frame=3)
    state.inventory = Inventory(equipment=equipment)
    state.psyche = Psyche(
        expression=AttachmentState(
            id="bubble", layer="0", icon="loquacity", offset=Position(x=10, y=-10), ttl=100
        )
    )
    
    keys = frame.keys("npc", state)
    
    assert keys[0] == (f"npc{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[1] == (f"leather_armor{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[2] == (f"lantern{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[3] == (f"pickaxe{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[4] == (f"sword{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[5] == (f"buckler{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    
    expr_key = f"{ExpressionsPalette.BUBBLES.value}{SEPARATOR}loquacity"
    assert keys[6] == (expr_key, 10, -10)


def test_index_frame_indexing():
    frame = IndexFrame()
    props = WidgetProperties(
        dimensions=Dimensions(w=16, l=16),
        frames=["sword", "shield"]
    )
    assert frame.index("items", props) == {
        f"items{SEPARATOR}sword": (0, 0, 16, 16),
        f"items{SEPARATOR}shield": (16, 0, 16, 16)
    }


def test_index_frame_suppresses_vacant_slot():
    frame = IndexFrame()
    
    occupied_state = IconState(id="weapons", icon_function=lambda: "shortsword")
    keys = frame.keys("weapons", occupied_state)
    assert keys == [("weapons-shortsword", 0, 0)]

    empty_state = IconState(id="weapons", icon_function=lambda: "")
    assert frame.keys("weapons", empty_state) == []

    none_state = IconState(id="weapons", icon_function=lambda: None)
    assert frame.keys("weapons", none_state) == []


def test_sprite_frame_player_suppresses_expression():
    """
    Ensure player entities suppress expression attachments in SpriteFrame.keys.
    """
    frame = SpriteFrame()
    state = SpriteState(id=RequiredAssets.PLAYER.value)
    state.animation = AnimationState(action="walk", direction="down", frame=0)
    state.inventory = Inventory(equipment=Equipment())
    state.psyche = Psyche(
        expression=AttachmentState(
            id="bubble", layer="0", icon="loquacity", offset=Position(x=10, y=-10), ttl=100
        )
    )
    keys = frame.keys(RequiredAssets.PLAYER.value, state)
    
    # Only base persona key should be generated; expression overlay is omitted for player
    assert len(keys) == 1
    assert keys[0] == (f"{RequiredAssets.PLAYER.value}{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}0", 0, 0)


def test_sprite_frame_no_equipment():
    """
    Ensure SpriteFrame handles sprites with empty or None equipment inventories cleanly.
    """
    frame = SpriteFrame()
    state = SpriteState(id="npc")
    state.animation = AnimationState(action="walk", direction="down", frame=0)
    state.inventory = Inventory(equipment=None)
    state.psyche = Psyche()
    
    keys = frame.keys("npc", state)
    assert keys == [(f"npc{SEPARATOR}walk{SEPARATOR}down{SEPARATOR}0", 0, 0)]


def test_fluid_frame_indexing():
    """
    Verify FluidFrame generates full tile keys and directional forward/reverse
    fractional slices across dimensions and animation frames.
    """
    frame = FluidFrame()
    props = EffectProperties(dimensions=Dimensions(w=32, l=32), count=2)
    crops = frame.index("waterflow", props)

    # 1. Base full frames
    assert crops[f"waterflow{SEPARATOR}0"] == (0, 0, 32, 32)
    assert crops[f"waterflow{SEPARATOR}1"] == (32, 0, 32, 32)

    # 2. Forward vertical slicing: down
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}down{SEPARATOR}10"] == (0, 0, 32, 10)
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}down{SEPARATOR}slice{SEPARATOR}10"] == (0, 0, 32, 10)

    # 3. Reverse vertical slicing: up (anchored at distal edge 32 - 10 = 22)
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}up{SEPARATOR}10"] == (0, 22, 32, 10)
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}up{SEPARATOR}slice{SEPARATOR}10"] == (0, 22, 32, 10)

    # 4. Forward horizontal slicing: right
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}right{SEPARATOR}10"] == (0, 0, 10, 32)
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}right{SEPARATOR}slice{SEPARATOR}10"] == (0, 0, 10, 32)

    # 5. Reverse horizontal slicing: left (anchored at distal edge 32 - 10 = 22)
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}left{SEPARATOR}10"] == (22, 0, 10, 32)
    assert crops[f"waterflow{SEPARATOR}0{SEPARATOR}left{SEPARATOR}slice{SEPARATOR}10"] == (22, 0, 10, 32)


def test_fluid_frame_keys_downward_stream():
    """
    Verify downward stream emits full tile keys plus fractional terminal slice.
    """
    frame = FluidFrame(tile_w=32, tile_l=32)
    state = FluidState(
        id="waterflow",
        source=Directions.DOWN,
        length=48
    )
    keys = frame.keys("waterflow", state)

    assert len(keys) == 2
    assert keys[0] == (f"waterflow{SEPARATOR}0", 0, 0)
    assert keys[1] == (f"waterflow{SEPARATOR}0{SEPARATOR}down{SEPARATOR}16", 0, 32)


def test_fluid_frame_keys_upward_stream():
    """
    Verify upward stream emits negative Y-coordinate offsets and reverse slice keys.
    """
    frame = FluidFrame(tile_w=32, tile_l=32)
    state = FluidState(
        id="waterflow",
        source=Directions.UP,
        length=48
    )
    keys = frame.keys("waterflow", state)

    assert len(keys) == 2
    assert keys[0] == (f"waterflow{SEPARATOR}0", 0, -32)
    assert keys[1] == (f"waterflow{SEPARATOR}0{SEPARATOR}up{SEPARATOR}16", 0, -48)


def test_fluid_frame_keys_lateral_streams():
    """
    Verify lateral streams emit X-axis offsets for right and left flow vectors.
    """
    frame = FluidFrame(tile_w=32, tile_l=32)

    # Right flow
    state_right = FluidState(id="waterflow", source=Directions.RIGHT, length=48)
    keys_right = frame.keys("waterflow", state_right)
    assert keys_right[0] == (f"waterflow{SEPARATOR}0", 0, 0)
    assert keys_right[1] == (f"waterflow{SEPARATOR}0{SEPARATOR}right{SEPARATOR}16", 32, 0)

    # Left flow
    state_left = FluidState(id="waterflow", source=Directions.LEFT, length=48)
    keys_left = frame.keys("waterflow", state_left)
    assert keys_left[0] == (f"waterflow{SEPARATOR}0", -32, 0)
    assert keys_left[1] == (f"waterflow{SEPARATOR}0{SEPARATOR}left{SEPARATOR}16", -48, 0)


def test_fluid_frame_keys_with_annular_pool():
    """
    Verify annular pool hitboxes translate to grid-spaced frame key offsets.
    """
    frame = FluidFrame(tile_w=32, tile_l=32)
    stream_hb = Hitbox(Position(0, 0), Dimensions(32, 64))
    flank_hb = Hitbox(Position(-32, 64), Dimensions(96, 32))

    state = FluidState(
        id="waterflow",
        source=Directions.DOWN,
        length=64,
        pool=Pool(x=38, y=64, w=96, l=64),
        hitboxes=[stream_hb, flank_hb]
    )
    keys = frame.keys("waterflow", state)

    # Stream corridor (2 full 32px tiles)
    assert (f"waterflow{SEPARATOR}0", 0, 0) in keys
    assert (f"waterflow{SEPARATOR}0", 0, 32) in keys

    # Flank corridor (3 horizontal 32px steps along 96px width)
    assert (f"waterflow{SEPARATOR}0", -32, 64) in keys
    assert (f"waterflow{SEPARATOR}0", 0, 64) in keys
    assert (f"waterflow{SEPARATOR}0", 32, 64) in keys


def test_sprite_frame_channels_dry():
    """
    Verify SpriteFrame.channels returns an empty list when sprite is not submerged.
    """
    frame = SpriteFrame()
    state = SpriteState(id="player")
    state.mutators.triggers.submerged = False
    props = SheetProperties(dimensions=Dimensions(w=64, l=64))

    directives = frame.channels("player", state, props)
    assert directives == []


def test_sprite_frame_channels_submerged():
    """
    Verify SpriteFrame.channels emits SUBMERGE directive with half-length split
    and aquatic modulation payload when sprite is submerged.
    """
    frame = SpriteFrame()
    state = SpriteState(id="player")
    state.mutators.triggers.submerged = True
    props = SheetProperties(dimensions=Dimensions(w=64, l=64))

    directives = frame.channels("player", state, props)
    assert len(directives) == 1
    assert directives[0] == (
        ChannelTypes.SUBMERGE.value,
        (32, 40, 110, 180, 170)
    )