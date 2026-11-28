"""
@domain.test
@test.unit
@app.mechanic
@physics.motion
@physics.space
@workflow.collisions
@workflow.combat
@workflow.interactions

# Ontology: Tests - tests.unit.app.game.logic.mechanics.spatial.test_spatial

Unit test for the SpatialMechanics base class.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Buildings,
    Mechanics,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.physics_motion,
    pytest.mark.physics_space,
]

# ---------------------------------------------------------------------------


def test_spatial_mechanic_center(mock_mechanic):
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    pos = Position(10, 10)
    dim = Dimensions(32, 64)
    cx, cy = mechanics.center(pos, dim)

    assert cx == 26.0
    assert cy == 42.0


@pytest.mark.app_asset
@pytest.mark.workflow_collisions
@pytest.mark.workflow_combat
def test_spatial_mechanic_collisions(mock_mechanic, mock_asset):
    """
    Verifies Space broad-phase hashing and narrow-phase filtering with real fixtures.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate_a = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate_b = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    strut = mock_asset(
        AssetCategories.CRAFTS.value,
        AssetInstances.STRUTS.value,
    )

    crate_a.state.position = Position(10, 10)
    crate_b.state.position = Position(20, 20)
    strut.state.position = Position(200, 200)

    pairs = mechanics.collisions([crate_a, crate_b, strut])

    assert len(pairs) == 1
    assert (crate_a, crate_b) in pairs or (crate_b, crate_a) in pairs
    assert (crate_a, strut) not in pairs


@pytest.mark.app_asset
@pytest.mark.workflow_collisions
def test_spatial_mechanic_collisions_elevation_filtering(mock_mechanic, mock_asset):
    """
    Verifies SpatialMechanic.collisions filters out entities that have no hitboxes on the queried elevation.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate_a = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate_b = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )

    crate_a.elevation = 0
    crate_a.state.position = Position(10, 10)

    crate_b.elevation = 1
    crate_b.state.position = Position(10, 10)

    assert mechanics.collisions([crate_a, crate_b], elevation=0) == []
    assert mechanics.collisions([crate_a, crate_b], elevation=1) == []


@pytest.mark.app_asset
@pytest.mark.workflow_interactions
def test_spatial_mechanic_intersections(mock_mechanic, mock_asset):
    """
    Verifies virtual full-dimension hitbox generation for post-separation interaction checks.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    chest = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CHESTS.value,
    )

    crate.state.position = Position(10, 10)
    chest.state.position = Position(20, 20)

    pairs = mechanics.intersections([crate, chest])

    assert len(pairs) == 1
    assert (crate, chest) in pairs or (chest, crate) in pairs


@pytest.mark.app_asset
@pytest.mark.workflow_interactions
def test_spatial_mechanic_proximities(mock_mechanic, mock_asset):
    """
    Verifies virtual action-radius padded hitbox intersections for separated entities.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    sprite_a = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite_b = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )

    # Separated by 70px horizontally; each 64x64 sprite has action.radius = 25 (padded width = 114)
    sprite_a.state.position = Position(10, 10)
    sprite_b.state.position = Position(80, 10)

    pairs = mechanics.proximities([sprite_a, sprite_b])

    assert len(pairs) == 1
    assert (sprite_a, sprite_b) in pairs or (sprite_b, sprite_a) in pairs


@pytest.mark.app_component
@pytest.mark.workflow_collisions
def test_spatial_mechanic_constrain_elevation_filtering(mock_mechanic, mock_board):
    """
    Verifies SpatialMechanic.constrain pairs dynamic assets with boundaries only on active hitbox elevations.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    boundary = mock_board.perimeters[crate.state.layer][0][0]

    crate.elevation = 0
    hb = crate.hitboxes[0]
    crate.state.position = Position(
        boundary.position.x - hb.position.x,
        boundary.position.y - hb.position.y,
    )

    pairs_e0 = mechanics.constrain([crate], [boundary], elevation=0)
    pairs_e1 = mechanics.constrain([crate], [boundary], elevation=1)

    assert pairs_e0 == [(crate, boundary)]
    assert pairs_e1 == []

