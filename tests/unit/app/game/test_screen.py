"""
# Ontology: tests.unit.test_app_game_screen.py
"""
# Standard Libraries
from unittest.mock import MagicMock

# External Libraries
import pytest

# Application Libraries
from app.game.screen import Screen
from app.assets.frames import (
    NoFrame, 
    SingleFrame, 
    IterableFrame, 
    StateFrame, 
    SpriteFrame,
    SeasonalFrame
)
from app.models.state import (
    EffectState,
    AnimationState, 
    SpriteState, 
    Inventory, 
    Equipment,
    CalendarState
)
from app.config.enums import (
    AssetCategories, 
    Actions, 
    Directions,
    ChannelTypes,
    Seasons,
    Cycles
)

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions
)


@pytest.mark.rendering
def test_screen_initialization(mock_screen):
    """Test screen canvas initialization and geometry construction mapping."""
    assert mock_screen.screensize.w == 320
    assert mock_screen.screensize.l == 240
    assert mock_screen.boardsize.w == 640
    assert mock_screen.boardsize.l == 480
    assert mock_screen.bg_canvas is not None
    assert mock_screen.fg_canvas is not None

@pytest.mark.rendering
def test_screen_camera_clamping(mock_screen):
    """Test that the camera clamps firmly to the board boundaries."""
    mock_screen.screensize = Dimensions(w=800, l=600)
    mock_screen.boardsize = Dimensions(w=1600, l=1200)

    # Focus near top-left (should clamp to 0,0)
    pos = mock_screen.camera(focus=Position(x=100, y=100), dim=Dimensions(w=32, l=32))
    assert pos.x == 0
    assert pos.y == 0

    # Focus near bottom-right (should clamp to max bounds: board - screen)
    pos = mock_screen.camera(focus=Position(x=1500, y=1100), dim=Dimensions(w=32, l=32))
    assert pos.x == 800  # 1600 - 800
    assert pos.y == 600  # 1200 - 600

    # Focus freely in the middle
    pos = mock_screen.camera(focus=Position(x=800, y=600), dim=Dimensions(w=32, l=32))
    assert pos.x == 416  # 800 + 16 - 400
    assert pos.y == 316  # 600 + 16 - 300


@pytest.mark.rendering
@pytest.mark.frames
def test_frame_keys_generation():
    """Ensure keys() methods calculate correctly for all possible Frame implementations."""
    # TODO: use fixtures
    state = EffectState(id="base_id")

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
    assert keys == expected_keys


@pytest.mark.rendering
def test_screen_draw_culling_and_sorting(
    mock_screen,
    mock_crate,
    mock_crate_alt,
    mock_chest,
    monkeypatch
):
    """
    Test that Screen.draw correctly culls out-of-bounds assets and sorts visible
    assets by the 3-key Painter's Algorithm (elevation, ground_y, priority).
    """
    mock_screen.screensize = Dimensions(w=800, l=600)
    mock_screen.boardsize = Dimensions(w=1600, l=1200)

    rendered_assets = []
    monkeypatch.setattr(
        "app.game.screen.render.render",
        lambda bg, fg, assets, px, py, sw, sl, target=None: rendered_assets.extend(assets)
    )

    # Asset 1: Inside camera view (cam is 0,0 to 800,600)
    mock_crate.elevation = 0
    mock_crate.state.position = Position(x=100, y=100)

    # Asset 2: Outside camera view (culled)
    mock_crate_alt.elevation = 0
    mock_crate_alt.state.position = Position(x=1000, y=1000)

    # Asset 3: Inside view, but renders on top of Asset 1 (higher ground_y)
    mock_chest.elevation = 0
    mock_chest.state.position = Position(x=100, y=120)

    # Pass in reverse-sorted order
    assets = [mock_chest, mock_crate_alt, mock_crate]

    mock_screen.draw(assets, focus=Position(x=0, y=0), dim=Dimensions(w=32, l=32))

    # Only mock_crate and mock_chest should be passed to render (mock_crate_alt is culled)
    assert len(rendered_assets) == 2

    # mock_crate (y=100, ground_y=132) drawn BEFORE mock_chest (y=120, ground_y=152)
    assert rendered_assets[0][5] == 100  # mock_crate dx
    assert rendered_assets[0][6] == 100  # mock_crate dy
    assert rendered_assets[1][5] == 100  # mock_chest dx
    assert rendered_assets[1][6] == 120  # mock_chest dy


