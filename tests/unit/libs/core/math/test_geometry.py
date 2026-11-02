"""
@domain.test
@test.unit
@app.library
@workflow.collisions
@workflow.navigation

# Ontology: Tests - tests.unit.libs.core.math.test_geometry

Unit tests for Geometry Cython Library.
"""
# External Libraries
import pytest

# Cython Libraries
from libs.core.models import (
    Position,
    Dimensions,
    Hitbox,
)
from libs.core.math import geometry

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_library,
    pytest.mark.workflow_collisions,
    pytest.mark.workflow_navigation,
]

# -----------------------------------------------------

# ----------------------------------------------------------------------------------------
# BASIC GEOMETRY TESTS
# ----------------------------------------------------------------------------------------


def test_geometry_intersects():
    pos1 = Position(0, 0)
    dim1 = Dimensions(32, 32)
    hb1 = [Hitbox(Position(0, 0), Dimensions(32, 32))]

    pos2 = Position(16, 16)
    dim2 = Dimensions(32, 32)
    hb2 = [Hitbox(Position(0, 0), Dimensions(32, 32))]

    result = geometry.intersects(pos1, dim1, hb1, pos2, dim2, hb2)
    assert result is not None
    assert result == (hb1[0], hb2[0])


def test_geometry_intersects_disjoint_and_empty():
    pos1 = Position(0, 0)
    dim1 = Dimensions(32, 32)
    hb1 = [Hitbox(Position(0, 0), Dimensions(16, 16))]

    pos2 = Position(100, 100)
    dim2 = Dimensions(32, 32)
    hb2 = [Hitbox(Position(0, 0), Dimensions(16, 16))]

    assert geometry.intersects(pos1, dim1, hb1, pos2, dim2, hb2) is None
    assert geometry.intersects(pos1, dim1, [], pos2, dim2, hb2) is None


def test_geometry_onscreen():
    pos = Position(100, 100)
    dim = Dimensions(32, 32)

    p_pos = Position(100, 100)
    p_dim = Dimensions(32, 32)
    screen = Dimensions(480, 480)

    assert geometry.onscreen(pos, dim, p_pos, p_dim, screen) is True

    far_pos = Position(2000, 2000)
    assert geometry.onscreen(far_pos, dim, p_pos, p_dim, screen) is False


def test_geometry_cone():
    assert geometry.cone(0, 0, 0, 10, 100, 0.5, "down") is True
    assert geometry.cone(0, 0, 0, 10, 100, 0.5, "up") is False
    assert geometry.cone(0, 0, -10, 0, 100, 0.5, "left") is True
    assert geometry.cone(0, 0, 10, 0, 100, 0.5, "right") is True
    assert geometry.cone(0, 0, 0, 0, 100, 0.5, "down") is True
    assert geometry.cone(0, 0, 200, 0, 100, 0.5, "right") is False


def test_geometry_nearby():
    assert geometry.nearby(0, 0, 3, 4, 10) is True
    assert geometry.nearby(0, 0, 10, 10, 5) is False


def test_geometry_bounded():
    hb = Hitbox(Position(4, 4), Dimensions(16, 16))
    hit = geometry.bounded(10, 10, [hb], 20, 20, 10, 10)
    assert hit == (hb,)

    miss = geometry.bounded(10, 10, [hb], 100, 100, 10, 10)
    assert miss is None


# ----------------------------------------------------------------------------------------
# RAYCASTING & LINE OF SIGHT TESTS
# ----------------------------------------------------------------------------------------


def test_geometry_punctures_intersection():
    assert geometry.punctures(0.0, 10.0, 100.0, 10.0, 40.0, 0.0, 20.0, 20.0) is True


def test_geometry_punctures_clear():
    assert geometry.punctures(0.0, 50.0, 100.0, 50.0, 40.0, 0.0, 20.0, 20.0) is False


def test_geometry_punctures_origin_inside_box():
    assert geometry.punctures(45.0, 10.0, 100.0, 10.0, 40.0, 0.0, 20.0, 20.0) is True


def test_geometry_punctures_parallel_outside():
    assert geometry.punctures(0.0, -10.0, 100.0, -10.0, 40.0, 0.0, 20.0, 20.0) is False