@pytest.mark.app_asset
@pytest.mark.workflow_interactions
def test_spatial_mechanic_intersections_motive_padding(mock_mechanic, mock_asset):
    """
    Verifies SpatialMechanic.intersections applies a 2px contact margin to Sprites/Players
    so flush post-collision separation still registers an intersection.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    chest = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CHESTS.value,
    )

    hb_s = sprite.hitboxes[0]
    hb_c = chest.hitboxes[0]

    # Position chest 1px flush outside the right edge of the sprite's physical hitbox
    sprite.state.position = Position(10, 10)
    chest.state.position = Position(
        10 + hb_s.position.x + hb_s.dimensions.w + 1 - hb_c.position.x,
        10 + hb_s.position.y - hb_c.position.y,
    )

    assert mechanics.collisions([sprite, chest]) == []
    assert len(mechanics.intersections([sprite, chest])) == 1


@pytest.mark.app_asset
@pytest.mark.workflow_collisions
@pytest.mark.workflow_interactions
def test_spatial_mechanic_empty_and_parameterless_guards(mock_mechanic, mock_asset, mock_boundary):
    """
    Verifies empty collection guards and safe skipping of parameterless assets in proximities.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )

    assert mechanics.collisions([]) == []
    assert mechanics.intersections([]) == []
    assert mechanics.proximities([]) == []
    assert mechanics.proximities([crate]) == []
    assert mechanics.constrain([], [mock_boundary]) == []
    assert mechanics.constrain([crate], []) == []

@pytest.mark.app_asset
@pytest.mark.workflow_collisions
@pytest.mark.workflow_interactions
def test_spatial_mechanic_proximities_cross_cell_boundary(mock_mechanic, mock_asset):
    """
    Verifies SpatialMechanic.proximities hashes the action-radius padded hitbox bounds
    into Space so entities in non-overlapping base cells still pair across cell boundaries.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    sprite_a = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite_b = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )

    # Base 64x64 footprints occupy cx in {0, 1} ([50, 114]) and cx in {2, 3} ([130, 194]),
    # while 25px action-padded hitboxes span [25, 139] and [105, 219] (overlapping in cx=2).
    sprite_a.state.position = Position(50, 10)
    sprite_b.state.position = Position(130, 10)

    pairs = mechanics.proximities([sprite_a, sprite_b])

    assert len(pairs) == 1
    assert (sprite_a, sprite_b) in pairs or (sprite_b, sprite_a) in pairs

@pytest.mark.app_asset
@pytest.mark.workflow_interactions
def test_spatial_mechanic_intersections_elevation_isolation(mock_mechanic, mock_asset):
    """
    Verifies SpatialMechanic.intersections isolates assets occupying distinct elevation tiers.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    crate_a = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate_b = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )

    crate_a.elevation = 0
    crate_a.state.position = Position(10, 10)
    crate_b.elevation = 1
    crate_b.state.position = Position(10, 10)

    assert mechanics.intersections([crate_a, crate_b]) == []


@pytest.mark.app_asset
@pytest.mark.workflow_interactions
def test_spatial_mechanic_proximities_elevation_isolation(mock_mechanic, mock_asset):
    """
    Verifies SpatialMechanic.proximities filters out candidate pairs on distinct elevation tiers.
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    sprite_a = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    sprite_b = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )

    sprite_a.elevation = 0
    sprite_a.state.position = Position(10, 10)
    sprite_b.elevation = 1
    sprite_b.state.position = Position(20, 10)

    assert mechanics.proximities([sprite_a, sprite_b]) == []


@pytest.mark.app_asset
@pytest.mark.workflow_interactions
def test_spatial_mechanic_intersections_skips_empty_hitbox_assets(mock_mechanic, mock_asset):
    """
    Verifies SpatialMechanic.intersections excludes passable assets whose HitboxSchema
    emits empty elevations and hitboxes (e.g., floor Struts).
    """
    mechanics = mock_mechanic(Mechanics.COLLISION.value)
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    strut = mock_asset(
        AssetCategories.CRAFTS.value,
        AssetInstances.STRUTS.value,
    )

    strut.state.blueprint = Buildings.FLOORS.value
    sprite.state.position = Position(50, 50)
    strut.state.position = Position(50, 50)

    assert mechanics.intersections([sprite, strut]) == []