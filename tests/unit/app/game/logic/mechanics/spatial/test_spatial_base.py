"""
# Ontology: tests.unit.app.game.logic.mechanics.spatial.test_spatial_base
"""
# External Libraries
import pytest

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
)


@pytest.mark.physics
def test_spatial_mechanic_center(mock_collision_mechanics):
    pos = Position(10, 10)
    dim = Dimensions(32, 64)
    cx, cy = mock_collision_mechanics.center(pos, dim)

    assert cx == 26.0
    assert cy == 42.0


@pytest.mark.physics
@pytest.mark.collisions
def test_spatial_mechanic_collisions(mock_collision_mechanics, mock_crate, mock_crate_alt, mock_strut):
    """
    Verifies Space broad-phase hashing and narrow-phase filtering with real fixtures.
    """
    mock_crate.state.position = Position(10, 10)
    mock_crate_alt.state.position = Position(20, 20)
    mock_strut.state.position = Position(200, 200)

    pairs = mock_collision_mechanics.collisions([mock_crate, mock_crate_alt, mock_strut])

    assert len(pairs) == 1
    assert (mock_crate, mock_crate_alt) in pairs or (mock_crate_alt, mock_crate) in pairs
    assert (mock_crate, mock_strut) not in pairs


@pytest.mark.physics
@pytest.mark.collisions
def test_spatial_mechanic_collisions_elevation_filtering(mock_collision_mechanics, mock_crate, mock_crate_alt):
    """
    Verifies SpatialMechanic.collisions filters out entities that have no hitboxes on the queried elevation.
    """
    mock_crate.elevation = 0
    mock_crate.state.position = Position(10, 10)

    mock_crate_alt.elevation = 1
    mock_crate_alt.state.position = Position(10, 10)

    assert mock_collision_mechanics.collisions([mock_crate, mock_crate_alt], elevation=0) == []
    assert mock_collision_mechanics.collisions([mock_crate, mock_crate_alt], elevation=1) == []


@pytest.mark.physics
@pytest.mark.collisions
def test_spatial_mechanic_intersections(mock_collision_mechanics, mock_crate, mock_chest):
    """
    Verifies virtual full-dimension hitbox generation for post-separation interaction checks.
    """
    mock_crate.state.position = Position(10, 10)
    mock_chest.state.position = Position(20, 20)

    pairs = mock_collision_mechanics.intersections([mock_crate, mock_chest])

    assert len(pairs) == 1
    assert (mock_crate, mock_chest) in pairs or (mock_chest, mock_crate) in pairs


@pytest.mark.physics
@pytest.mark.collisions
def test_spatial_mechanic_proximities(mock_collision_mechanics, mock_sprite, mock_sprite_alt):
    """
    Verifies virtual action-radius padded hitbox intersections for separated entities.
    """
    # Separated by 70px horizontally; each 64x64 sprite has action.radius = 25 (padded width = 114)
    mock_sprite.state.position = Position(10, 10)
    mock_sprite_alt.state.position = Position(80, 10)

    pairs = mock_collision_mechanics.proximities([mock_sprite, mock_sprite_alt])

    assert len(pairs) == 1
    assert (mock_sprite, mock_sprite_alt) in pairs or (mock_sprite_alt, mock_sprite) in pairs


@pytest.mark.physics
@pytest.mark.collisions
def test_spatial_mechanic_constrain_elevation_filtering(mock_collision_mechanics, mock_crate, mock_boundary):
    """
    Verifies SpatialMechanic.constrain pairs dynamic assets with boundaries only on active hitbox elevations.
    """
    mock_crate.elevation = 0
    mock_crate.state.position = Position(10, 0)

    pairs_e0 = mock_collision_mechanics.constrain([mock_crate], [mock_boundary], elevation=0)
    pairs_e1 = mock_collision_mechanics.constrain([mock_crate], [mock_boundary], elevation=1)

    assert pairs_e0 == [(mock_crate, mock_boundary)]
    assert pairs_e1 == []