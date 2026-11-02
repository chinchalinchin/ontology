"""
@domain.test
@test.unit
@app.module
@physics.fields
@workflow.fluids

# Ontology: Tests - tests.unit.app.game.logic.modules.motion.test_field_motion

Unit Tests for Field motion calculations.
"""
# Standard Libraries
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
)
from app.game.logic.modules.motion import fields
from app.services.generators.game import Cartographer

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position,
    Velocity,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.physics_fields,
    pytest.mark.workflow_fluids,
]

# -----------------------------------------------------


def test_direction_vectors():
    """
    Verify normalized direction vector mapping across cardinal directions.
    """
    assert fields._direction_vector(Directions.UP.value) == (0.0, -1.0)
    assert fields._direction_vector(Directions.DOWN.value) == (0.0, 1.0)
    assert fields._direction_vector(Directions.LEFT.value) == (-1.0, 0.0)
    assert fields._direction_vector(Directions.RIGHT.value) == (1.0, 0.0)
    assert fields._direction_vector("unknown") == (0.0, 0.0)


def test_shoreline_normals():
    """
    Verify inward water normal vectors across cardinal bank orientations.
    """
    assert fields._shoreline_normal(Directions.UP.value) == (0.0, 1.0)
    assert fields._shoreline_normal(Directions.DOWN.value) == (0.0, -1.0)
    assert fields._shoreline_normal(Directions.LEFT.value) == (1.0, 0.0)
    assert fields._shoreline_normal(Directions.RIGHT.value) == (-1.0, 0.0)
    assert fields._shoreline_normal("unknown") == (0.0, 0.0)


@patch("app.static.settings.BASE_FLOW_SPEED", 20)
def test_fluid_velocity(mock_asset):
    """
    Verify current velocity calculation based on emitter source and flow intensity.
    """
    mock_fluid = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.FLUIDS.value,
    )
    vx, vy = fields._fluid_velocity(mock_fluid)
    assert vx == 0.0
    assert vy == 40.0  # flow (2) * BASE_FLOW_SPEED (20.0)


