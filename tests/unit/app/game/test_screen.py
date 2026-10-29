"""
@domain.test
@test.unit
@app.core
@app.component

# Ontology: Tests - tests.unit.app.game.test_screen

Unit Tests for the Screen class.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.screen import Screen
from app.assets.frames import NoFrame
from app.models.state import (
    AnimationState,
    CalendarState,
)
from app.static.semantics import (
    AssetInstances,
    Actions,
    Directions,
    ChannelTypes,
    Seasons,
    Cycles,
    Substrates,
)

# Cython Libraries
from libs.core.models import (
    Position,
    Dimensions,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_core,
    pytest.mark.app_component,
    pytest.mark.workflow_rendering,
]

# ---------------------------------------------------------------------------


def test_screen_initialization(mock_screen):
    """Test screen canvas initialization and geometry construction mapping."""
    assert mock_screen.screensize.w == 320
    assert mock_screen.screensize.l == 240
    assert mock_screen.boardsize.w == 640
    assert mock_screen.boardsize.l == 480
    assert mock_screen.bg_canvas is not None
    assert mock_screen.fg_canvas is not None


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


@pytest.mark.asset_frame
def test_frame_keys_generation(mock_board):
    """Ensure keys() methods calculate correctly for core Frame implementations."""
    obstacle = mock_board.instances(AssetInstances.OBSTACLES.value)[0]
    effect = mock_board.instances(AssetInstances.PASSIVE.value)[0]
    pixie = mock_board.instances(AssetInstances.PIXIES.value)[0]
    player = mock_board.player()

    effect.state.animation = AnimationState(
        action=Actions.WALK.value,
        direction=Directions.DOWN.value,
        frame=2,
    )
    pixie.state.animation = AnimationState(
        action=Actions.WALK.value,
        direction=Directions.DOWN.value,
        frame=2,
    )
    player.state.animation = AnimationState(
        action=Actions.THRUST.value,
        direction=Directions.UP.value,
        frame=4,
    )
    player.state.inventory.equipment.armor = "leather"
    player.state.inventory.equipment.weapon = "shortsword"
    player.state.inventory.equipment.shield = "buckler"

    # 1. NoFrame
    assert NoFrame().keys(obstacle.id, obstacle.state) == [(obstacle.id, 0, 0)]

    # 2. SingleFrame
    assert obstacle.frame.keys(obstacle.id, obstacle.state) == [(obstacle.id, 0, 0)]

    # 3. IterableFrame
    assert effect.frame.keys(effect.id, effect.state) == [(f"{effect.id}-2", 0, 0)]

    # 4. StateFrame
    assert pixie.frame.keys(pixie.id, pixie.state) == [(f"{pixie.id}-walk-down-2", 0, 0)]

    # 5. SpriteFrame (Strict Z-index: Base -> Armor -> Utility -> Tool -> Weapon -> Shield)
    expected_keys = [
        ("player-thrust-up-4", 0, 0),
        ("leather-thrust-up-4", 0, 0),
        ("shortsword-thrust-up-4", 0, 0),
        ("buckler-thrust-up-4", 0, 0),
    ]
    assert player.frame.keys(player.id, player.state) == expected_keys


def test_screen_draw_culling_and_sorting(mock_screen, mock_board, mock_render):
    """
    Test that Screen.draw correctly culls out-of-bounds assets and sorts visible
    assets by the 4-key Painter's Algorithm (elevation, substrate, ground_y, priority).
    """
    mock_screen.screensize = Dimensions(w=800, l=600)
    mock_screen.boardsize = Dimensions(w=1600, l=1200)

    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    obstacle_culled = mock_board.instances(AssetInstances.OBSTACLES.value)[0]
    obstacle_fore = mock_board.instances(AssetInstances.OBSTACLES.value)[1]

    # Asset 1: Inside camera view (cam is 0,0 to 800,600), l=32 -> ground_y=132
    crate.state.elevation = 0
    crate.state.position = Position(x=100, y=100)

    # Asset 2: Outside camera view (culled)
    obstacle_culled.state.elevation = 0
    obstacle_culled.state.position = Position(x=1000, y=1000)

    # Asset 3: Inside view, renders on top of Asset 1 (l=56 -> ground_y=176)
    obstacle_fore.state.elevation = 0
    obstacle_fore.state.position = Position(x=100, y=120)

    assets = [obstacle_fore, obstacle_culled, crate]
    mock_screen.draw(assets, focus=Position(x=0, y=0), dim=Dimensions(w=32, l=32))

    rendered_assets = mock_render.render.call_args[0][2]
    assert len(rendered_assets) == 2

    # crate (y=100) drawn before obstacle_fore (y=120)
    assert rendered_assets[0][5] == 100
    assert rendered_assets[0][6] == 100
    assert rendered_assets[1][5] == 100
    assert rendered_assets[1][6] == 120


def test_screen_camera_centering_sub_viewport(mock_screen):
    """
    Ensure layers smaller than the viewport center correctly using negative camera offsets.
    """
    mock_screen.screensize = Dimensions(w=480, l=480)
    mock_screen.boardsize = Dimensions(w=128, l=192)

    pos = mock_screen.camera(focus=Position(x=64, y=96), dim=Dimensions(w=32, l=32))
    assert pos.x == -176  # -((480 - 128) // 2)
    assert pos.y == -144  # -((480 - 192) // 2)


def test_screen_camera_asymmetric_centering(mock_screen):
    """
    Ensure camera centers axes that are smaller than the viewport while clamping larger axes.
    """
    mock_screen.screensize = Dimensions(w=480, l=480)
    mock_screen.boardsize = Dimensions(w=200, l=1000)

    pos = mock_screen.camera(focus=Position(x=100, y=800), dim=Dimensions(w=32, l=32))
    assert pos.x == -140  # -((480 - 200) // 2)
    assert pos.y == 520   # min(800 + 16 - 240, 1000 - 480)


def test_screen_boardsize_preservation_and_canvas_allocation(mock_screen, mock_render):
    """
    Ensure Screen retains unpadded board dimensions while allocating canvas textures to viewport bounds.
    """
    mock_render.canvas.reset_mock()

    mock_screen.rebake(
        tiles=[],
        boardsize=Dimensions(w=128, l=192),
        calendar=CalendarState(),
        screensize=Dimensions(w=480, l=480),
    )

    assert mock_screen.boardsize.w == 128
    assert mock_screen.boardsize.l == 192
    mock_render.canvas.assert_any_call(480, 480, opaque=True)
    mock_render.canvas.assert_any_call(480, 480)


@pytest.mark.workflow_fluids
def test_screen_draw_submerge_channel_splitting(mock_screen, mock_board, mock_render):
    """
    Test that Screen.draw splits texture passes into upper unmodulated and
    lower aquatic-modulated slices when ChannelTypes.SUBMERGE is active.
    """
    mock_screen.screensize = Dimensions(w=800, l=600)
    mock_screen.boardsize = Dimensions(w=1600, l=1200)

    player = mock_board.player()
    player.state.position = Position(x=100, y=100)
    player.state.inventory.equipment.armor = None
    player.state.inventory.equipment.weapon = None
    player.state.inventory.equipment.shield = None
    player.state.inventory.equipment.tool = None
    player.state.inventory.equipment.utility = None
    player.state.mutators.triggers.submerged = True

    channels = player.frame.channels(player.id, player.state, player.properties)
    submerge_payload = next(
        payload for c_type, payload in channels if c_type == ChannelTypes.SUBMERGE.value
    )
    split_y, r, g, b, a = submerge_payload
    rem_l = player.dimensions.l - split_y

    mock_screen.draw([player], focus=Position(x=0, y=0), dim=Dimensions(w=32, l=32))

    active_assets = mock_render.render.call_args[0][2]
    assert len(active_assets) == 2

    # Upper slice: normal modulation
    upper = active_assets[0]
    assert upper[4] == split_y
    assert upper[6] == 100
    assert upper[8] == split_y
    assert upper[9:] == (255, 255, 255, 255)

    # Lower slice: aquatic modulation
    lower = active_assets[1]
    assert lower[2] == upper[2] + split_y
    assert lower[4] == rem_l
    assert lower[6] == 100 + split_y
    assert lower[8] == rem_l
    assert lower[9:] == (r, g, b, a)


def test_screen_sort_elevation_precedence(mock_board):
    """
    Verify _sort enforces primary elevation tier ordering: higher elevation assets
    sort after lower elevation assets regardless of lower y + l values.
    """
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    tree = mock_board.instances(AssetInstances.TREES.value)[0]

    # crate: l=32, y=200 -> ground_y = 232, elevation = 0
    crate.state.elevation = 0
    crate.state.position = Position(x=0, y=200)
    crate.state.anchor = 0
    crate.properties.priority = 0

    # tree: l=137, y=10 -> ground_y = 147, elevation = 1
    tree.state.elevation = 1
    tree.state.position = Position(x=0, y=10)
    tree.state.anchor = 0
    tree.properties.priority = 0

    assert Screen._sort(crate) == (0, 0, 232, 0)
    assert Screen._sort(tree) == (1, 0, 147, 0)

    assets = [tree, crate]
    assets.sort(key=Screen._sort)

    assert assets[0] is crate
    assert assets[1] is tree


def test_screen_sort_ground_perspective_and_anchor(mock_board):
    """
    Verify _sort evaluates tertiary ground perspective (y + l + anchor) and quaternary
    properties.priority as a coplanar surface tie-breaker.
    """
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    tree = mock_board.instances(AssetInstances.TREES.value)[0]

    crate.state.elevation = 0
    crate.state.position = Position(x=0, y=50)  # l=32 -> 50 + 32 = 82
    crate.state.anchor = 10                     # ground_y = 82 + 10 = 92
    crate.properties.priority = 1

    tree.state.elevation = 0
    tree.state.position = Position(x=0, y=0)    # l=137 -> ground_y = 137
    tree.state.anchor = 0
    tree.properties.priority = 0

    assert Screen._sort(crate) == (0, 0, 92, 1)
    assert Screen._sort(tree) == (0, 0, 137, 0)

    assets = [tree, crate]
    assets.sort(key=Screen._sort)

    assert assets[0] is crate
    assert assets[1] is tree


def test_screen_sort_coplanar_priority_tie_breaker(mock_board):
    """
    Verify _sort uses properties.priority to resolve tie-breakers between
    coplanar assets sharing identical elevation, substrate, and ground contact baselines.
    """
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    tree = mock_board.instances(AssetInstances.TREES.value)[0]

    # Identical elevation=0, substrate=0, and ground_y=100
    crate.state.elevation = 0
    crate.state.position = Position(x=0, y=68)   # 68 + 32 = 100
    crate.state.anchor = 0
    crate.properties.priority = 1

    tree.state.elevation = 0
    tree.state.position = Position(x=0, y=-37)   # -37 + 137 = 100
    tree.state.anchor = 0
    tree.properties.priority = 0

    assert Screen._sort(crate) == (0, 0, 100, 1)
    assert Screen._sort(tree) == (0, 0, 100, 0)

    assets = [crate, tree]
    assets.sort(key=Screen._sort)

    assert assets[0] is tree
    assert assets[1] is crate


def test_screen_sort_substrate_hierarchy(mock_board):
    """
    Verify _sort orders assets by intra-elevation substrate plane
    underneath standard physical entities at the same elevation.
    """
    environ_tile = mock_board.instances(AssetInstances.ENVIRON.value)[0]
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    bridge = mock_board.instances(AssetInstances.BRIDGES.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    for asset in (environ_tile, fluid, bridge, crate):
        asset.state.elevation = 0

    assert environ_tile.substrate == Substrates.ENVIRON.value
    assert fluid.substrate == Substrates.FLUIDS.value
    assert bridge.substrate == Substrates.OVERLAYS.value
    assert crate.substrate == Substrates.STANDARD.value

    assets = [crate, bridge, fluid, environ_tile]
    assets.sort(key=Screen._sort)

    assert assets[0] is environ_tile  # substrate -4
    assert assets[1] is fluid         # substrate -3
    assert assets[2] is bridge        # substrate -1
    assert assets[3] is crate         # substrate 0


@pytest.mark.workflow_seasons
def test_screen_initialization_with_calendar(mock_board, mock_registry, mock_render):
    """
    Ensure Screen compiles initial tile canvases with the provided CalendarState.
    """
    mock_render.construct.reset_mock()

    calendar = CalendarState(
        season=Seasons.AUTUMN.value,
        cycle=Cycles.PEAK.value,
        period=1,
    )
    tile = mock_board.instances(AssetInstances.ENVIRON.value)[0]

    screen = Screen(
        screensize=Dimensions(w=480, l=480),
        boardsize=Dimensions(w=480, l=480),
        tiles=[tile],
        registry=mock_registry,
        calendar=calendar,
    )

    assert mock_render.construct.call_count == 2
    bg_canvas, back_tiles = mock_render.construct.call_args_list[0][0]
    fg_canvas, fore_tiles = mock_render.construct.call_args_list[1][0]
    assert bg_canvas is screen.bg_canvas
    assert fg_canvas is screen.fg_canvas
    assert len(back_tiles) == 1
    assert len(fore_tiles) == 0


@pytest.mark.workflow_seasons
def test_screen_reconstruct_updates_canvases_without_reallocating(
    mock_screen,
    mock_board,
    mock_render,
):
    """
    Ensure Screen.reconstruct queries eras() and rebuilds canvases
    without reallocating or destroying existing TexturePtr references.
    """
    mock_render.canvas.reset_mock()
    mock_render.construct.reset_mock()

    updated_calendar = CalendarState(
        season=Seasons.WINTER.value,
        cycle=Cycles.DECLINE.value,
        period=2,
    )
    tile = mock_board.instances(AssetInstances.ENVIRON.value)[0]

    mock_screen.reconstruct([tile], updated_calendar)

    assert mock_render.canvas.call_count == 0
    assert mock_render.construct.call_count == 2
    _, back_tiles = mock_render.construct.call_args_list[0][0]
    assert len(back_tiles) == 1