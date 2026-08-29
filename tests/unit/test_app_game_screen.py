"""
# Ontology: tests.unit.test_app_game_screen.py
"""
from unittest.mock import patch, MagicMock

from app.game.screen import Screen
from app.assets.frames import (
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
    AnimatorState,
    Inventory, 
    Equipment
)
from libs.core.models import (
    Position, 
    Dimensions
)
from app.config.enums import (
    AssetCategories, 
    Actions, 
    Directions
)

@patch('app.game.screen.canvas')
@patch('app.game.screen.construct')
def test_screen_initialization(mock_construct, mock_canvas, mock_registry):
    """Test screen canvas initialization and geometry construction mapping."""
    mock_canvas.return_value = MagicMock()
    
    screen = Screen(
        screensize=Dimensions(w=800, l=600),
        boardsize=Dimensions(w=1600, l=1200),
        tiles=[],
        registry=mock_registry
    )
    
    assert mock_canvas.call_count == 2
    assert mock_construct.call_count == 2
    assert screen.screensize.w == 800
    assert screen.boardsize.w == 1600


@patch('app.game.screen.canvas')
@patch('app.game.screen.construct')
def test_screen_camera_clamping(mock_construct, mock_canvas, mock_registry):
    """Test that the camera clamps firmly to the board boundaries."""
    screen = Screen(
        screensize=Dimensions(w=800, l=600),
        boardsize=Dimensions(w=1600, l=1200),
        tiles=[],
        registry=mock_registry
    )
    
    # Focus near top-left (should clamp to 0,0)
    pos = screen.camera(focus=Position(x=100, y=100), dim=Dimensions(w=32, l=32))
    assert pos.x == 0
    assert pos.y == 0
    
    # Focus near bottom-right (should clamp to max bounds: board - screen)
    pos = screen.camera(focus=Position(x=1500, y=1100), dim=Dimensions(w=32, l=32))
    assert pos.x == 800  # 1600 - 800
    assert pos.y == 600  # 1200 - 600
    
    # Focus freely in the middle
    pos = screen.camera(focus=Position(x=800, y=600), dim=Dimensions(w=32, l=32))
    assert pos.x == 416  # 800 + 16 - 400
    assert pos.y == 316  # 600 + 16 - 300


def test_frame_keys_generation():
    """Ensure keys() methods calculate correctly for all possible Frame implementations."""
    state = AssetState(id="base_id")
    
    # Use AnimatorState since AssetState (base) has strict slots and no 'animation' attribute
    anim_state = AnimatorState(id="anim_id")
    anim_state.animation = AnimationState(action=Actions.WALK, direction=Directions.DOWN, frame=2)
    
    sprite_state = SpriteState(id="player", name="player_1")
    sprite_state.animation = AnimationState(action=Actions.THRUST, direction=Directions.UP, frame=4)
    sprite_state.inventory = Inventory(
        equipment=Equipment(
            armor="leather",
            weapon="sword",
            shield="buckler"
        )
    )
    
    # 1. NoFrame
    assert NoFrame().keys("dummy", state) == ["dummy"]
    
    # 2. SingleFrame
    assert SingleFrame().keys("dummy", state) == ["dummy"]
    
    # 3. IterableFrame
    assert IterableFrame().keys("eff", anim_state) == ["eff-2"]
    
    # 4. StateFrame
    assert StateFrame().keys("npc", anim_state) == ["npc-walk-down-2"]
    
    # 5. SpriteFrame (Strict Z-index: Base -> Armor -> Utility -> Tool -> Weapon -> Shield)
    keys = SpriteFrame().keys("player", sprite_state)
    expected_keys = [
        "player-thrust-up-4",
        "leather-thrust-up-4",
        "sword-thrust-up-4",
        "buckler-thrust-up-4"
    ]
    # NOTE: Missing None items (utility, tool) are dynamically dropped.
    assert keys == expected_keys


@patch('app.game.screen.render')
@patch('app.game.screen.canvas')
@patch('app.game.screen.construct')
def test_screen_draw_culling_and_sorting(mock_construct, mock_canvas, mock_render, mock_registry):
    """Test that Screen.draw correctly culls out-of-bounds assets and sorts by height/depth."""
    screen = Screen(
        screensize=Dimensions(w=800, l=600),
        boardsize=Dimensions(w=1600, l=1200),
        tiles=[],
        registry=mock_registry
    )
    
    # Create dummy assets
    # Asset 1: Inside camera view (cam is 0,0 to 800,600)
    # Removing `spec=Asset` to bypass strictly-enforced class attribute constraints on the mock
    asset1 = MagicMock()
    asset1.category = AssetCategories.OBJECTS
    asset1.id = "obj1"
    asset1.state = MagicMock()
    asset1.state.position = Position(x=100, y=100)
    asset1.state.height = 100
    asset1.state.depth = 0
    asset1.dimensions = Dimensions(w=32, l=32)
    asset1.frame.keys.return_value = ["obj1-key"]
    
    # Asset 2: Outside camera view (culled)
    asset2 = MagicMock()
    asset2.category = AssetCategories.OBJECTS
    asset2.id = "obj2"
    asset2.state = MagicMock()
    asset2.state.position = Position(x=1000, y=1000)
    asset2.state.height = 1000
    asset2.state.depth = 0
    asset2.dimensions = Dimensions(w=32, l=32)
    asset2.frame.keys.return_value = ["obj2-key"]
    
    # Asset 3: Inside view, but should render ON TOP of Asset 1 (higher height)
    asset3 = MagicMock()
    asset3.category = AssetCategories.OBJECTS
    asset3.id = "obj3"
    asset3.state = MagicMock()
    asset3.state.position = Position(x=100, y=120)
    asset3.state.height = 120
    asset3.state.depth = 1
    asset3.dimensions = Dimensions(w=32, l=32)
    asset3.frame.keys.return_value = ["obj3-key"]
    
    assets = [asset3, asset2, asset1]
    
    # Draw with camera focused securely at 0,0
    screen.draw(assets, focus=Position(x=0, y=0), dim=Dimensions(w=32, l=32))
    
    # Assert render was called once
    mock_render.assert_called_once()
    
    # Get the active_assets list passed to Cython render primitive mapper
    active_assets = mock_render.call_args[0][2]
    
    # Only asset1 and asset3 should be passed to Cython (asset2 is culled by the AABB checks)
    assert len(active_assets) == 2
    
    # Ensure they are sorted correctly: asset1 (height 100) drawn BEFORE asset3 (height 120)
    # The active_assets elements format index layout is: (tex, sx, sy, sw, sl, dx, dy, dw, dl)
    assert active_assets[0][5] == 100  # asset1 dx
    assert active_assets[0][6] == 100  # asset1 dy
    
    assert active_assets[1][5] == 100  # asset3 dx
    assert active_assets[1][6] == 120  # asset3 dy