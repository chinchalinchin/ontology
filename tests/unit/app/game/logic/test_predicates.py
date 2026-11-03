"""
@domain.test
@domain.logic
@test.unit
@app.asset
@app.semantics

# Ontology: Tests - tests.unit.app.game.logic.test_predicates

Stateless Asset Predicate Unit Tests.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic import predicates
from app.models.state.assets.effects import (
    Branch,
    Pool,
)
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
)

# Cython Libraries
from libs.core.models import Position

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_asset,
    pytest.mark.app_config
]

# ---------------------------------------------------------------------------
# ------------------------------------------- PHYSICAL & OBSTACLE PREDICATES
# ---------------------------------------------------------------------------


@pytest.mark.workflow_collisions
def test_is_weight_qualification(mock_asset):
    """
    Verifies predicates.is_weight() includes dynamic (m > 0) and static (m = 0)
    physical bodies while excluding sensors (m = -1) and non-physical categories.
    """
    # Dynamic and static physical bodies (m >= 0)
    player = mock_asset(AssetCategories.SHEETS.value, AssetInstances.PLAYERS.value)
    sprite = mock_asset(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    crate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    chest = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CHESTS.value)
    obstacle = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.OBSTACLES.value)
    tree = mock_asset(AssetCategories.RESOURCES.value, AssetInstances.TREES.value)

    assert predicates.is_weight(player) is True
    assert predicates.is_weight(sprite) is True
    assert predicates.is_weight(crate) is True
    assert predicates.is_weight(chest) is True
    assert predicates.is_weight(obstacle) is True
    assert predicates.is_weight(tree) is True

    # Sensors (m = -1) and excluded categories (effects, tiles)
    sign = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.SIGNS.value)
    bridge = mock_asset(AssetCategories.CRAFTS.value, AssetInstances.BRIDGES.value)
    fluid = mock_asset(AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)
    passive = mock_asset(AssetCategories.EFFECTS.value, AssetInstances.PASSIVE.value)
    environ = mock_asset(AssetCategories.TILES.value, AssetInstances.ENVIRON.value)

    assert predicates.is_weight(sign) is False
    assert predicates.is_weight(bridge) is False
    assert predicates.is_weight(fluid) is False
    assert predicates.is_weight(passive) is False
    assert predicates.is_weight(environ) is False


@pytest.mark.workflow_collisions
def test_is_obstacle_qualification(mock_asset):
    """
    Verifies predicates.is_obstacle() identifies structural and navigational
    obstruction instances and excludes non-obstacle instances.
    """
    chest = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CHESTS.value)
    sign = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.SIGNS.value)
    crate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    gate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    strut = mock_asset(AssetCategories.CRAFTS.value, AssetInstances.STRUTS.value)
    obstacle = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.OBSTACLES.value)
    tree = mock_asset(AssetCategories.RESOURCES.value, AssetInstances.TREES.value)

    for asset in (chest, sign, crate, gate, strut, obstacle, tree):
        assert predicates.is_obstacle(asset) is True

    player = mock_asset(AssetCategories.SHEETS.value, AssetInstances.PLAYERS.value)
    sprite = mock_asset(AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    bridge = mock_asset(AssetCategories.CRAFTS.value, AssetInstances.BRIDGES.value)
    raft = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.RAFTS.value)
    crop = mock_asset(AssetCategories.RESOURCES.value, AssetInstances.CROPS.value)
    fluid = mock_asset(AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)
    environ = mock_asset(AssetCategories.TILES.value, AssetInstances.ENVIRON.value)

    for asset in (player, sprite, bridge, raft, crop, fluid, environ):
        assert predicates.is_obstacle(asset) is False


# ---------------------------------------------------------------------------
# ------------------------------------------------ FLUID CONTAINMENT PREDICATES
# ---------------------------------------------------------------------------


@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_in_pool_containment(mock_asset):
    """
    Verifies predicates.in_pool() evaluates coordinate containment against
    active annular Pool boundaries and rejects empty or degenerate pools.
    """
    fluid = mock_asset(AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)

    # 1. No pool configured
    fluid.state.pool = None
    assert predicates.in_pool(Position(70, 70), fluid) is False

    # 2. Degenerate pool dimensions
    fluid.state.pool = Pool(x=64, y=64, w=0, l=32)
    assert predicates.in_pool(Position(64, 70), fluid) is False

    # 3. Active pool bounding box [64..128, 64..128]
    fluid.state.pool = Pool(x=64, y=64, w=64, l=64)
    assert predicates.in_pool(Position(96, 96), fluid) is True
    assert predicates.in_pool(Position(32, 96), fluid) is False
    assert predicates.in_pool(Position(160, 160), fluid) is False


@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
@pytest.mark.parametrize(
    "direction,inside_coords,outside_coords",
    [
        (Directions.DOWN.value, (70, 100), (70, 40)),
        (Directions.UP.value, (70, 20), (70, 100)),
        (Directions.RIGHT.value, (100, 70), (20, 70)),
        (Directions.LEFT.value, (20, 70), (200, 70)),
    ],
)
def test_in_stream_directional_corridors(
    mock_asset,
    direction: str,
    inside_coords: tuple[int, int],
    outside_coords: tuple[int, int],
):
    """
    Verifies predicates.in_stream() projects parent stream corridors across
    all four cardinal source directions.
    """
    fluid = mock_asset(AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)
    fluid.state.position = Position(64, 64)
    fluid.state.source = direction
    fluid.state.length = 96
    fluid.state.branches = []

    assert predicates.in_stream(Position(*inside_coords), fluid) is True
    assert predicates.in_stream(Position(*outside_coords), fluid) is False


@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_in_stream_branches_and_zero_length(mock_asset):
    """
    Verifies predicates.in_stream() evaluates active child Branch corridors
    and ignores zero-length streams or branches.
    """
    fluid = mock_asset(AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)
    fluid.state.position = Position(64, 64)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 0
    fluid.state.branches = []

    # Zero-length parent stream with no branches
    assert predicates.in_stream(Position(70, 80), fluid) is False

    # Add a degenerate branch (length=0) and an active RIGHT branch at (160, 160)
    fluid.state.length = 64
    fluid.state.branches = [
        Branch(
            position=Position(160, 160),
            source=Directions.LEFT.value,
            flow=1,
            length=0,
        ),
        Branch(
            position=Position(160, 160),
            source=Directions.RIGHT.value,
            flow=1,
            length=128,
        ),
    ]

    assert predicates.in_stream(Position(140, 170), fluid) is False
    assert predicates.in_stream(Position(220, 170), fluid) is True


@pytest.mark.workflow_fluids
@pytest.mark.workflow_ecology
def test_in_fluid_composite_containment(mock_asset):
    """
    Verifies predicates.in_fluid() returns True when a coordinate intersects
    either the annular Pool or any active stream corridor, and False otherwise.
    """
    fluid = mock_asset(AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)
    fluid.state.position = Position(64, 64)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 96
    fluid.state.pool = Pool(x=48, y=160, w=128, l=64)
    fluid.state.branches = [
        Branch(
            position=Position(176, 160),
            source=Directions.DOWN.value,
            flow=1,
            length=96,
        )
    ]

    # Inside parent stream corridor
    assert predicates.in_fluid(Position(70, 100), fluid) is True
    # Inside annular pool
    assert predicates.in_fluid(Position(55, 180), fluid) is True
    # Inside child branch corridor
    assert predicates.in_fluid(Position(185, 210), fluid) is True
    # Outside all fluid geometry
    assert predicates.in_fluid(Position(10, 10), fluid) is False