def test_raft_passively_drifts_in_fluid(mock_board):
    """
    Verify raft intersecting an active fluid corridor acquires current velocity.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    raft = mock_board.instances(AssetInstances.RAFTS.value)[0]

    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    raft.state.position = Position(x=70, y=50)

    fields.update([raft], mock_board, 0.016)

    assert raft.state.velocity.vx == 0.0
    assert raft.state.velocity.vy == 40.0


def test_raft_halts_when_outside_fluid(mock_board):
    """
    Verify raft halts to zero velocity when not intersecting any fluid.
    """
    raft = mock_board.instances(AssetInstances.RAFTS.value)[0]

    raft.state.position = Position(x=300, y=300)
    raft.state.velocity = Velocity(vx=10.0, vy=10.0)

    fields.update([raft], mock_board, 0.016)

    assert raft.state.velocity.vx == 0.0
    assert raft.state.velocity.vy == 0.0


def test_raft_halts_when_layer_has_no_fluids(mock_board):
    """
    Verify raft velocity resets to zero when all layer fluids are removed.
    """
    fluids = list(mock_board.instances(AssetInstances.FLUIDS.value))
    mock_board.remove(fluids)

    raft = mock_board.instances(AssetInstances.RAFTS.value)[0]
    raft.state.velocity = Velocity(vx=15.0, vy=25.0)

    fields.update([raft], mock_board, 0.016)

    assert raft.state.velocity.vx == 0.0
    assert raft.state.velocity.vy == 0.0


def test_surface_interception_passenger_on_raft(mock_board):
    """
    Verify passenger on a raft inherits raft drift and suppresses submersion.
    """
    raft = mock_board.instances(AssetInstances.RAFTS.value)[0]
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]

    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    raft.state.position = Position(x=70, y=50)
    rhb = raft.hitboxes[0]

    player = mock_board.player()
    phb = player.hitboxes[0]
    # Align player hitbox (offset 23, 34) directly over raft hitbox at (70, 50)
    player.state.position = Position(
        x=raft.state.position.x + rhb.position.x - phb.position.x,
        y=raft.state.position.y + rhb.position.y - phb.position.y,
    )
    player.state.velocity = Velocity(vx=5.0, vy=0.0)
    player.state.mutators.triggers.submerged = True

    fields.update([raft, player], mock_board, 0.016)

    # Player voluntary velocity (5, 0) + raft velocity (0, 40)
    assert player.state.velocity.vx == 5.0
    assert player.state.velocity.vy == 40.0
    assert player.state.mutators.triggers.submerged is False


def test_direct_immersion_in_fluid_adds_velocity_and_spawns_splash(mock_board):
    """
    Verify un-rafted entity entering fluid acquires current velocity,
    sets submerged=True, and generates a splash asset on the board layer.
    """
    Cartographer.purge("0", mock_board)

    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 150
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 150))]

    # test-fluid-00 spans x in [60, 92], y in [0, 150].
    # Player at (50, 50) places its hitbox [50+23, 50+41] = [73, 91] inside the stream.
    player = mock_board.player()
    player.state.position = Position(x=50, y=50)
    player.state.velocity = Velocity(vx=0.0, vy=10.0)
    player.state.mutators.triggers.submerged = False

    initial_passives = len(mock_board.instances(AssetInstances.PASSIVE.value, "0"))

    fields.update([player], mock_board, 0.016)

    # Net velocity = voluntary (0, 10) + current (0, 40)
    assert player.state.velocity.vx == 0.0
    assert player.state.velocity.vy == 50.0
    assert player.state.mutators.triggers.submerged is True

    # Confirm splash entity is persisted to the active board layer
    passives = mock_board.instances(AssetInstances.PASSIVE.value, "0")
    assert len(passives) == initial_passives + 1
    assert passives[-1].state.position.x == 50
    assert passives[-1].state.position.y == 82  # 50 + (64 // 2)


def test_entity_leaving_fluid_clears_submersion(mock_board):
    """
    Verify entity leaving fluid corridor clears submerged trigger.
    """
    player = mock_board.player()
    player.state.position = Position(x=300, y=300)
    player.state.velocity = Velocity(vx=0.0, vy=0.0)
    player.state.mutators.triggers.submerged = True

    fields.update([player], mock_board, 0.016)

    assert player.state.mutators.triggers.submerged is False


def test_lateral_fluid_flow_left(mock_board):
    """
    Verify lateral leftward fluid flow correctly imparts negative X velocity.
    """
    Cartographer.purge("0", mock_board)

    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=250, y=100)
    fluid.state.source = Directions.LEFT.value
    fluid.state.flow = 1
    fluid.state.length = 150
    fluid.state.hitboxes = [Hitbox(Position(-150, 0), Dimensions(150, 32))]

    # Stream spans x in [100, 250], y in [100, 132].
    # Player at (130, 75) has hitbox at [153, 171] x [109, 124].
    player = mock_board.player()
    player.state.position = Position(x=130, y=75)
    player.state.velocity = Velocity(vx=0.0, vy=0.0)
    player.state.mutators.triggers.submerged = False

    fields.update([player], mock_board, 0.016)

    # flow = 1 * BASE_FLOW_SPEED (20.0) directed LEFT -> vx = -20.0
    assert player.state.velocity.vx == -20.0
    assert player.state.velocity.vy == 0.0
    assert player.state.mutators.triggers.submerged is True


def test_projectiles_bypass_field_forces(mock_board, mock_asset):
    """
    Verify ballistic projectiles ignore environmental fluid fields.
    """
    projectile = mock_asset(
        AssetCategories.CURSORS.value,
        AssetInstances.PROJECTILES.value,
    )
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    mock_board.add([projectile])

    fields.update([projectile], mock_board, 0.016)

    # Ballistic velocity remains unaffected by current
    assert projectile.state.velocity.vx == 50.0
    assert projectile.state.velocity.vy == 0.0


def test_fields_shoreline_entry_nudge_and_submerge(mock_board):
    """
    Verify crossing shoreline into water applies orthogonal step-down displacement
    accounting for shoreline thickness (22px) and half asset width (32px),
    toggles submerged=True, and spawns splash particles.
    """
    shoreline = mock_board.shorelines("0")[0]
    other_shores = [s for s in mock_board.shorelines("0") if s is not shoreline]
    mock_board.remove(other_shores)

    shoreline.state.orientation = Directions.LEFT.value
    shoreline.state.position = Position(x=300, y=300)
    shoreline.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(64, 64))]

    player = mock_board.player()
    player.state.position = Position(x=300, y=300)
    # Moving East (+X) into water against West shoreline (orientation=LEFT, normal=(1, 0))
    player.state.velocity = Velocity(vx=4.0, vy=0.0)
    player.state.mutators.triggers.submerged = False

    initial_passives = len(mock_board.instances(AssetInstances.PASSIVE.value, "0"))

    fields.update([player], mock_board, 0.016)

    expected_step = shoreline.properties.thickness + (player.dimensions.w // 2)
    assert player.state.position.x == 300 + expected_step
    assert player.state.position.y == 300
    assert player.state.mutators.triggers.submerged is True

    # Verify splash particle spawned at post-displacement position
    passives = mock_board.instances(AssetInstances.PASSIVE.value, "0")
    assert len(passives) == initial_passives + 1
    assert passives[-1].state.position.x == 300 + expected_step
    assert passives[-1].state.position.y == 300 + (player.dimensions.l // 2)


def test_surface_interception_bridge_deck_crossings(mock_board):
    """
    Verify entities traversing a bridge deck suppress submersion, bypass fluid current
    drift, and do not emit splash particles.
    """
    mock_fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    mock_fluid.state.length = 150
    mock_fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 150))]

    mock_bridge = mock_board.bridges("0")[0]
    mock_bridge.state.position = Position(x=50, y=50)

    player = mock_board.player()
    player.state.position = Position(x=50, y=50)
    player.state.velocity = Velocity(vx=4.0, vy=0.0)
    player.state.mutators.triggers.submerged = True

    initial_passives = len(mock_board.instances(AssetInstances.PASSIVE.value, "0"))

    fields.update([player], mock_board, 0.016)

    assert player.state.velocity.vx == 4.0
    assert player.state.velocity.vy == 0.0
    assert player.state.mutators.triggers.submerged is False
    assert len(mock_board.instances(AssetInstances.PASSIVE.value, "0")) == initial_passives


def test_surface_interception_bridge_preempts_shoreline(mock_board):
    """
    Verify bridge deck surface interception evaluates before shoreline edge crossing,
    suppressing orthogonal drop nudges and splash triggers.
    """
    bridge = mock_board.bridges("0")[0]
    bridge.state.position = Position(x=300, y=300)

    shoreline = mock_board.shorelines("0")[0]
    shoreline.state.orientation = Directions.LEFT.value
    shoreline.state.position = Position(x=300, y=300)
    shoreline.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(64, 64))]

    player = mock_board.player()
    player.state.position = Position(x=300, y=300)
    player.state.velocity = Velocity(vx=4.0, vy=0.0)
    player.state.mutators.triggers.submerged = False

    fields.update([player], mock_board, 0.016)

    # Position is not nudged by shoreline
    assert player.state.position.x == 300
    assert player.state.position.y == 300
    assert player.state.mutators.triggers.submerged is False


@pytest.mark.parametrize(
    "orientation,init_x,init_y,vx,vy,expected_x,expected_y",
    [
        # temperate-banks thickness (22) + player half-dimension (32) = 54px nudge
        # West bank (normal = (1, 0)): nudged +X by 54 -> 354
        (Directions.LEFT.value, 300, 300, 4.0, 0.0, 354, 300),
        # East bank (normal = (-1, 0)): nudged -X by 54 -> 246
        (Directions.RIGHT.value, 300, 300, -4.0, 0.0, 246, 300),
        # North bank (normal = (0, 1)): nudged +Y by 54 -> 354
        (Directions.UP.value, 300, 300, 0.0, 4.0, 300, 354),
        # South bank (normal = (0, -1)): nudged -Y by 54 -> 246
        (Directions.DOWN.value, 300, 300, 0.0, -4.0, 300, 246),
    ],
)
def test_fields_shoreline_entry_nudge_cardinal_axes(
    mock_board,
    orientation,
    init_x,
    init_y,
    vx,
    vy,
    expected_x,
    expected_y,
):
    """
    Verify orthogonal displacement applies thickness + half-dimension across all
    cardinal entry normals (w // 2 for horizontal, l // 2 for vertical).
    """
    shoreline = mock_board.shorelines("0")[0]
    other_shores = [s for s in mock_board.shorelines("0") if s is not shoreline]
    mock_board.remove(other_shores)

    shoreline.state.orientation = orientation
    shoreline.state.position = Position(x=init_x, y=init_y)
    shoreline.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(64, 64))]

    player = mock_board.player()
    player.state.position = Position(x=init_x, y=init_y)
    player.state.velocity = Velocity(vx=vx, vy=vy)
    player.state.mutators.triggers.submerged = False

    fields.update([player], mock_board, 0.016)

    assert player.state.position.x == expected_x
    assert player.state.position.y == expected_y
    assert player.state.mutators.triggers.submerged is True


def test_fields_bipartite_heterogeneous_resolution(mock_board):
    """
    Verify physics.environment resolves multiple entities across bridges, rafts,
    and direct fluid immersion in a single frame update.
    """
    Cartographer.purge("0", mock_board)

    # Active stream corridor along x in [60, 92], y in [0, 350]
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 350
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 350))]

    # Bridge deck spans over stream at (50, 50)
    bridge = mock_board.bridges("0")[0]
    bridge.state.position = Position(x=50, y=50)

    # Raft floats downstream at (70, 150)
    raft = mock_board.instances(AssetInstances.RAFTS.value)[0]
    raft.state.position = Position(x=70, y=150)
    rhb = raft.hitboxes[0]

    # Player on bridge deck: voluntary movement only, submerged=False
    player = mock_board.player()
    player.state.position = Position(x=50, y=50)
    player.state.velocity = Velocity(vx=5.0, vy=0.0)
    player.state.mutators.triggers.submerged = False

    # Crate immersed directly in fluid channel: acquires flow velocity (0, 40)
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=250)
    crate.state.velocity = Velocity(vx=0.0, vy=0.0)
    crate.state.mutators.triggers.submerged = False

    # NPC Sprite aboard the raft: inherits raft velocity
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    shb = sprite.hitboxes[0]
    sprite.state.layer = "0"
    sprite.state.position = Position(
        x=raft.state.position.x + rhb.position.x - shb.position.x,
        y=raft.state.position.y + rhb.position.y - shb.position.y,
    )
    sprite.state.velocity = Velocity(vx=0.0, vy=0.0)
    sprite.state.mutators.triggers.submerged = False

    all_entities = [raft, player, crate, sprite]
    fields.update(all_entities, mock_board, 0.016)

    # 1. Player on bridge deck
    assert player.state.velocity.vx == 5.0
    assert player.state.velocity.vy == 0.0
    assert player.state.mutators.triggers.submerged is False

    # 2. Crate in water corridor
    assert crate.state.velocity.vy == 40.0
    assert crate.state.mutators.triggers.submerged is True

    # 3. Sprite aboard drifting raft
    assert sprite.state.velocity.vy == 40.0
    assert sprite.state.mutators.triggers.submerged is False