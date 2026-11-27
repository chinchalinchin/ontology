"""
@domain.test
@test.unit
@app.library
@workflow.collisions

# Ontology: Tests - tests.unit.libs.core.test_models

Unit tests for Cython value-model comparison operators, serialization,
and pickle round-trips (Bug B090).
"""
# Standard Libraries
import pickle

# External Libraries
import pytest

# Cython Libraries
from libs.core.models import (
    Boundary,
    Dimensions,
    Hitbox,
    Multiple,
    Position,
    Scale,
    Velocity,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_library,
    pytest.mark.workflow_collisions,
]

# -----------------------------------------------------


def test_position_equality_and_serialization():
    p1 = Position(10, 20)
    p2 = Position(10, 20, rx=0.45, ry=-0.25)
    p3 = Position(10, 21)

    assert p1 == p2
    assert not (p1 != p2)
    assert p1 != p3
    assert not (p1 == p3)
    assert p1 != None  # noqa: E711
    assert p1 != (10, 20)
    assert p1 != Dimensions(10, 20)

    with pytest.raises(TypeError):
        _ = p1 < p3

    restored = pickle.loads(pickle.dumps(p2))
    assert restored == p2
    assert (restored.rx, restored.ry) == (0.45, -0.25)
    assert p2.to_dict() == {"x": 10, "y": 20, "rx": 0.45, "ry": -0.25}


def test_dimensions_equality_and_serialization():
    d1 = Dimensions(32, 64)
    d2 = Dimensions(32, 64)
    d3 = Dimensions(64, 32)

    assert d1 == d2
    assert not (d1 != d2)
    assert d1 != d3
    assert d1 != None  # noqa: E711
    assert d1 != Position(32, 64)

    with pytest.raises(TypeError):
        _ = d1 < d3

    assert pickle.loads(pickle.dumps(d1)) == d1
    assert d1.to_dict() == {"w": 32, "l": 64}


def test_multiple_equality_and_serialization():
    m1 = Multiple(2, 4)
    m2 = Multiple(2, 4)
    m3 = Multiple(2, 5)

    assert m1 == m2
    assert not (m1 != m2)
    assert m1 != m3
    assert m1 != None  # noqa: E711
    assert m1 != Position(2, 4)

    with pytest.raises(TypeError):
        _ = m1 < m3

    assert pickle.loads(pickle.dumps(m1)) == m1
    assert m1.to_dict() == {"nx": 2, "ny": 4}


def test_velocity_equality_and_serialization():
    v1 = Velocity(12.5, -3.25)
    v2 = Velocity(12.5, -3.25)
    v3 = Velocity(12.5, 3.25)

    assert v1 == v2
    assert not (v1 != v2)
    assert v1 != v3
    assert v1 != None  # noqa: E711
    assert v1 != Scale(12.5, -3.25)

    with pytest.raises(TypeError):
        _ = v1 < v3

    assert pickle.loads(pickle.dumps(v1)) == v1
    assert v1.to_dict() == {"vx": 12.5, "vy": -3.25}


def test_scale_equality_and_serialization():
    s1 = Scale(0.25, 0.75)
    s2 = Scale(0.25, 0.75)
    s3 = Scale(0.5, 0.75)

    assert s1 == s2
    assert not (s1 != s2)
    assert s1 != s3
    assert s1 != None  # noqa: E711
    assert s1 != Velocity(0.25, 0.75)

    with pytest.raises(TypeError):
        _ = s1 < s3

    assert pickle.loads(pickle.dumps(s1)) == s1
    assert s1.to_dict() == {"pw": 0.25, "pl": 0.75}


def test_hitbox_equality_none_safety_and_serialization():
    h1 = Hitbox(Position(4, 8), Dimensions(16, 24))
    h2 = Hitbox(Position(4, 8), Dimensions(16, 24))
    h3 = Hitbox(Position(4, 9), Dimensions(16, 24))
    h_empty_a = Hitbox(None, None)
    h_empty_b = Hitbox(None, None)

    assert h1 == h2
    assert not (h1 != h2)
    assert h1 != h3
    assert h1 != h_empty_a
    assert h_empty_a != h1
    assert h_empty_a == h_empty_b
    assert h1 != Boundary(Position(4, 8), Dimensions(16, 24))
    assert h1 != None  # noqa: E711

    with pytest.raises(TypeError):
        _ = h1 < h3

    assert pickle.loads(pickle.dumps(h1)) == h1
    assert h_empty_a.to_dict() == {"position": None, "dimensions": None}


def test_boundary_equality_none_safety_and_primitive():
    b1 = Boundary(Position(10, 20), Dimensions(30, 40))
    b2 = Boundary(Position(10, 20), Dimensions(30, 40))
    b3 = Boundary(Position(10, 20), Dimensions(30, 41))
    b_empty_a = Boundary(None, None)
    b_empty_b = Boundary(None, None)

    assert b1 == b2
    assert not (b1 != b2)
    assert b1 != b3
    assert b1 != b_empty_a
    assert b_empty_a == b_empty_b
    assert b1 != Hitbox(Position(10, 20), Dimensions(30, 40))
    assert b1 != None  # noqa: E711

    with pytest.raises(TypeError):
        _ = b1 < b3

    assert b1.primitive() == (10, 20, 30, 40)
    assert pickle.loads(pickle.dumps(b1)) == b1
    assert b_empty_a.to_dict() == {"position": None, "dimensions": None}