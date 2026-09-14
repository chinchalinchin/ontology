"""
# Ontology: tests.unit.test_app_game_logic_mechanics_intentional_navigation
"""
from collections import deque
from unittest.mock import MagicMock, patch

import pytest
from app.config.enums import Goals, Intentions
import app.config.settings as settings
from app.game.logic.mechanics.intentional.navigation import NavigationMechanics
from app.models.state import Goal, DevicePayload
from libs.core.models import Position, Boundary, Dimensions


# ---------------------------------------------------------------------------
# ANCHOR & OBSTACLE TESTS
# ---------------------------------------------------------------------------

def test_navigation_anchor_with_hitbox(mock_sprite_with_hitbox):
    # Position: (175, 200), Hitbox: pos=(21, 23), dim=(22, 21)
    # Footprint anchor: x = 175 + 21 + 22 // 2 = 207, y = 200 + 23 + 21 // 2 = 233
    anchor = NavigationMechanics.anchor(mock_sprite_with_hitbox)
    assert anchor.x == 207
    assert anchor.y == 233


def test_navigation_anchor_fallback_dimensions(mock_crate):
    # Position: (10, 10), Dimensions: (32, 32), default hitbox generated matching dimensions
    anchor = NavigationMechanics.anchor(mock_crate)
    assert anchor.x == 10 + 32 // 2
    assert anchor.y == 10 + 32 // 2


def test_navigation_obstacles_multi_hitbox(mock_board, mock_multi_hitbox_asset):
    mock_board.add([mock_multi_hitbox_asset])
    obs = NavigationMechanics.obstacles(layer="0", board=mock_board, exclude=[])

    # Position: (250, 250)
    # Hitbox 1: (178, 102, 25, 12) -> (428.0, 352.0, 25.0, 12.0)
    # Hitbox 2: (17, 102, 25, 12)  -> (267.0, 352.0, 25.0, 12.0)
    # Hitbox 3: (5, 39, 203, 63)   -> (255.0, 289.0, 203.0, 63.0)
    assert (428.0, 352.0, 25.0, 12.0) in obs
    assert (267.0, 352.0, 25.0, 12.0) in obs
    assert (255.0, 289.0, 203.0, 63.0) in obs


def test_navigation_obstacles_offset_hitbox(mock_board, mock_offset_hitbox_asset):
    mock_board.add([mock_offset_hitbox_asset])
    obs = NavigationMechanics.obstacles(layer="brick-house-compose-layer", board=mock_board, exclude=[])

    # Position: (150, 150), Hitbox: (6, 17, 116, 54) -> (156.0, 167.0, 116.0, 54.0)
    assert (156.0, 167.0, 116.0, 54.0) in obs


def test_navigation_obstacles_exclusion_and_perimeters(mock_board, mock_offset_hitbox_asset):
    mock_board.add([mock_offset_hitbox_asset])
    mock_board.perimeters["brick-house-compose-layer"] = [
        Boundary(Position(0, 0), Dimensions(10, 20))
    ]

    obs = NavigationMechanics.obstacles(
        layer="brick-house-compose-layer",
        board=mock_board,
        exclude=[mock_offset_hitbox_asset.name]
    )

    assert (156.0, 167.0, 116.0, 54.0) not in obs
    assert (0.0, 0.0, 10.0, 20.0) in obs


# ---------------------------------------------------------------------------
# STATE & TARGET ANCHOR TESTS
# ---------------------------------------------------------------------------

def test_navigation_navigating(mock_sprite_with_hitbox):
    sprite = mock_sprite_with_hitbox
    sprite.state.goal = Goal(name="target", category=Goals.TARGET.value)

    sprite.state.intention = Intentions.FIND
    assert NavigationMechanics.navigating(sprite) is True

    sprite.state.intention = Intentions.HUNT
    assert NavigationMechanics.navigating(sprite) is True

    sprite.state.intention = Intentions.WANDER
    assert NavigationMechanics.navigating(sprite) is True

    sprite.state.intention = Intentions.IDLE
    assert NavigationMechanics.navigating(sprite) is False

    sprite.state.intention = Intentions.ATTACK
    assert NavigationMechanics.navigating(sprite) is False

    sprite.state.goal = None
    sprite.state.intention = Intentions.FIND
    assert NavigationMechanics.navigating(sprite) is False


