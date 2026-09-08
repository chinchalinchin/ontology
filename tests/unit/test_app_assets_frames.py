"""
# Ontology: tests.unit.test_app_assets_frames
"""
from app.assets.frames.core import (
    NoFrame, 
    SingleFrame, 
    IterableFrame, 
    StateFrame, 
    SpriteFrame
)
from app.models.state import (
    AssetState, 
    AnimationState, 
    SpriteState, 
    Inventory, 
    Equipment, 
    Psyche
)
from app.models.state.objects import AttachmentState
from app.config.enums import ExpressionsPalette
from libs.core.models import Position
from app.config.settings import SEPARATOR

def test_no_frame():
    frame = NoFrame()
    assert frame.keys("test", None) == [("test", 0, 0)]
    assert frame.index("test", {}) == {"test": (0, 0, 0, 0)}

def test_single_frame():
    frame = SingleFrame()
    assert frame.keys("test", None) == [("test", 0, 0)]
    assert frame.index("test", {"dimensions": {"w": 32, "l": 32}}) == {"test": (0, 0, 32, 32)}

def test_iterable_frame():
    frame = IterableFrame()
    state = SpriteState(id="test")
    state.animation.frame = 1
    
    expected_key = f"test{SEPARATOR}1"
    assert frame.keys("test", state) == [(expected_key, 0, 0)]
    
    index = frame.index("test", {"dimensions": {"w": 32, "l": 32}, "count": 2})
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

def test_sprite_frame():
    frame = SpriteFrame()
    
    # Configure equipment in strict Z-index stack order
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
    
    # 1. Base Sprite Persona
    assert keys[0] == (f"npc{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    
    # 2-6. Z-Indexed Equipment
    assert keys[1] == (f"leather_armor{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[2] == (f"lantern{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[3] == (f"pickaxe{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[4] == (f"sword{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    assert keys[5] == (f"buckler{SEPARATOR}slash{SEPARATOR}left{SEPARATOR}3", 0, 0)
    
    # 7. Dynamic Expression Overlays
    expr_key = f"{ExpressionsPalette.BUBBLES.value}{SEPARATOR}loquacity"
    assert keys[6] == (expr_key, 10, -10)