@pytest.mark.rendering
def test_screen_camera_centering_sub_viewport(mock_screen):
    """
    Ensure layers smaller than the viewport center correctly using negative camera offsets.
    """
    mock_screen.screensize = Dimensions(w=480, l=480)
    mock_screen.boardsize = Dimensions(w=128, l=192)

    pos = mock_screen.camera(focus=Position(x=64, y=96), dim=Dimensions(w=32, l=32))
    assert pos.x == -176  # -((480 - 128) // 2)
    assert pos.y == -144  # -((480 - 192) // 2)


@pytest.mark.rendering
def test_screen_camera_asymmetric_centering(mock_screen):
    """
    Ensure camera centers axes that are smaller than the viewport while clamping larger axes.
    """
    mock_screen.screensize = Dimensions(w=480, l=480)
    mock_screen.boardsize = Dimensions(w=200, l=1000)

    pos = mock_screen.camera(focus=Position(x=100, y=800), dim=Dimensions(w=32, l=32))
    assert pos.x == -140  # -((480 - 200) // 2)
    assert pos.y == 520   # min(800 + 16 - 240, 1000 - 480)


@pytest.mark.rendering
def test_screen_boardsize_preservation_and_canvas_allocation(mock_screen, monkeypatch):
    """
    Ensure Screen retains unpadded board dimensions while allocating canvas textures to viewport bounds.
    """
    canvas_calls = []
    # TODO: is this not already patched in the fixtures?
    monkeypatch.setattr(
        "app.game.screen.render.canvas",
        lambda w, l, opaque=False: canvas_calls.append((w, l, opaque)) or MagicMock()
    )

    mock_screen.rebake(
        tiles=[],
        boardsize=Dimensions(w=128, l=192),
        calendar=CalendarState(),
        screensize=Dimensions(w=480, l=480)
    )

    assert mock_screen.boardsize.w == 128
    assert mock_screen.boardsize.l == 192
    assert (480, 480, True) in canvas_calls


@pytest.mark.rendering
@pytest.mark.fluids
def test_screen_draw_submerge_channel_splitting(
    mock_screen,
    mock_registry,
    monkeypatch
):
    """
    Test that Screen.draw splits texture passes into upper unmodulated and
    lower aquatic-modulated slices when ChannelTypes.SUBMERGE is active.
    """
    mock_screen.screensize = Dimensions(w=800, l=600)
    mock_screen.boardsize = Dimensions(w=1600, l=1200)

    mock_registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 64, 64)

    captured_renders = []
    # TODO: not needed
    monkeypatch.setattr(
        "app.game.screen.render.render",
        lambda bg, fg, assets, px, py, sw, sl, target=None: captured_renders.append(assets)
    )

    # TODO: USE FIXTURES!
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

    mock_screen.draw([sprite_asset], focus=Position(x=0, y=0), dim=Dimensions(w=32, l=32))

    assert len(captured_renders) == 1
    active_assets = captured_renders[0]

    assert len(active_assets) == 2

    # Upper slice: height 32, normal modulation
    upper = active_assets[0]
    assert upper[4] == 32    # sl = split_y
    assert upper[6] == 100   # dy
    assert upper[8] == 32    # dl = split_y
    assert upper[9:] == (255, 255, 255, 255)

    # Lower slice: height 32, aquatic modulation
    lower = active_assets[1]
    assert lower[2] == 32    # sy + split_y
    assert lower[4] == 32    # rem_l
    assert lower[6] == 132   # dy + split_y
    assert lower[8] == 32    # dl = rem_l
    assert lower[9:] == (40, 110, 180, 170)


# tests/unit/app/game/test_screen.py

