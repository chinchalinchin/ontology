"""
# Ontology: tests.unit.test_app_game_logic_modules_paths
"""
from unittest.mock import patch
import pytest

from app.game.logic.modules.paths.plan import Node, Planner
from libs.core.math.paths import rrt
from libs.core.models import Position


def test_node_initialization():
    node = Node(10.5, 20.25)
    assert node.x == 10.5
    assert node.y == 20.25
    assert node.parent is None


def test_planner_initialization():
    start = Position(x=10, y=10)
    target = Position(x=50, y=60)
    obstacles = [(20.0, 20.0, 10.0, 10.0)]
    step_size = 16.0

    planner = Planner(start=start, target=target, obstacles=obstacles, step_size=step_size, max_iter=100)

    assert planner.start == start
    assert planner.target == target
    assert planner.obstacles == obstacles
    assert planner.step_size == 16.0
    assert planner.max_iter == 100


def test_rrt_direct_clear_path():
    path = rrt(0.0, 0.0, 30.0, 0.0, [], step_size=15.0, max_iter=50)
    assert len(path) > 0
    assert path[-1].x == 30
    assert path[-1].y == 0
    assert all(isinstance(p, Position) for p in path)


def test_rrt_direct_obstacle_avoidance():
    # Target directly on the X axis, blocked by a wall at x=25
    wall = (20.0, -20.0, 10.0, 40.0)
    path = rrt(0.0, 0.0, 60.0, 0.0, [wall], step_size=15.0, max_iter=300)

    assert len(path) > 0
    assert path[-1].x == 60
    assert path[-1].y == 0
    # Trajectory points should deviate outside the obstacle boundary
    deviated = any(p.y > 20 or p.y < -20 for p in path)
    assert deviated is True


def test_rrt_direct_unreachable_returns_empty():
    # Impenetrable enclosure around the target
    box = (-50.0, -50.0, 200.0, 200.0)
    path = rrt(0.0, 0.0, 100.0, 0.0, [box], step_size=10.0, max_iter=10)
    assert path == []


def test_rrt_direct_zero_max_iter():
    path = rrt(0.0, 0.0, 100.0, 0.0, [], step_size=10.0, max_iter=0)
    assert path == []


def test_planner_plan_clear_path():
    start = Position(0, 0)
    target = Position(30, 0)
    planner = Planner(start=start, target=target, obstacles=[], step_size=15.0, max_iter=50)

    path = planner.plan()
    assert len(path) > 0
    assert path[-1].x == 30
    assert path[-1].y == 0
    assert all(isinstance(p, Position) for p in path)


def test_planner_plan_unreachable_returns_empty():
    start = Position(0, 0)
    target = Position(100, 0)
    wall = (-50.0, -50.0, 200.0, 200.0)
    planner = Planner(start=start, target=target, obstacles=[wall], step_size=10.0, max_iter=10)

    path = planner.plan()
    assert path == []


def test_planner_delegates_to_rrt():
    start = Position(10, 20)
    target = Position(100, 200)
    obstacles = [(30.0, 40.0, 10.0, 10.0)]

    with patch("app.game.logic.modules.paths.plan.rrt", return_value=[target]) as mock_rrt:
        planner = Planner(start=start, target=target, obstacles=obstacles, step_size=20.0, max_iter=150)
        result = planner.plan()

        mock_rrt.assert_called_once_with(10.0, 20.0, 100.0, 200.0, obstacles, 20.0, 150)
        assert result == [target]