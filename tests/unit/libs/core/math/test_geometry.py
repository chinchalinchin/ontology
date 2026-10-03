"""
# Ontology: tests.unit.libs.core.math.test_geometry
"""
# External Libraries
import pytest

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions, 
    Hitbox
)
from libs.core.math import geometry

# ----------------------------------------------------------------------------------------
# BASIC GEOMETRY TESTS
# ----------------------------------------------------------------------------------------

def test_geometry_intersects():
    pos1 = Position(0, 0)
    dim1 = Dimensions(32, 32)
    hb1 = [Hitbox(Position(0,0), Dimensions(32, 32))]
    
    pos2 = Position(16, 16)
    dim2 = Dimensions(32, 32)
    hb2 = [Hitbox(Position(0,0), Dimensions(32, 32))]
    
    # Narrow-phase AABB positive
    result = geometry.intersects(pos1, dim1, hb1, pos2, dim2, hb2)
    assert result is not None
    assert result == (hb1[0], hb2[0])


def test_geometry_onscreen():
    pos = Position(100, 100)
    dim = Dimensions(32, 32)
    
    # Camera centered safely within screen bounds 
    p_pos = Position(100, 100)
    p_dim = Dimensions(32, 32)
    screen = Dimensions(480, 480)
    
    assert geometry.onscreen(pos, dim, p_pos, p_dim, screen) is True


def test_geometry_cone():
    # Downward check (dy=10) well within radius, cos(120/2) -> 0.5 limit
    assert geometry.cone(0, 0, 0, 10, 100, 0.5, "down") is True
    # Opposite direction check (dy=10 but facing up), should fail
    assert geometry.cone(0, 0, 0, 10, 100, 0.5, "up") is False


def test_geometry_nearby():
    # Distance of 5 is strictly less than radius of 10
    assert geometry.nearby(0, 0, 3, 4, 10) is True
    assert geometry.nearby(0, 0, 10, 10, 5) is False


# ----------------------------------------------------------------------------------------
# RAYCASTING & LINE OF SIGHT TESTS
# ----------------------------------------------------------------------------------------

def test_geometry_punctures_intersection():
    # Segment from (0, 10) to (100, 10) through box (40, 0, 20, 20)
    assert geometry.punctures(0.0, 10.0, 100.0, 10.0, 40.0, 0.0, 20.0, 20.0) is True


def test_geometry_punctures_clear():
    # Segment passes safely above the bounding box
    assert geometry.punctures(0.0, 50.0, 100.0, 50.0, 40.0, 0.0, 20.0, 20.0) is False


def test_geometry_punctures_origin_inside_box():
    # Ray originating inside the obstacle
    assert geometry.punctures(45.0, 10.0, 100.0, 10.0, 40.0, 0.0, 20.0, 20.0) is True


def test_geometry_punctures_parallel_outside():
    # Segment parallel to X axis outside Y boundaries
    assert geometry.punctures(0.0, -10.0, 100.0, -10.0, 40.0, 0.0, 20.0, 20.0) is False


def test_geometry_los_unobstructed():
    rects = [
        (10.0, 10.0, 20.0, 20.0),
        (50.0, 50.0, 10.0, 10.0)
    ]
    # Trajectory clears all bounding boxes
    assert geometry.los(0.0, 0.0, 100.0, 0.0, rects) is True


def test_geometry_los_obstructed():
    rects = [
        (40.0, 0.0, 20.0, 20.0)
    ]
    # Trajectory intersects the middle obstacle
    assert geometry.los(0.0, 10.0, 100.0, 10.0, rects) is False


def test_boundary_primitive(mock_boundary):
    """Verify Boundary.primitive unpacks spatial coordinates into a 4-tuple."""
    assert mock_boundary.primitive() == (10, 20, 30, 40)


def test_geometry_raycast_down_hit():
    """
    Verify downward raycast strikes obstacle within corridor cross-section.
    """
    obstacles = [(10, 100, 32, 32, "crate")]
    dist, hit = geometry.raycast(10, 0, 32, 32, "down", obstacles, 500)

    assert dist == 100
    assert hit == "crate"


def test_geometry_raycast_down_collinear_ignored():
    """
    Verify raycast ignores occluders sharing emitter origin Y-coordinate.
    """
    obstacles = [
        (10, 0, 32, 1, "boundary-top"),
        (10, 120, 32, 32, "crate")
    ]
    dist, hit = geometry.raycast(10, 0, 32, 32, "down", obstacles, 500)

    assert dist == 120
    assert hit == "crate"


def test_geometry_raycast_up_hit():
    """
    Verify upward raycast detects distal bottom edge of obstacle.
    """
    obstacles = [(10, 50, 32, 50, "wall")]  # Bottom edge at 50 + 50 = 100
    dist, hit = geometry.raycast(10, 200, 32, 32, "up", obstacles, 500)

    assert dist == 100
    assert hit == "wall"


def test_geometry_raycast_lateral_directions():
    """
    Verify right and left raycasts calculate accurate X-axis displacement.
    """
    # Right
    obs_right = [(100, 10, 32, 32, "crate-right")]
    dist_r, hit_r = geometry.raycast(0, 10, 32, 32, "right", obs_right, 500)
    assert dist_r == 100
    assert hit_r == "crate-right"

    # Left (right edge of obstacle at 50 + 30 = 80; emitter at 200 -> dist 120)
    obs_left = [(50, 10, 30, 32, "crate-left")]
    dist_l, hit_l = geometry.raycast(200, 10, 32, 32, "left", obs_left, 500)
    assert dist_l == 120
    assert hit_l == "crate-left"


def test_geometry_raycast_miss():
    """
    Verify raycast returns max_dist and None when path is clear.
    """
    obstacles = [(100, 100, 32, 32, "distant-crate")]
    dist, hit = geometry.raycast(0, 0, 32, 32, "down", obstacles, 300)

    assert dist == 300
    assert hit is None

# ---------------------------------------------------------------------

def test_geometry_contours_directed():
    """
    Verifies that the Cython sweep-line contour algorithm derives directed
    5-tuples (x, y, w, l, orientation) preserving outward edge normals.
    """
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

# ----------------------------------------------------------------------------------------
# POINT CONTAINMENT & BATCH OCCLUSION TESTS
# ----------------------------------------------------------------------------------------

def test_geometry_inside_point_in_aabbs():
    boxes = [
        (0, 0, 32, 32),
        (100, 100, 150, 150)
    ]
    # Points inside intervals
    assert geometry.inside(10, 10, boxes) is True
    assert geometry.inside(0, 0, boxes) is True
    assert geometry.inside(120, 130, boxes) is True

    # Boundary edge conditions (half-open: [min, max))
    assert geometry.inside(32, 10, boxes) is False
    assert geometry.inside(10, 32, boxes) is False

    # Point outside all boxes
    assert geometry.inside(50, 50, boxes) is False


def test_geometry_inside_empty_list():
    assert geometry.inside(10, 10, []) is False


def test_geometry_occluded_batch_overlap():
    obstacles = [
        (0, 0, 32, 32),
        (100, 100, 64, 64)
    ]
    # Overlapping query AABB
    assert geometry.occluded(16, 16, 32, 32, obstacles) is True
    assert geometry.occluded(90, 90, 20, 20, obstacles) is True

    # Clear query AABB
    assert geometry.occluded(40, 40, 20, 20, obstacles) is False
    assert geometry.occluded(200, 200, 32, 32, obstacles) is False


def test_geometry_occluded_empty_list():
    assert geometry.occluded(0, 0, 32, 32, []) is False