"""
# Ontology: tests.unit.test_app_game_logic_mechanics_modules_paths.py
"""
import pytest
from unittest.mock import patch

from libs.core.models import Position
from app.game.logic.mechanics.modules.paths.plan import Node, Planner


def test_node_initialization():
    node = Node(10.5, 20.25)
    assert node.x == 10.5
    assert node.y == 20.25
    assert node.parent is None


def test_planner_initialization_and_bounds():
    start = Position(x=10, y=10)
    target = Position(x=50, y=60)
    obstacles = [(20.0, 20.0, 10.0, 10.0)]
    step_size = 16.0

    planner = Planner(start=start, target=target, obstacles=obstacles, step_size=step_size, max_iter=100)

    assert planner.start.x == 10.0
    assert planner.start.y == 10.0
    assert planner.target.x == 50.0
    assert planner.target.y == 60.0
    assert planner.step_size == 16.0
    assert planner.max_iter == 100
    assert len(planner.node_list) == 1

    expected_pad_w = abs(50 - 10) * 0.2 + 16.0 * 2
    expected_pad_h = abs(60 - 10) * 0.2 + 16.0 * 2
    assert planner.min_x == 10.0 - expected_pad_w
    assert planner.max_x == 50.0 + expected_pad_w
    assert planner.min_y == 10.0 - expected_pad_h
    assert planner.max_y == 60.0 + expected_pad_h


def test_planner_calc_dist():
    n1 = Node(0.0, 0.0)
    n2 = Node(3.0, 4.0)
    assert Planner._calc_dist(n1, n2) == 5.0


def test_planner_get_nearest_node():
    n1 = Node(0.0, 0.0)
    n2 = Node(10.0, 10.0)
    n3 = Node(50.0, 50.0)
    sample = Node(8.0, 9.0)

    planner = Planner(start=Position(0, 0), target=Position(100, 100), obstacles=[])
    nearest = planner._get_nearest_node([n1, n2, n3], sample)
    assert nearest is n2


def test_planner_steer():
    planner = Planner(start=Position(0, 0), target=Position(100, 100), obstacles=[], step_size=10.0)
    from_node = Node(0.0, 0.0)
    to_node = Node(100.0, 0.0)

    steered = planner._steer(from_node, to_node, step_size=10.0)
    assert pytest.approx(steered.x, abs=1e-3) == 10.0
    assert pytest.approx(steered.y, abs=1e-3) == 0.0
    assert steered.parent is from_node


def test_planner_check_collision():
    planner = Planner(start=Position(0, 0), target=Position(100, 100), obstacles=[(40.0, 0.0, 20.0, 20.0)])
    near_node = Node(0.0, 10.0)
    blocked_node = Node(100.0, 10.0)
    clear_node = Node(0.0, 50.0)

    # Bisects obstacle at (40, 0, 20, 20)
    assert planner._check_collision(near_node, blocked_node, planner.obstacles) is False
    # Avoids obstacle
    assert planner._check_collision(near_node, clear_node, planner.obstacles) is True


def test_planner_sample_free_space_goal_bias():
    planner = Planner(start=Position(0, 0), target=Position(100, 100), obstacles=[])
    
    with patch("random.randint", return_value=1):
        sampled = planner._sample_free_space()
        assert sampled.x == 100.0
        assert sampled.y == 100.0

    with patch("random.randint", return_value=50):
        with patch("random.uniform", side_effect=[12.5, 34.5]):
            sampled = planner._sample_free_space()
            assert sampled.x == 12.5
            assert sampled.y == 34.5


def test_planner_plan_clear_path():
    start = Position(0, 0)
    target = Position(30, 0)
    planner = Planner(start=start, target=target, obstacles=[], step_size=15.0, max_iter=50)

    # Goal bias forces direct sampling of target
    with patch("random.randint", return_value=1):
        path = planner.plan()

    assert len(path) > 0
    assert path[-1].x == 30
    assert path[-1].y == 0
    assert all(isinstance(p, Position) for p in path)


def test_planner_plan_unreachable_returns_empty():
    start = Position(0, 0)
    target = Position(100, 0)
    # Complete impenetrable barrier blocking all trajectories
    wall = (-50.0, -50.0, 200.0, 200.0)
    planner = Planner(start=start, target=target, obstacles=[wall], step_size=10.0, max_iter=10)

    path = planner.plan()
    assert path == []