@pytest.mark.rendering
def test_screen_draw_culling_and_sorting(
    mock_screen,
    mock_crate,
    mock_crate_alt,
    mock_chest,
    monkeypatch
):
    """
    Test that Screen.draw correctly culls out-of-bounds assets and sorts visible
    assets by the 3-key Painter's Algorithm (elevation, ground_y, priority).
    """
    mock_screen.screensize = Dimensions(w=800, l=600)
    mock_screen.boardsize = Dimensions(w=1600, l=1200)

    rendered_assets = []
    monkeypatch.setattr(
        "app.game.screen.render.render",
        lambda bg, fg, assets, px, py, sw, sl, target=None: rendered_assets.extend(assets)
    )

    # Asset 1: Inside camera view (cam is 0,0 to 800,600)
    mock_crate.elevation = 0
    mock_crate.state.position = Position(x=100, y=100)

    # Asset 2: Outside camera view (culled)
    mock_crate_alt.elevation = 0
    mock_crate_alt.state.position = Position(x=1000, y=1000)

    # Asset 3: Inside view, but renders on top of Asset 1 (higher ground_y)
    mock_chest.elevation = 0
    mock_chest.state.position = Position(x=100, y=120)

    # Pass in reverse-sorted order
    assets = [mock_chest, mock_crate_alt, mock_crate]

    mock_screen.draw(assets, focus=Position(x=0, y=0), dim=Dimensions(w=32, l=32))

    # Only mock_crate and mock_chest should be passed to render (mock_crate_alt is culled)
    assert len(rendered_assets) == 2

    # mock_crate (y=100, ground_y=132) drawn BEFORE mock_chest (y=120, ground_y=152)
    assert rendered_assets[0][5] == 100  # mock_crate dx
    assert rendered_assets[0][6] == 100  # mock_crate dy
    assert rendered_assets[1][5] == 100  # mock_chest dx
    assert rendered_assets[1][6] == 120  # mock_chest dy


@pytest.mark.rendering
def test_screen_sort_elevation_precedence(mock_crate, mock_strut):
    """
    Verify _sort enforces primary elevation tier ordering: higher elevation assets
    sort after lower elevation assets regardless of lower y + l values.
    """
    # mock_crate: l=32, y=200 -> ground_y = 232, elevation = 0
    mock_crate.elevation = 0
    mock_crate.state.position = Position(x=0, y=200)

    # mock_strut: l=133, y=10 -> ground_y = 143, elevation = 1
    mock_strut.elevation = 1
    mock_strut.state.position = Position(x=0, y=10)

    assert Screen._sort(mock_crate) == (0, 232, 0)
    assert Screen._sort(mock_strut) == (1, 143, 0)

    assets = [mock_strut, mock_crate]
    assets.sort(key=Screen._sort)

    # mock_crate (elevation 0) must render before mock_strut (elevation 1)
    assert assets[0] is mock_crate
    assert assets[1] is mock_strut


@pytest.mark.rendering
def test_screen_sort_ground_perspective_and_anchor(mock_crate, mock_strut):
    """
    Verify _sort evaluates secondary ground perspective (y + l + anchor) and tertiary
    properties.priority as a coplanar surface tie-breaker.
    """
    # Same elevation tier
    mock_crate.elevation = 0
    mock_crate.state.position = Position(x=0, y=50)  # l=32 -> 50 + 32 = 82
    mock_crate.state.anchor = 10                     # ground_y = 82 + 10 = 92
    mock_crate.properties.priority = 1

    mock_strut.elevation = 0
    mock_strut.state.position = Position(x=0, y=0)   # l=133 -> ground_y = 133
    mock_strut.state.anchor = 0
    mock_strut.properties.priority = 0

    assert Screen._sort(mock_crate) == (0, 92, 1)
    assert Screen._sort(mock_strut) == (0, 133, 0)

    assets = [mock_strut, mock_crate]
    assets.sort(key=Screen._sort)

    assert assets[0] is mock_crate
    assert assets[1] is mock_strut


@pytest.mark.rendering
def test_screen_sort_coplanar_priority_tie_breaker(mock_crate, mock_strut):
    """
    Verify _sort uses properties.priority to resolve tie-breakers between
    coplanar assets sharing identical elevation and ground contact baselines.
    """
    # Identical elevation and ground_y = 100
    mock_crate.elevation = 0
    mock_crate.state.position = Position(x=0, y=68)   # 68 + 32 = 100
    mock_crate.state.anchor = 0
    mock_crate.properties.priority = 1                # Decal / fixture

    mock_strut.elevation = 0
    mock_strut.state.position = Position(x=0, y=-33)  # -33 + 133 = 100
    mock_strut.state.anchor = 0
    mock_strut.properties.priority = 0                # Wall facade

    assert Screen._sort(mock_crate) == (0, 100, 1)
    assert Screen._sort(mock_strut) == (0, 100, 0)

    assets = [mock_crate, mock_strut]
    assets.sort(key=Screen._sort)

    # Priority 0 (wall) renders before Priority 1 (decal on top)
    assert assets[0] is mock_strut
    assert assets[1] is mock_crate