def test_navigation_clear(mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()

    sprite = mock_sprite_with_hitbox
    sprite.state.trajectory.target = Position(10, 10)
    sprite.state.trajectory.vertices = [Position(10, 10), Position(20, 20)]
    sprite.state.trajectory.stalled = True

    mechanic._clear(sprite)

    assert sprite.state.trajectory.target is None
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.stalled is False


def test_navigation_target_same_layer_asset(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    player = mock_board.player()
    mock_board.relayer(player, mock_sprite_with_hitbox.state.layer)
    player.state.position = Position(300, 300)

    mock_sprite_with_hitbox.state.goal = Goal(
        name=player.name,
        category=Goals.TARGET.value,
        layer=player.state.layer,
        position=Position(300, 300)
    )

    target_anchor = mechanic._target(mock_sprite_with_hitbox, mock_board)
    expected_anchor = NavigationMechanics.anchor(player)

    assert target_anchor.x == expected_anchor.x
    assert target_anchor.y == expected_anchor.y


def test_navigation_target_coordinate_displacement(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.goal = Goal(
        name=None,
        category=Goals.POSITION.value,
        position=Position(50, 50)
    )

    anchor = NavigationMechanics.anchor(sprite)
    offset_x = anchor.x - sprite.state.position.x
    offset_y = anchor.y - sprite.state.position.y

    target_anchor = mechanic._target(sprite, mock_board)
    assert target_anchor.x == 50 + offset_x
    assert target_anchor.y == 50 + offset_y


# ---------------------------------------------------------------------------
# TRAJECTORY PLANNING & PROGRESSION TESTS
# ---------------------------------------------------------------------------

def test_navigation_clear_line_of_sight(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.goal = Goal(
        name="open-space",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(190, 200)
    )

    with patch("libs.core.math.geometry.los", return_value=True):
        mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.target == sprite.state.goal.position
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.stalled is False
    assert sprite.state.trajectory.cooldown == 0


def test_navigation_occluded_los_generates_waypoints(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.goal = Goal(
        name="behind-wall",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 300)
    )

    anchor = NavigationMechanics.anchor(sprite)
    offset_x = anchor.x - sprite.state.position.x
    offset_y = anchor.y - sprite.state.position.y

    mock_waypoints = [Position(210, 210), Position(250, 250)]

    with patch("libs.core.math.geometry.los", return_value=False), \
         patch("app.game.logic.modules.paths.plan.Planner.plan", return_value=mock_waypoints):
        mechanic._navigate(sprite, mock_board)

    # Coordinates in trajectory must subtract sensory anchor displacement
    expected_v0 = Position(210 - offset_x, 210 - offset_y)
    expected_v1 = Position(250 - offset_x, 250 - offset_y)

    assert len(sprite.state.trajectory.vertices) == 2
    assert sprite.state.trajectory.vertices[0].x == expected_v0.x
    assert sprite.state.trajectory.vertices[0].y == expected_v0.y
    assert sprite.state.trajectory.vertices[1].x == expected_v1.x
    assert sprite.state.trajectory.vertices[1].y == expected_v1.y
    assert sprite.state.trajectory.target == sprite.state.trajectory.vertices[0]
    assert sprite.state.trajectory.stalled is False


def test_navigation_stalled_path_enters_cooldown(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.goal = Goal(
        name="unreachable",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 300)
    )

    with patch("libs.core.math.geometry.los", return_value=False), \
         patch("app.game.logic.modules.paths.plan.Planner.plan", return_value=[]):
        mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.stalled is True
    assert sprite.state.trajectory.target is None
    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.cooldown == getattr(settings, "PATH_RETRY_INTERVAL", 60)


def test_navigation_cooldown_active_bypasses_planner(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.goal = Goal(
        name="unreachable",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 300)
    )
    sprite.state.trajectory.cooldown = 10

    with patch("libs.core.math.geometry.los", return_value=False), \
         patch("app.game.logic.modules.paths.plan.Planner.plan") as mock_plan:
        mechanic._navigate(sprite, mock_board)

        mock_plan.assert_not_called()
        assert sprite.state.trajectory.cooldown == 9


def test_navigation_waypoint_arrival_advances_queue(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.position = Position(100, 100)
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(200, 200)
    )

    wp1 = Position(100, 100)
    wp2 = Position(150, 150)
    sprite.state.trajectory.vertices = [wp1, wp2]
    sprite.state.trajectory.target = wp1

    # Goal LOS is blocked (False), but LOS to current waypoint is clear (True)
    with patch("libs.core.math.geometry.los", side_effect=[False, True]):
        mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.vertices == [wp2]
    assert sprite.state.trajectory.target == wp2


def test_navigation_waypoint_arrival_final_sets_goal_target(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.position = Position(150, 150)
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(200, 200)
    )

    wp_last = Position(150, 150)
    sprite.state.trajectory.vertices = [wp_last]
    sprite.state.trajectory.target = wp_last

    # Goal LOS is blocked (False), but LOS to final waypoint is clear (True)
    with patch("libs.core.math.geometry.los", side_effect=[False, True]):
        mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.target == sprite.state.goal.position


def test_navigation_waypoint_arrival_final_sets_goal_target(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.position = Position(150, 150)
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(200, 200)
    )

    wp_last = Position(150, 150)
    sprite.state.trajectory.vertices = [wp_last]
    sprite.state.trajectory.target = wp_last

    # Goal LOS is blocked (False), but LOS to final waypoint is clear (True)
    with patch("libs.core.math.geometry.los", side_effect=[False, True]):
        mechanic._navigate(sprite, mock_board)

    assert sprite.state.trajectory.vertices == []
    assert sprite.state.trajectory.target == sprite.state.goal.position
    

def test_navigation_dynamic_replan_when_waypoint_blocked(mock_board, mock_sprite_with_hitbox):
    mechanic = NavigationMechanics()
    sprite = mock_sprite_with_hitbox
    sprite.state.goal = Goal(
        name="destination",
        category=Goals.POSITION.value,
        layer=sprite.state.layer,
        position=Position(300, 300)
    )

    old_wp = Position(200, 200)
    sprite.state.trajectory.vertices = [old_wp]
    sprite.state.trajectory.target = old_wp

    new_wp = Position(220, 220)

    # LOS to goal is False, and LOS to immediate waypoint is also False (occluded by dynamic crate)
    with patch("libs.core.math.geometry.los", side_effect=[False, False]), \
         patch("app.game.logic.modules.paths.plan.Planner.plan", return_value=[new_wp]):
        mechanic._navigate(sprite, mock_board)

    anchor = NavigationMechanics.anchor(sprite)
    offset_x = anchor.x - sprite.state.position.x
    offset_y = anchor.y - sprite.state.position.y

    assert len(sprite.state.trajectory.vertices) == 1
    assert sprite.state.trajectory.vertices[0].x == new_wp.x - offset_x
    assert sprite.state.trajectory.vertices[0].y == new_wp.y - offset_y


def test_navigation_update_processes_sprites_skips_player(mock_board):
    mechanic = NavigationMechanics()
    player = mock_board.player()

    sprite1 = mock_board.instances("sprites")[0]
    sprite1.state.goal = Goal(name="target1", category=Goals.POSITION.value, position=Position(100, 100))
    sprite1.state.intention = Intentions.FIND

    with patch.object(mechanic, "_navigate") as mock_nav:
        mechanic.update(
            board=mock_board,
            delta=1.0 / 60.0,
            bus=deque(),
            payload=MagicMock(spec=DevicePayload)
        )

        # Verified _navigate called for sprite but not player
        nav_targets = [call.args[0] for call in mock_nav.call_args_list]
        assert sprite1 in nav_targets
        assert player not in nav_targets