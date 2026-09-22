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
    EffectState,
    AnimationState, 
    SpriteState, 
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
    Directions,
    ChannelTypes
)

@patch('app.game.screen.render.canvas')
@patch('app.game.screen.render.construct')
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


@patch('app.game.screen.render.canvas')
@patch('app.game.screen.render.construct')
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
    state = EffectState(id="base_id")
    
    # Use AnimatorState since AssetState (base) has strict slots and no 'animation' attribute
    anim_state = EffectState(id="anim_id")
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
    assert NoFrame().keys("dummy", state) == [("dummy", 0, 0)]
    
    # 2. SingleFrame
    assert SingleFrame().keys("dummy", state) == [("dummy", 0, 0)]
    
    # 3. IterableFrame
    assert IterableFrame().keys("eff", anim_state) == [("eff-2", 0, 0)]
    
    # 4. StateFrame
    assert StateFrame().keys("npc", anim_state) == [("npc-walk-down-2", 0, 0)]
    
    # 5. SpriteFrame (Strict Z-index: Base -> Armor -> Utility -> Tool -> Weapon -> Shield)
    keys = SpriteFrame().keys("player", sprite_state)
    expected_keys = [
        ("player-thrust-up-4", 0, 0),
        ("leather-thrust-up-4", 0, 0),
        ("sword-thrust-up-4", 0, 0),
        ("buckler-thrust-up-4", 0, 0)
    ]
    # NOTE: Missing None items (utility, tool) are dynamically dropped.
    assert keys == expected_keys


@patch('app.game.screen.render.render')
@patch('app.game.screen.render.canvas')
@patch('app.game.screen.render.construct')
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
    asset1.frame.keys.return_value = [("obj1-key", 0, 0)]
    
    # Asset 2: Outside camera view (culled)
    asset2 = MagicMock()
    asset2.category = AssetCategories.OBJECTS
    asset2.id = "obj2"
    asset2.state = MagicMock()
    asset2.state.position = Position(x=1000, y=1000)
    asset2.state.height = 1000
    asset2.state.depth = 0
    asset2.dimensions = Dimensions(w=32, l=32)
    asset2.frame.keys.return_value = [("obj2-key", 0, 0)]
    
    # Asset 3: Inside view, but should render ON TOP of Asset 1 (higher height)
    asset3 = MagicMock()
    asset3.category = AssetCategories.OBJECTS
    asset3.id = "obj3"
    asset3.state = MagicMock()
    asset3.state.position = Position(x=100, y=120)
    asset3.state.height = 120
    asset3.state.depth = 1
    asset3.dimensions = Dimensions(w=32, l=32)
    asset3.frame.keys.return_value = [("obj3-key", 0, 0)]
    
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

@patch('app.game.screen.render.canvas')
@patch('app.game.screen.render.construct')
def test_screen_camera_centering_sub_viewport(mock_construct, mock_canvas, mock_registry):
    """
    Ensure layers smaller than the viewport center correctly using negative camera offsets.
    """
    screen = Screen(
        screensize=Dimensions(w=480, l=480),
        boardsize=Dimensions(w=128, l=192),
        tiles=[],
        registry=mock_registry
    )

    # Focus coordinate should be disregarded; offset is derived strictly from dimension differences
    pos = screen.camera(focus=Position(x=64, y=96), dim=Dimensions(w=32, l=32))
    assert pos.x == -176  # -((480 - 128) // 2)
    assert pos.y == -144  # -((480 - 192) // 2)


@patch('app.game.screen.render.canvas')
@patch('app.game.screen.render.construct')
def test_screen_camera_asymmetric_centering(mock_construct, mock_canvas, mock_registry):
    """
    Ensure camera centers axes that are smaller than the viewport while clamping larger axes.
    """
    screen = Screen(
        screensize=Dimensions(w=480, l=480),
        boardsize=Dimensions(w=200, l=1000),
        tiles=[],
        registry=mock_registry
    )

    # Horizontal axis is sub-viewport (centered); vertical axis exceeds viewport (clamped)
    pos = screen.camera(focus=Position(x=100, y=800), dim=Dimensions(w=32, l=32))
    assert pos.x == -140  # -((480 - 200) // 2)
    assert pos.y == 520   # min(800 + 16 - 240, 1000 - 480)


@patch('app.game.screen.render.canvas')
@patch('app.game.screen.render.construct')
def test_screen_boardsize_preservation_and_canvas_allocation(mock_construct, mock_canvas, mock_registry):
    """
    Ensure Screen retains unpadded board dimensions while allocating canvas textures to viewport bounds.
    """
    screen = Screen(
        screensize=Dimensions(w=480, l=480),
        boardsize=Dimensions(w=128, l=192),
        tiles=[],
        registry=mock_registry
    )

    assert screen.boardsize.w == 128
    assert screen.boardsize.l == 192

    # Verify canvas allocation enforces hardware viewport minimums
    mock_canvas.assert_any_call(480, 480, opaque=True)
    
@patch('app.game.screen.render.render')
@patch('app.game.screen.render.canvas')
@patch('app.game.screen.render.construct')
def test_screen_draw_submerge_channel_splitting(
    mock_construct, 
    mock_canvas, 
    mock_render, 
    mock_registry
):
    """
    Test that Screen.draw splits texture passes into upper unmodulated and
    lower aquatic-modulated slices when ChannelTypes.SUBMERGE is active.
    """
    from app.assets.frames.core import ChannelTypes

    # Configure texture crop size to 64x64 matching sprite dimensions
    mock_registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 64, 64)

    screen = Screen(
        screensize=Dimensions(w=800, l=600),
        boardsize=Dimensions(w=1600, l=1200),
        tiles=[],
        registry=mock_registry
    )

    sprite_asset = MagicMock()
    sprite_asset.category = AssetCategories.SHEETS
    sprite_asset.id = "player"
    sprite_asset.state = MagicMock()
    sprite_asset.state.position = Position(x=100, y=100)
    sprite_asset.state.height = 100
    sprite_asset.state.depth = 0
    sprite_asset.dimensions = Dimensions(w=64, l=64)
    sprite_asset.properties = MagicMock()
    sprite_asset.frame.keys.return_value = [("player-walk-down-0", 0, 0)]
    sprite_asset.frame.channels.return_value = [
        (ChannelTypes.SUBMERGE.value, (32, 40, 110, 180, 170))
    ]

    screen.draw([sprite_asset], focus=Position(x=0, y=0), dim=Dimensions(w=32, l=32))

    mock_render.assert_called_once()
    active_assets = mock_render.call_args[0][2]

    # Upper slice and lower slice generated from single frame key
    assert len(active_assets) == 2

    # Upper slice: height 32, normal modulation (255, 255, 255, 255)
    upper = active_assets[0]
    assert upper[4] == 32    # sl = split_y = 32
    assert upper[6] == 100   # dy
    assert upper[8] == 32    # dl = split_y = 32
    assert upper[9:] == (255, 255, 255, 255)

    # Lower slice: height 32, aquatic modulation (40, 110, 180, 170)
    lower = active_assets[1]
    assert lower[2] == 32    # sy + split_y = 0 + 32 = 32
    assert lower[4] == 32    # rem_l = 64 - 32 = 32
    assert lower[6] == 132   # dy + split_y = 100 + 32 = 132
    assert lower[8] == 32    # dl = rem_l = 32
    assert lower[9:] == (40, 110, 180, 170)