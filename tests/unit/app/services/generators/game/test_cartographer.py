"""
# Ontology: tests.unit.services.generators.game.test_cartographer
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    AssetInstances,
    Directions
)
from app.models.state import (
    Branch,
    Pool
)
from app.services.generators.game.cartographer import Cartographer

# Cython Libraries
from libs.core.models import Position


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_collect_water_rectangles(mock_board):
    """
    Verify active stream corridors and annular pools are correctly extracted
    into primitive (min_x, min_y, max_x, max_y) AABB tuples.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 96
    fluid.state.pool = Pool(x=0, y=32, w=192, l=160)

    rects = Cartographer._collect_water_rectangles("0", mock_board)

    # Corridor: (70, 0, 70 + 32, 0 + 96) -> (70, 0, 102, 96)
    assert (70, 0, 102, 96) in rects
    # Pool: (0, 32, 0 + 192, 32 + 160) -> (0, 32, 192, 192)
    assert (0, 32, 192, 192) in rects


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_generate_and_coalesce_shorelines(
    mock_board, 
    mock_shoreline_index, 
    mock_actuator
):
    """
    Verify Cartographer sweeps fluid contours, samples substrate tiles,
    and returns coalesced Shoreline assets without mutating board state.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    mock_actuator.propagate(fluid, mock_board)

    shores = Cartographer.generate("0", mock_board, mock_shoreline_index)

    assert len(shores) > 0
    for shore in shores:
        assert shore.instance == AssetInstances.SHORELINES.value
        assert shore.state.layer == "0"
        assert shore.state.length > 0
        assert len(shore.hitboxes) == 1

    # Verify board state is not mutated by generate()
    assert len(mock_board.shorelines("0")) == 0


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_purge_clears_layer_shorelines(
    mock_board, 
    mock_shoreline_index, 
    mock_actuator
):
    """
    Verify Cartographer.purge disposes of all procedural shorelines on the target layer.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    mock_actuator.propagate(fluid, mock_board)

    shores = Cartographer.generate("0", mock_board, mock_shoreline_index)
    mock_board.add(shores)
    assert len(mock_board.shorelines("0")) > 0

    Cartographer.purge("0", mock_board)
    assert len(mock_board.shorelines("0")) == 0


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_coincident_pools_do_not_deadlock(
    mock_board, 
    mock_shoreline_index, 
    mock_actuator, 
    mock_fluid_alt2
):
    """
    Verify Bug B015 fix: two parallel fluid streams forming identical/overlapping
    annular pools merge through contour analysis without mutual exclusion deadlock.
    """
    fluid1 = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid1.state.position = Position(x=70, y=0)
    fluid1.state.source = Directions.DOWN.value
    fluid1.state.flow = 2

    # Remove pre-existing secondary fluids to isolate the test
    other_fluids = [f for f in mock_board.instances(AssetInstances.FLUIDS.value, "0") if f is not fluid1]
    mock_board.remove(other_fluids)

    # Add parallel adjacent fluid stream
    mock_fluid_alt2.state.position = Position(x=102, y=0)
    mock_fluid_alt2.state.source = Directions.DOWN.value
    mock_fluid_alt2.state.flow = 2
    mock_board.add([mock_fluid_alt2])

    # Static barrier struck by both fluids at y=96
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=96)

    mock_actuator.propagate(fluid1, mock_board)
    mock_actuator.propagate(mock_fluid_alt2, mock_board)

    shores = Cartographer.generate("0", mock_board, mock_shoreline_index)

    # Shorelines must be synthesized around the composite pool perimeter
    assert len(shores) > 0


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_fluid_meeting_fluid_suppresses_shorelines(
    mock_board, 
    mock_shoreline_index, 
    mock_actuator, 
    mock_fluid_alt2
):
    """
    Verify that interior fluid-to-fluid thresholds between adjacent streams
    do not generate dividing shorelines.
    """
    fluid1 = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid1.state.position = Position(x=70, y=0)
    fluid1.state.source = Directions.DOWN.value

    # Remove pre-existing secondary fluids to isolate the two parallel streams
    other_fluids = [
        f for f in mock_board.instances(AssetInstances.FLUIDS.value, "0") 
        if f is not fluid1
    ]
    mock_board.remove(other_fluids)

    # Fluid 2 placed directly along East margin of Fluid 1 (x=70 + 32 = 102)
    mock_fluid_alt2.state.position = Position(x=102, y=0)
    mock_fluid_alt2.state.source = Directions.DOWN.value
    mock_board.add([mock_fluid_alt2])

    mock_actuator.propagate(fluid1, mock_board)
    mock_actuator.propagate(mock_fluid_alt2, mock_board)

    shores = Cartographer.generate("0", mock_board, mock_shoreline_index)

    left_shores = [
        s for s in shores 
        if s.state.orientation == Directions.LEFT.value
    ]
    right_shores = [
        s for s in shores 
        if s.state.orientation == Directions.RIGHT.value
    ]

    # Outer West margin (x=70) generates West shorelines
    assert len(left_shores) > 0
    assert all(s.state.position.x == 70 for s in left_shores)

    # Outer East margin (x=102..134) generates East shorelines positioned at x=102
    assert len(right_shores) > 0
    assert all(s.state.position.x == 102 for s in right_shores)

    # Dividing seam at x=102 must NOT generate an internal West shoreline (orientation=LEFT)
    assert not any(s.state.orientation == Directions.LEFT.value and s.state.position.x == 102 for s in shores)

    # Dividing seam at x=102 must NOT generate an internal East shoreline (orientation=RIGHT at x=70)
    assert not any(s.state.orientation == Directions.RIGHT.value and s.state.position.x == 70 for s in shores)


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_empty_fluid_returns_empty(mock_board, mock_shoreline_index):
    """
    Verify layers with no active fluid bodies return an empty list without error.
    """
    shores = Cartographer.generate("unpopulated-layer", mock_board, mock_shoreline_index)
    assert shores == []


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_board_shoreline_lifecycle(mock_board, mock_shoreline):
    """
    Verify that Board correctly indexes and tracks procedural shoreline assets
    in board.shorelines[layer] on add and remove.
    """
    assert len(mock_board.shorelines("0")) == 0

    mock_board.add([mock_shoreline])
    assert len(mock_board.shorelines("0")) == 1
    assert mock_board.shorelines("0")[0] is mock_shoreline

    mock_board.remove([mock_shoreline])
    assert len(mock_board.shorelines("0")) == 0


@pytest.mark.fluids
@pytest.mark.services
def test_cartographer_collects_active_branch_rectangles(mock_board):
    """
    Verify Cartographer._collect_water_rectangles compiles bounding boxes for
    parent streams, annular pools, and active child branch corridors.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 32
    fluid.state.pool = Pool(x=0, y=32, w=192, l=160)
    fluid.state.branches = [
        Branch(
            position=Position(x=0, y=192),
            source=Directions.DOWN.value,
            flow=1,
            length=127
        ),
        Branch(
            position=Position(x=160, y=192),
            source=Directions.DOWN.value,
            flow=1,
            length=127
        )
    ]

    rects = Cartographer._collect_water_rectangles("0", mock_board)

    # Parent stream
    assert (70, 0, 102, 32) in rects
    # Annular pool
    assert (0, 32, 192, 192) in rects
    # Left branch corridor: (0, 192, 32, 192 + 127) -> (0, 192, 32, 319)
    assert (0, 192, 32, 319) in rects
    # Right branch corridor: (160, 192, 192, 192 + 127) -> (160, 192, 192, 319)
    assert (160, 192, 192, 319) in rects