def test_geometry_los_unobstructed():
    rects = [
        (10.0, 10.0, 20.0, 20.0),
        (50.0, 50.0, 10.0, 10.0),
    ]
    assert geometry.los(0.0, 0.0, 100.0, 0.0, rects) is True


def test_geometry_los_obstructed():
    rects = [
        (40.0, 0.0, 20.0, 20.0),
    ]
    assert geometry.los(0.0, 10.0, 100.0, 10.0, rects) is False


def test_boundary_primitive(mock_boundary):
    """Verify Boundary.primitive unpacks spatial coordinates into a 4-tuple."""
    assert mock_boundary.primitive() == (10, 20, 30, 40)


def test_geometry_raycast_down_hit():
    obstacles = [(10, 100, 32, 32, "crate")]
    dist, hit = geometry.raycast(10, 0, 32, 32, "down", obstacles, 500)

    assert dist == 100
    assert hit == "crate"


def test_geometry_raycast_down_collinear_ignored():
    obstacles = [
        (10, 0, 32, 1, "boundary-top"),
        (10, 120, 32, 32, "crate"),
    ]
    dist, hit = geometry.raycast(10, 0, 32, 32, "down", obstacles, 500)

    assert dist == 120
    assert hit == "crate"


def test_geometry_raycast_up_hit():
    obstacles = [(10, 50, 32, 50, "wall")]
    dist, hit = geometry.raycast(10, 200, 32, 32, "up", obstacles, 500)

    assert dist == 100
    assert hit == "wall"


def test_geometry_raycast_lateral_directions():
    obs_right = [(100, 10, 32, 32, "crate-right")]
    dist_r, hit_r = geometry.raycast(0, 10, 32, 32, "right", obs_right, 500)
    assert dist_r == 100
    assert hit_r == "crate-right"

    obs_left = [(50, 10, 30, 32, "crate-left")]
    dist_l, hit_l = geometry.raycast(200, 10, 32, 32, "left", obs_left, 500)
    assert dist_l == 120
    assert hit_l == "crate-left"


def test_geometry_raycast_miss():
    obstacles = [(100, 100, 32, 32, "distant-crate")]
    dist, hit = geometry.raycast(0, 0, 32, 32, "down", obstacles, 300)

    assert dist == 300
    assert hit is None


# ---------------------------------------------------------------------


def test_geometry_contours_directed():
    rects = [(0, 0, 64, 64)]
    contours = geometry.contours(rects)

    assert len(contours) == 4
    orientations = {c[4] for c in contours}
    assert orientations == {"up", "down", "left", "right"}

    for x, y, w, l, orientation in contours:
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(w, int)
        assert isinstance(l, int)
        assert isinstance(orientation, str)


def test_geometry_contours_overlapping_rects():
    rects = [
        (0, 0, 64, 64),
        (32, 0, 96, 64),
    ]
    contours = geometry.contours(rects)
    assert (0, 0, 96, 1, "up") in contours
    assert (0, 64, 96, 1, "down") in contours
    assert (0, 0, 1, 64, "left") in contours
    assert (96, 0, 1, 64, "right") in contours


# ----------------------------------------------------------------------------------------
# POINT CONTAINMENT & BATCH OCCLUSION TESTS
# ----------------------------------------------------------------------------------------


def test_geometry_inside_point_in_aabbs():
    boxes = [
        (0, 0, 32, 32),
        (100, 100, 150, 150),
    ]
    assert geometry.inside(10, 10, boxes) is True
    assert geometry.inside(0, 0, boxes) is True
    assert geometry.inside(120, 130, boxes) is True

    assert geometry.inside(32, 10, boxes) is False
    assert geometry.inside(10, 32, boxes) is False
    assert geometry.inside(50, 50, boxes) is False


def test_geometry_inside_empty_list():
    assert geometry.inside(10, 10, []) is False


def test_geometry_occluded_batch_overlap():
    obstacles = [
        (0, 0, 32, 32),
        (100, 100, 64, 64),
    ]
    assert geometry.occluded(16, 16, 32, 32, obstacles) is True
    assert geometry.occluded(90, 90, 20, 20, obstacles) is True

    assert geometry.occluded(40, 40, 20, 20, obstacles) is False
    assert geometry.occluded(200, 200, 32, 32, obstacles) is False


def test_geometry_occluded_empty_list():
    assert geometry.occluded(0, 0, 32, 32, []) is False