@pytest.mark.rendering
def test_screen_sort_substrate_hierarchy(
    mock_back_tile,
    mock_fluid,
    mock_shoreline,
    mock_bridge,
    mock_crate
):
    """
    Verify _sort lazily resolves negative substrate tiers when elevation is None,
    enforcing global substrate draw ordering underneath physical entities.
    """
    # Verify default substrate tier resolution via settings.SUBSTRATES
    assert mock_back_tile.elevation == -4
    assert mock_fluid.elevation == -3
    assert mock_shoreline.elevation == -2
    assert mock_bridge.elevation == -1
    assert mock_crate.elevation == 0

    assets = [mock_crate, mock_bridge, mock_shoreline, mock_fluid, mock_back_tile]
    print([ (asset.id, asset.name, asset.category, asset.instance, getattr(asset, 'dimensions', None)) for asset in assets ])
    assets.sort(key=Screen._sort)

    assert assets[0] is mock_back_tile  # elevation -4
    assert assets[1] is mock_fluid      # elevation -3
    assert assets[2] is mock_shoreline  # elevation -2
    assert assets[3] is mock_bridge     # elevation -1
    assert assets[4] is mock_crate      # elevation 0


@pytest.mark.rendering
@pytest.mark.seasons
def test_screen_initialization_with_calendar(mock_registry, monkeypatch):
    """
    Ensure Screen compiles initial tile canvases with the provided CalendarState.
    """
    construct_calls = []
    # WHY!?
    monkeypatch.setattr("app.game.screen.render.canvas", lambda w, l, opaque=False: MagicMock())
    monkeypatch.setattr(
        "app.game.screen.render.construct",
        lambda canvas, tiles: construct_calls.append((canvas, tiles))
    )

    calendar = CalendarState(
        season=Seasons.AUTUMN.value,
        cycle=Cycles.PEAK.value,
        period=1
    )
    # WHY?
    tile = MagicMock()
    tile.id = "temperate"
    tile.taxonomy.instance = "back"
    tile.state.position = Position(0, 0)
    tile.dimensions = Dimensions(32, 32)
    tile.state.multiple = MagicMock(nx=1, ny=1)
    tile.frame.eras.return_value = [("temperate-autumn-peak-1", 0, 0)]

    mock_registry.image.return_value = (MagicMock(), 0, 0, 32, 32)

    screen = Screen(
        screensize=Dimensions(w=480, l=480),
        boardsize=Dimensions(w=480, l=480),
        tiles=[tile],
        registry=mock_registry,
        calendar=calendar
    )

    tile.frame.eras.assert_called_once_with("temperate", calendar)
    assert len(construct_calls) == 2


@pytest.mark.rendering
@pytest.mark.seasons
def test_screen_reconstruct_updates_canvases_without_reallocating(
    mock_screen,
    monkeypatch
):
    """
    Ensure Screen.reconstruct queries eras() and rebuilds canvases
    without reallocating or destroying existing TexturePtr references.
    """
    reconstruct_calls = []
    realloc_calls = []

    # WHY!!!!?
    monkeypatch.setattr(
        "app.game.screen.render.construct",
        lambda canvas, tiles: reconstruct_calls.append((canvas, tiles))
    )
    monkeypatch.setattr(
        "app.game.screen.render.canvas",
        lambda w, l, opaque=False: realloc_calls.append((w, l, opaque))
    )

    updated_calendar = CalendarState(
        season=Seasons.WINTER.value,
        cycle=Cycles.DECLINE.value,
        period=2
    )

    tile = MagicMock()
    tile.id = "temperate"
    tile.taxonomy.instance = "back"
    tile.state.position = Position(0, 0)
    tile.dimensions = Dimensions(32, 32)
    tile.state.multiple = MagicMock(nx=1, ny=1)
    tile.frame.eras.return_value = [("temperate-winter-decline-2", 0, 0)]

    mock_screen.registry.image.return_value = (MagicMock(), 0, 0, 32, 32)

    mock_screen.reconstruct([tile], updated_calendar)

    tile.frame.eras.assert_called_once_with("temperate", updated_calendar)
    assert len(reconstruct_calls) == 2  # Once for bg_canvas, once for fg_canvas
    assert len(realloc_calls) == 0      # Zero GPU texture allocations during reconstruct