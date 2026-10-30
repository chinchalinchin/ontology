"""
@domain.test
@test.unit
@app.services
@workflow.generation
@workflow.fluids

# Ontology: Tests - tests.unit.services.generators.game.test_cartographer

Unit tests for the Cartographer service.
"""
# External Libraries
import pytest

# Application Libraries
from app.services.generators.game.cartographer import Cartographer
from app.static.semantics import (
    AssetInstances,
    Directions,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_fluids,
]

# -----------------------------------------------------


def test_cartographer_collect_water_rectangles(mock_board):
    """
    Verify active stream corridors and annular pools are correctly extracted
    into primitive (min_x, min_y, max_x, max_y) AABB tuples.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fw = fluid.properties.dimensions.w
    fx = fluid.state.position.x
    fy = fluid.state.position.y
    pool = fluid.state.pool

    rects = Cartographer._collect_water_rectangles("0", mock_board)

    assert (fx, fy, fx + fw, fy + fluid.state.length) in rects
    assert pool is not None
    assert (pool.x, pool.y, pool.x + pool.w, pool.y + pool.l) in rects


def test_cartographer_generate_and_coalesce_shorelines(
    mock_board,
    mock_shoreline_index,
):
    """
    Verify Cartographer sweeps fluid contours, samples substrate tiles,
    aligns shoreline hitboxes to ShorelineProperties.dimensions (Fix B018),
    and returns coalesced Shoreline assets without mutating board state.
    """
    Cartographer.purge("0", mock_board)
    assert len(mock_board.shorelines("0")) == 0

    shores = Cartographer.generate("0", mock_board, mock_shoreline_index)

    assert len(shores) > 0
    for shore in shores:
        assert shore.instance == AssetInstances.SHORELINES.value
        assert shore.state.layer == "0"
        assert shore.state.length > 0
        assert len(shore.hitboxes) == 1
        hb = shore.hitboxes[0]
        if shore.state.orientation == Directions.DOWN.value:
            assert hb.position.y == shore.dimensions.l - shore.properties.thickness
        elif shore.state.orientation == Directions.RIGHT.value:
            assert hb.position.x == shore.dimensions.w - shore.properties.thickness

    assert len(mock_board.shorelines("0")) == 0


def test_cartographer_purge_clears_layer_shorelines(mock_board):
    """
    Verify Cartographer.purge disposes of all procedural shorelines on the target layer.
    """
    assert len(mock_board.shorelines("0")) > 0

    Cartographer.purge("0", mock_board)
    assert len(mock_board.shorelines("0")) == 0


def test_cartographer_coincident_pools_do_not_deadlock(
    mock_board,
    mock_shoreline_index,
    mock_actuator,
):
    """
    Verify Bug B015 fix: two parallel fluid streams forming identical/overlapping
    annular pools merge through contour analysis without mutual exclusion deadlock.
    """
    fluid1, fluid2 = mock_board.instances(AssetInstances.FLUIDS.value, "0")[:2]
    fw = fluid1.properties.dimensions.w

    fluid1.state.position = Position(x=200, y=0)
    fluid1.state.source = Directions.DOWN.value
    fluid1.state.flow = 2

    fluid2.state.position = Position(x=200 + fw, y=0)
    fluid2.state.source = Directions.DOWN.value
    fluid2.state.flow = 2

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=264, y=150)

    mock_actuator.propagate(fluid1, mock_board)
    mock_actuator.propagate(fluid2, mock_board)
    mock_board.update_fluid_cache("0")

    shores = Cartographer.generate("0", mock_board, mock_shoreline_index)

    assert len(shores) > 0


def test_cartographer_fluid_meeting_fluid_suppresses_shorelines(
    mock_board,
    mock_shoreline_index,
    mock_actuator,
):
    """
    Verify that interior fluid-to-fluid thresholds between adjacent streams
    do not generate dividing shorelines and outer margins align with shoreline dimensions (Fix B018).
    """
    fluid1, fluid2 = mock_board.instances(AssetInstances.FLUIDS.value, "0")[:2]
    fw = fluid1.properties.dimensions.w
    x1 = 1200
    x2 = x1 + fw

    fluid1.state.position = Position(x=x1, y=0)
    fluid1.state.source = Directions.DOWN.value
    fluid1.state.flow = 0

    fluid2.state.position = Position(x=x2, y=0)
    fluid2.state.source = Directions.DOWN.value
    fluid2.state.flow = 0

    mock_actuator.propagate(fluid1, mock_board)
    mock_actuator.propagate(fluid2, mock_board)
    mock_board.update_fluid_cache("0")

    shores = Cartographer.generate("0", mock_board, mock_shoreline_index)

    left_shores = [
        s for s in shores
        if s.state.orientation == Directions.LEFT.value
        and s.state.position.x >= x1
    ]
    right_shores = [
        s for s in shores
        if s.state.orientation == Directions.RIGHT.value
        and s.state.position.x >= x1
    ]

    assert len(left_shores) > 0
    assert all(s.state.position.x == x1 for s in left_shores)

    assert len(right_shores) > 0
    assert all(
        s.state.position.x == x2 + fw - s.dimensions.w
        for s in right_shores
    )

    assert not any(
        s.state.orientation == Directions.LEFT.value and s.state.position.x == x2
        for s in shores
    )
    assert not any(
        s.state.orientation == Directions.RIGHT.value
        and s.state.position.x == x2 - s.dimensions.w
        for s in shores
    )


def test_cartographer_empty_fluid_returns_empty(mock_board, mock_shoreline_index):
    """
    Verify layers with no active fluid bodies return an empty list without error.
    """
    shores = Cartographer.generate("unpopulated-layer", mock_board, mock_shoreline_index)
    assert shores == []


def test_cartographer_board_shoreline_frequency(mock_board):
    """
    Verify that Board correctly indexes and tracks procedural shoreline assets
    in board.shorelines(layer) on add and remove.
    """
    shores = list(mock_board.shorelines("0"))
    assert len(shores) > 0

    target_shore = shores[0]
    mock_board.remove(shores)
    assert len(mock_board.shorelines("0")) == 0

    mock_board.add([target_shore])
    assert len(mock_board.shorelines("0")) == 1
    assert mock_board.shorelines("0")[0] is target_shore


def test_cartographer_collects_active_branch_rectangles(mock_board):
    """
    Verify Cartographer._collect_water_rectangles compiles bounding boxes for
    parent streams, annular pools, and active child branch corridors.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fw = fluid.properties.dimensions.w

    rects = Cartographer._collect_water_rectangles("0", mock_board)

    assert len(fluid.state.branches) == 2
    for branch in fluid.state.branches:
        assert (
            branch.position.x,
            branch.position.y,
            branch.position.x + fw,
            branch.position.y + branch.length,
        ) in rects