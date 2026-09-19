"""
# Ontology: tests.unit.test_app_assets_frames
"""
from app.config.settings import SEPARATOR
from app.assets.frames import (
    NoFrame, 
    SingleFrame, 
    IterableFrame, 
    StateFrame, 
    SpriteFrame,
    IndexFrame
)
from app.models.properties import (
    ObjectProperties,
    TileProperties,
    SheetProperties,
    WidgetProperties,
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
    AttachmentState
)
from app.config.enums import (
    RequiredAssets,
    ExpressionsPalette
)

# Cython Libraries
from libs.core.models import Position, Dimensions


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

