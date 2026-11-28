"""
@domain.test
@test.unit
@app.asset
@asset.hitbox
@workflow.collisions
@workflow.combat

# Ontology: Test - tests.unit.app.assets.test_hitboxes

Unit tests for Asset Hitbox implementations.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Actions,
    AnnualStages,
    AssetCategories,
    AssetInstances,
    Buildings,
    Directions,
    PerennialStages,
    LayerProjections,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position,
)

pytestmark = [
    pytest.mark.app_asset,
    pytest.mark.asset_hitbox,
    pytest.mark.workflow_collisions,
]


@pytest.mark.category_objects
def test_static_hitbox_fallback_on_none(mock_asset):
    """Undeclared hitboxes fall back to full bounding box dimensions."""
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.properties.hitboxes = None

    assert len(crate.hitboxes) == 1
    assert crate.hitboxes[0].position.x == 0
    assert crate.hitboxes[0].position.y == 0
    assert crate.hitboxes[0].dimensions.w == crate.dimensions.w
    assert crate.hitboxes[0].dimensions.l == crate.dimensions.l


@pytest.mark.category_objects
def test_static_hitbox_preserves_explicit_empty_list(mock_asset):
    """Explicit empty list [] preserves passable entity without bounding-box fallback (Bug B014)."""
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.properties.hitboxes = []

    assert crate.hitboxes == []


@pytest.mark.category_objects
def test_static_hitbox_elevation_filtering(mock_asset):
    """StaticHitbox resolves hitboxes at tier 0 and returns empty list on higher tiers."""
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    crate.state.elevation = 0

    assert crate.hitbox.elevations(crate.properties, crate.state) == [0]
    assert len(crate.hitbox.get(crate.properties, crate.state, elevation=0)) == 1
    assert crate.hitbox.get(crate.properties, crate.state, elevation=1) == []


@pytest.mark.category_tiles
def test_no_hitbox_unconditionally_empty(mock_asset):
    """NoHitbox strategy always resolves an empty collision list and no elevation tiers."""
    tile = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.ENVIRON.value,
    )
    assert tile.hitbox.elevations(tile.properties, tile.state) == []
    assert tile.hitboxes == []


@pytest.mark.category_effects
def test_dynamic_hitbox_reads_state_bounds(mock_asset):
    """DynamicHitbox resolves the mutable state hitbox list rather than static properties."""
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    custom_bounds = [Hitbox(Position(0, 0), Dimensions(32, 64))]
    fluid.state.hitboxes = custom_bounds

    assert fluid.hitboxes == custom_bounds


@pytest.mark.category_effects
@pytest.mark.workflow_fluids
def test_substrate_negative_elevation_collapses_to_tier_zero(mock_asset):
    """
    Verifies assets with negative elevations normalize to collision tier 0
    when resolving hitboxes and return [] at elevation >= 1.
    """
    fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    bridge = mock_asset(
        AssetCategories.CRAFTS.value,
        AssetInstances.BRIDGES.value,
    )

    fluid_hb = [Hitbox(Position(0, 0), Dimensions(96, 512))]
    fluid.state.elevation = -3
    fluid.state.hitboxes = fluid_hb

    bridge.state.elevation = -1

    assert fluid.hitbox.elevations(fluid.properties, fluid.state) == [0]
    assert fluid.hitboxes == fluid_hb
    assert fluid.hitbox.get(fluid.properties, fluid.state, elevation=0) == fluid_hb
    assert fluid.hitbox.get(fluid.properties, fluid.state, elevation=1) == []

    assert bridge.hitbox.elevations(bridge.properties, bridge.state) == [0]
    assert len(bridge.hitboxes) > 0
    assert bridge.hitbox.get(bridge.properties, bridge.state, elevation=1) == []


@pytest.mark.category_crafts
@pytest.mark.modality_material
def test_material_hitbox_resolves_by_blueprint_and_elevation(mock_asset):
    """MaterialHitbox resolves hitboxes matching state.blueprint at the deployed elevation."""
    stairs = mock_asset(
        AssetCategories.CRAFTS.value,
        AssetInstances.STAIRS.value,
    )
    stairs.state.elevation = 0

    expected = stairs.properties.hitboxes.get(stairs.state.blueprint, [])
    assert stairs.hitbox.elevations(stairs.properties, stairs.state) == [0]
    assert stairs.hitboxes == expected
    assert stairs.hitbox.get(stairs.properties, stairs.state, elevation=1) == []


@pytest.mark.category_resources
@pytest.mark.workflow_seasons
def test_stage_hitbox_annual_crop_transitions(mock_asset):
    """Verifies annual crop stages transition from passable sprout/growth to solid stalk/bloom."""
    crop = mock_asset(
        AssetCategories.RESOURCES.value,
        AssetInstances.CROPS.value,
        id="maize",
    )

    crop.state.stage = AnnualStages.STALK.value
    stalk_hbs = crop.hitboxes
    assert len(stalk_hbs) == 1
    assert stalk_hbs[0].position.x == 6
    assert stalk_hbs[0].position.y == 10
    assert stalk_hbs[0].dimensions.w == 20
    assert stalk_hbs[0].dimensions.l == 12

    crop.state.stage = AnnualStages.BLOOM.value
    bloom_hbs = crop.hitboxes
    assert len(bloom_hbs) == 1
    assert bloom_hbs[0].position.x == 4
    assert bloom_hbs[0].position.y == 6
    assert bloom_hbs[0].dimensions.w == 24
    assert bloom_hbs[0].dimensions.l == 16

    crop.state.stage = AnnualStages.STUMP.value
    assert crop.hitboxes == []


@pytest.mark.category_resources
@pytest.mark.workflow_seasons
def test_stage_hitbox_perennial_transitions(mock_asset):
    """Verifies adult stage constrains to trunk, sapling is passable, and stump resizes."""
    tree = mock_asset(
        AssetCategories.RESOURCES.value,
        AssetInstances.TREES.value,
        id="deciduous",
    )

    tree.state.stage = PerennialStages.ADULT.value
    hbs = tree.hitboxes
    assert len(hbs) == 1
    assert hbs[0].position.x == 36
    assert hbs[0].position.y == 110
    assert hbs[0].dimensions.w == 22
    assert hbs[0].dimensions.l == 24

    tree.state.stage = PerennialStages.STUMP.value
    stump_hbs = tree.hitboxes
    assert len(stump_hbs) == 1
    assert stump_hbs[0].position.x == 36
    assert stump_hbs[0].position.y == 120
    assert stump_hbs[0].dimensions.w == 18
    assert stump_hbs[0].dimensions.l == 14


@pytest.mark.category_sheets
@pytest.mark.workflow_combat
def test_attack_hitbox_elevations_and_frame_resolution(mock_equipment, mock_asset):
    """Verifies AttackHitbox resolves elevations and frame-keyed weapon hitboxes on matching tiers."""
    sword = mock_equipment.weapons["sword"]
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )

    player.state.elevation = 0
    assert sword.hitbox.elevations(sword.properties, player.state) == [0]

    player.state.elevation = 2
    assert sword.hitbox.elevations(sword.properties, player.state) == [2]

    player.state.elevation = -1
    assert sword.hitbox.elevations(sword.properties, player.state) == [0]

    player.state.elevation = 0
    player.state.animation.action = Actions.SLASH.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 3

    expected = sword.properties.hitboxes["slash-right-3"]
    assert sword.hitbox.get(sword.properties, player.state, elevation=0) == expected
    assert sword.hitbox.get(sword.properties, player.state, elevation=1) == []

    player.state.animation.frame = 0
    assert sword.hitbox.get(sword.properties, player.state, elevation=0) == []


@pytest.mark.category_sheets
@pytest.mark.workflow_combat
def test_attack_hitbox_non_dict_hitboxes_returns_empty(mock_equipment, mock_asset):
    """Verifies AttackHitbox returns an empty list when weapon hitboxes are None."""
    longbow = mock_equipment.weapons["longbow"]
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )

    longbow.properties.hitboxes = None
    player.state.elevation = 0
    player.state.animation.action = Actions.SHOOT.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 9

    assert longbow.hitbox.get(longbow.properties, player.state, elevation=0) == []


@pytest.mark.category_sheets
@pytest.mark.workflow_combat
@pytest.mark.workflow_projectiles
def test_attack_hitbox_ranged_release_frames(mock_equipment, mock_asset):
    """Verifies longbow and crossbow resolve directional release hitboxes strictly on their release frames."""
    longbow = mock_equipment.weapons["longbow"]
    crossbow = mock_equipment.weapons["crossbow"]
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )
    player.state.elevation = 0

    player.state.animation.action = Actions.SHOOT.value
    player.state.animation.frame = 9
    for direction in (
        Directions.UP.value,
        Directions.LEFT.value,
        Directions.DOWN.value,
        Directions.RIGHT.value,
    ):
        player.state.animation.direction = direction
        assert (
            longbow.hitbox.get(longbow.properties, player.state, elevation=0)
            == longbow.properties.hitboxes[f"shoot-{direction}-9"]
        )

    player.state.animation.frame = 8
    assert longbow.hitbox.get(longbow.properties, player.state, elevation=0) == []

    player.state.animation.action = Actions.THRUST.value
    player.state.animation.frame = 5
    for direction in (
        Directions.UP.value,
        Directions.LEFT.value,
        Directions.DOWN.value,
        Directions.RIGHT.value,
    ):
        player.state.animation.direction = direction
        assert (
            crossbow.hitbox.get(crossbow.properties, player.state, elevation=0)
            == crossbow.properties.hitboxes[f"thrust-{direction}-5"]
        )

    player.state.animation.frame = 4
    assert crossbow.hitbox.get(crossbow.properties, player.state, elevation=0) == []


@pytest.mark.category_cursors
@pytest.mark.workflow_projectiles
def test_rotated_hitbox_elevations_and_filtering(mock_asset):
    """Verifies RotatedHitbox elevation clamping and cross-tier isolation."""
    proj = mock_asset(
        AssetCategories.CURSORS.value,
        AssetInstances.PROJECTILES.value,
    )

    proj.state.elevation = 0
    assert proj.hitbox.elevations(proj.properties, proj.state) == [0]
    assert len(proj.hitbox.get(proj.properties, proj.state, elevation=0)) == 1
    assert proj.hitbox.get(proj.properties, proj.state, elevation=1) == []

    proj.state.elevation = 2
    assert proj.hitbox.elevations(proj.properties, proj.state) == [2]
    assert len(proj.hitbox.get(proj.properties, proj.state, elevation=2)) == 1
    assert proj.hitbox.get(proj.properties, proj.state, elevation=0) == []

    proj.state.elevation = -1
    assert proj.hitbox.elevations(proj.properties, proj.state) == [0]


@pytest.mark.category_cursors
@pytest.mark.workflow_projectiles
def test_rotated_hitbox_fallback_on_none_and_empty_list(mock_asset):
    """Verifies None falls back to rotated frame dimensions while [] stays empty."""
    proj = mock_asset(
        AssetCategories.CURSORS.value,
        AssetInstances.PROJECTILES.value,
    )
    proj.state.elevation = 0
    proj.properties.hitboxes = None

    # 16x16 cannonball at 0 degrees
    proj.state.angle = 0
    hbs_0 = proj.hitboxes
    assert len(hbs_0) == 1
    assert (hbs_0[0].position.x, hbs_0[0].position.y) == (0, 0)
    assert (hbs_0[0].dimensions.w, hbs_0[0].dimensions.l) == (16, 16)

    # 16x16 cannonball at 45 degrees -> circumscribed 23x23 centered on (8, 8)
    proj.state.angle = 45
    hbs_45 = proj.hitboxes
    assert len(hbs_45) == 1
    assert (hbs_45[0].position.x, hbs_45[0].position.y) == (-4, -4)
    assert (hbs_45[0].dimensions.w, hbs_45[0].dimensions.l) == (23, 23)

    # Explicit empty list preserves passability
    proj.properties.hitboxes = []
    assert proj.hitboxes == []


@pytest.mark.category_cursors
@pytest.mark.workflow_projectiles
@pytest.mark.parametrize(
    "angle, expected_pos, expected_dim",
    [
        (0, (30, 18), (10, 5)),
        (90, (18, 30), (5, 10)),
        (180, (1, 18), (10, 5)),
        (270, (18, 1), (5, 10)),
        (360, (30, 18), (10, 5)),
        (-90, (18, 1), (5, 10)),
    ],
)
def test_rotated_hitbox_cardinal_projections(
    mock_asset,
    mock_properties,
    angle: int,
    expected_pos: tuple[int, int],
    expected_dim: tuple[int, int],
):
    """Verifies clockwise screen-space rotation of an asymmetric base hitbox across cardinal angles."""
    proj = mock_asset(
        AssetCategories.CURSORS.value,
        AssetInstances.PROJECTILES.value,
    )
    arrow_props = mock_properties(
        AssetCategories.CURSORS.value,
        AssetInstances.PROJECTILES.value,
        id="arrow",
    )
    # Arrow frame is 41x41 (center 20.5, 20.5); place arrowhead on the +x tip
    arrow_props.hitboxes = [Hitbox(Position(30, 18), Dimensions(10, 5))]
    proj.state.elevation = 0
    proj.state.angle = angle

    rotated = proj.hitbox.get(arrow_props, proj.state, elevation=0)
    assert len(rotated) == 1
    assert (rotated[0].position.x, rotated[0].position.y) == expected_pos
    assert (rotated[0].dimensions.w, rotated[0].dimensions.l) == expected_dim


@pytest.mark.category_cursors
@pytest.mark.workflow_projectiles
def test_rotated_hitbox_diagonal_projection(mock_asset):
    """Verifies tight AABB projection at 45 degrees clockwise around the frame center."""
    proj = mock_asset(
        AssetCategories.CURSORS.value,
        AssetInstances.PROJECTILES.value,
    )
    # 16x16 frame (center 8.0, 8.0); base hitbox center at (13, 8) -> offset (+5, 0)
    proj.properties.hitboxes = [Hitbox(Position(10, 6), Dimensions(6, 4))]
    proj.state.elevation = 0
    proj.state.angle = 45

    rotated = proj.hitboxes
    assert len(rotated) == 1
    assert (rotated[0].position.x, rotated[0].position.y) == (8, 8)
    assert (rotated[0].dimensions.w, rotated[0].dimensions.l) == (7, 7)

@pytest.mark.category_crafts
@pytest.mark.modality_material
def test_material_hitbox_passable_blueprint_returns_empty(mock_asset):
    """MaterialHitbox emits empty elevations and hitboxes for passable surface blueprints."""
    strut = mock_asset(
        AssetCategories.CRAFTS.value,
        AssetInstances.STRUTS.value,
    )
    strut.state.elevation = 0
    strut.state.blueprint = Buildings.FLOORS.value

    assert strut.hitbox.elevations(strut.properties, strut.state) == []
    assert strut.hitboxes == []
    assert strut.hitbox.get(strut.properties, strut.state, elevation=0) == []


@pytest.mark.category_objects
def test_switch_hitbox_closed_and_open(mock_asset):
    """SwitchHitbox emits active hitboxes when closed (switch=False) and [] when open."""
    gate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.GATES.value,
    )
    gate.state.elevation = 0

    gate.state.switch = False
    assert gate.hitbox.elevations(gate.properties, gate.state) == [0]
    assert len(gate.hitboxes) >= 1
    assert gate.hitbox.get(gate.properties, gate.state, elevation=1) == []

    gate.state.switch = True
    assert gate.hitbox.elevations(gate.properties, gate.state) == []
    assert gate.hitboxes == []
    assert gate.hitbox.get(gate.properties, gate.state, elevation=0) == []


@pytest.mark.category_objects
def test_layered_hitbox_in_and_out_projections(mock_board):
    """LayeredHitbox resolves active hitboxes across IN and OUT door projections and normalizes elevation."""
    door = mock_board.instances(AssetInstances.DOORS.value)[0]
    door.state.elevation = 0

    door.state.projection = LayerProjections.IN.value
    assert door.hitbox.elevations(door.properties, door.state) == [0]
    assert len(door.hitboxes) >= 1
    assert door.hitbox.get(door.properties, door.state, elevation=1) == []

    door.state.projection = LayerProjections.OUT.value
    assert door.hitbox.elevations(door.properties, door.state) == [0]
    assert len(door.hitboxes) >= 1
    assert door.hitbox.get(door.properties, door.state, elevation=1) == []

    door.state.elevation = -1
    assert door.hitbox.elevations(door.properties, door.state) == [0]