"""
# Ontology: tests.unit.app.game.logic.modules.motion.test_fields
"""
# Standard Libraries
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraires
from app.config.enums import (
    AssetInstances,
    Directions
)
from app.game.logic.modules.motion import fields

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions, 
    Hitbox, 
    Velocity
)


@pytest.mark.fluids
@pytest.mark.motion
def test_direction_vectors():
    """
    Verify normalized direction vector mapping across cardinal directions.
    """
    assert fields._direction_vector(Directions.UP.value) == (0.0, -1.0)
    assert fields._direction_vector(Directions.DOWN.value) == (0.0, 1.0)
    assert fields._direction_vector(Directions.LEFT.value) == (-1.0, 0.0)
    assert fields._direction_vector(Directions.RIGHT.value) == (1.0, 0.0)
    assert fields._direction_vector("unknown") == (0.0, 0.0)


@pytest.mark.fluids
@pytest.mark.motion
def test_shoreline_normals():
    """
    Verify inward water normal vectors across cardinal bank orientations.
    """
    assert fields._shoreline_normal(Directions.UP.value) == (0.0, 1.0)
    assert fields._shoreline_normal(Directions.DOWN.value) == (0.0, -1.0)
    assert fields._shoreline_normal(Directions.LEFT.value) == (1.0, 0.0)
    assert fields._shoreline_normal(Directions.RIGHT.value) == (-1.0, 0.0)
    assert fields._shoreline_normal("unknown") == (0.0, 0.0)


@pytest.mark.fluids
@pytest.mark.motion
def test_fluid_velocity(mock_fluid):
    """
    Verify current velocity calculation based on emitter source and flow intensity.
    """
    mock_fluid.state.flow = 2
    with patch('app.config.settings.BASE_FLOW_SPEED', 20):
        vx, vy = fields._fluid_velocity(mock_fluid)
        assert vx == 0.0
        assert vy == 40.0  # 2 * BASE_FLOW_SPEED (20.0)


@pytest.mark.fluids
@pytest.mark.motion
def test_raft_passively_drifts_in_fluid(mock_board, mock_raft, mock_fluid):
    """
    Verify raft intersecting an active fluid corridor acquires current velocity.
    """
    mock_fluid.state.length = 100
    mock_fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    mock_raft.state.position = Position(x=70, y=50)

    fields.update([mock_raft], mock_board, 0.016)

    assert mock_raft.state.velocity.vx == 0.0
    assert mock_raft.state.velocity.vy == 40.0


@pytest.mark.fluids
@pytest.mark.motion
def test_raft_halts_when_outside_fluid(mock_board, mock_raft):
    """
    Verify raft halts to zero velocity when not intersecting any fluid.
    """
    mock_raft.state.position = Position(x=300, y=300)
    mock_raft.state.velocity = Velocity(vx=10.0, vy=10.0)

    fields.update([mock_raft], mock_board, 0.016)

    assert mock_raft.state.velocity.vx == 0.0
    assert mock_raft.state.velocity.vy == 0.0


@pytest.mark.fluids
@pytest.mark.motion
def test_surface_interception_passenger_on_raft(mock_board, mock_raft, mock_fluid):
    """
    Verify passenger on a raft inherits raft drift and suppresses submersion.
    """
    mock_fluid.state.length = 100
    mock_fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    # Raft at (70, 50) registered onto the board
    mock_raft.state.position = Position(x=70, y=50)
    mock_board.add([mock_raft])

    player = mock_board.player()
    player.state.position.x = 70
    player.state.position.y = 50
    player.state.velocity.vx = 5.0
    player.state.velocity.vy = 0.0
    player.state.mutators.triggers.submerged = True

    fields.update([mock_raft, player], mock_board, 0.016)

    # Player voluntary velocity (5, 0) + raft velocity (0, 40)
    assert player.state.velocity.vx == 5.0
    assert player.state.velocity.vy == 40.0
    assert player.state.mutators.triggers.submerged is False


@pytest.mark.fluids
@pytest.mark.motion
def test_direct_immersion_in_fluid_adds_velocity_and_spawns_splash(mock_board):
    """
    Verify un-rafted entity entering fluid acquires current velocity,
    sets submerged=True, and generates a splash asset on the board layer.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    player = mock_board.player()
    player.state.position.x = 70
    player.state.position.y = 50
    player.state.velocity.vx = 0.0
    player.state.velocity.vy = 10.0
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
    assert passives[-1].state.position.x == 70
    assert passives[-1].state.position.y == 82  # 50 + (64 // 2)


@pytest.mark.fluids
@pytest.mark.motion
def test_entity_leaving_fluid_clears_submersion(mock_board):
    """
    Verify entity leaving fluid corridor clears submerged trigger.
    """
    player = mock_board.player()
    player.state.position.x = 300
    player.state.position.y = 300
    player.state.velocity.vx = 0.0
    player.state.velocity.vy = 0.0
    player.state.mutators.triggers.submerged = True

    fields.update([player], mock_board, 0.016)

    assert player.state.mutators.triggers.submerged is False


@pytest.mark.fluids
@pytest.mark.motion
def test_lateral_fluid_flow_left(mock_board):
    """
    Verify lateral leftward fluid flow correctly imparts negative X velocity.
    """
    player = mock_board.player()
    player.state.position.x = 150
    player.state.position.y = 100
    player.state.velocity.vx = 0 
    player.state.velocity.vy = 0
    player.state.mutators.triggers.submerged = False

    fields.update([player], mock_board, 0.016)

    # flow = 1 * BASE_FLOW_SPEED (20.0) directed LEFT -> vx = -20.0
    assert player.state.velocity.vx == -20.0
    assert player.state.velocity.vy == 0.0
    assert player.state.mutators.triggers.submerged is True


@pytest.mark.fluids
@pytest.mark.motion
def test_projectiles_bypass_field_forces(mock_board, mock_projectile):
    """
    Verify ballistic projectiles ignore environmental fluid fields.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    mock_board.add([mock_projectile])

    fields.update([mock_projectile], mock_board, 0.016)

    # Ballistic velocity remains unaffected by current
    assert mock_projectile.state.velocity.vx == 50.0
    assert mock_projectile.state.velocity.vy == 0.0


@pytest.mark.fluids
@pytest.mark.motion
def test_fields_shoreline_entry_nudge_and_submerge(mock_board, mock_shoreline):
    """
    Verify crossing shoreline into water applies orthogonal step-down displacement
    accounting for shoreline thickness and half asset width, toggles submerged=True,
    and spawns splash particles.
    """
    player = mock_board.player()
    player.state.position = Position(x=70, y=0)
    # Moving East (+X) into water against West shoreline (orientation=LEFT, normal=(1, 0))
    player.state.velocity = Velocity(vx=4.0, vy=0.0)
    player.state.mutators.triggers.submerged = False

    mock_board.add([mock_shoreline])

    fields.update([player], mock_board, 0.016)

    # Nudged along normal (1, 0) by thickness (8px) + half-width (32px): x = 70 + 40 = 110
    assert player.state.position.x == 110
    assert player.state.position.y == 0
    assert player.state.mutators.triggers.submerged is True

    # Verify splash particle spawned at post-displacement position
    passives = mock_board.instances(AssetInstances.PASSIVE.value, "0")
    assert len(passives) > 0
    assert passives[-1].state.position.x == 110
    assert passives[-1].state.position.y == 0 + (player.dimensions.l // 2)


@pytest.mark.fluids
@pytest.mark.motion
def test_fields_shoreline_sheer_ledge_blocks_exit(mock_board, mock_shoreline):
    """
    Verify non-bidirectional sheer ledges nullify velocities directed against the bank.
    """
    player = mock_board.player()
    player.state.position = Position(x=70, y=0)
    player.state.mutators.triggers.submerged = True

    # Configure shoreline as one-way ledge
    mock_shoreline.state.bidirectional = False
    # Player trying to move West (-X) out of water (v_dot = -4 * 1 < 0)
    player.state.velocity = Velocity(vx=-4.0, vy=0.0)

    mock_board.add([mock_shoreline])

    fields.update([player], mock_board, 0.016)

    # Velocity directed against the bank is nullified
    assert player.state.velocity.vx == 0.0


@pytest.mark.fluids
@pytest.mark.motion
def test_surface_interception_bridge_deck_crossings(mock_board, mock_bridge, mock_fluid):
    """
    Verify entities traversing a bridge deck suppress submersion, bypass fluid current
    drift, and do not emit splash particles.
    """
    mock_fluid.state.length = 100
    mock_fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    mock_bridge.state.position = Position(x=70, y=50)
    mock_board.add([mock_bridge])

    player = mock_board.player()
    player.state.position.x = 70
    player.state.position.y = 50
    player.state.velocity.vx = 4.0
    player.state.velocity.vy = 0.0
    player.state.mutators.triggers.submerged = True

    initial_passives = len(mock_board.instances(AssetInstances.PASSIVE.value, "0"))

    fields.update([player], mock_board, 0.016)

    assert player.state.velocity.vx == 4.0
    assert player.state.velocity.vy == 0.0
    assert player.state.mutators.triggers.submerged is False
    assert len(mock_board.instances(AssetInstances.PASSIVE.value, "0")) == initial_passives


@pytest.mark.fluids
@pytest.mark.motion
def test_surface_interception_bridge_preempts_shoreline(mock_board, mock_bridge, mock_shoreline):
    """
    Verify bridge deck surface interception evaluates before shoreline edge crossing,
    suppressing orthogonal drop nudges and splash triggers.
    """
    mock_bridge.state.position = Position(x=70, y=0)
    mock_shoreline.state.position = Position(x=70, y=0)
    mock_board.add([mock_bridge, mock_shoreline])

    player = mock_board.player()
    player.state.position = Position(x=70, y=0)
    player.state.velocity = Velocity(vx=4.0, vy=0.0)
    player.state.mutators.triggers.submerged = False

    fields.update([player], mock_board, 0.016)

    # Position is not nudged by shoreline thickness (8px)
    assert player.state.position.x == 70
    assert player.state.mutators.triggers.submerged is False


@pytest.mark.fluids
@pytest.mark.motion
@pytest.mark.parametrize(
    "orientation,init_x,init_y,vx,vy,expected_x,expected_y",
    [
        # West bank (normal = (1, 0)): nudged +X by t(8) + w//2(32) = +40
        (Directions.LEFT.value, 70, 50, 4.0, 0.0, 110, 50),
        # East bank (normal = (-1, 0)): nudged -X by t(8) + w//2(32) = -40
        (Directions.RIGHT.value, 70, 50, -4.0, 0.0, 30, 50),
        # North bank (normal = (0, 1)): nudged +Y by t(8) + l//2(32) = +40
        (Directions.UP.value, 70, 50, 0.0, 4.0, 70, 90),
        # South bank (normal = (0, -1)): nudged -Y by t(8) + l//2(32) = -40
        (Directions.DOWN.value, 70, 50, 0.0, -4.0, 70, 10),
    ],
)
def test_fields_shoreline_entry_nudge_cardinal_axes(
    mock_board,
    mock_shoreline,
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
    mock_shoreline.state.orientation = orientation
    mock_shoreline.state.thickness = 8
    mock_shoreline.state.position = Position(x=70, y=50)
    mock_shoreline.state.hitboxes = [
        Hitbox(Position(0, 0), Dimensions(32, 32))
    ]
    mock_board.add([mock_shoreline])

    player = mock_board.player()
    player.state.position = Position(x=init_x, y=init_y)
    player.state.velocity = Velocity(vx=vx, vy=vy)
    player.state.mutators.triggers.submerged = False

    fields.update([player], mock_board, 0.016)

    assert player.state.position.x == expected_x
    assert player.state.position.y == expected_y
    assert player.state.mutators.triggers.submerged is True


@pytest.mark.fluids
@pytest.mark.motion
def test_fields_bipartite_heterogeneous_resolution(
    mock_board, 
    mock_bridge, 
    mock_raft, 
    mock_crate, 
    mock_fluid
):
    """
    Verify physics.environment resolves multiple entities across bridges, rafts, 
    and direct fluid immersion in a single frame update.
    """
    # Active stream corridor along x=70, y=[0, 300)
    mock_fluid.state.length = 300
    mock_fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 300))]

    # Bridge deck spans at (70, 50)
    mock_bridge.state.position = Position(x=70, y=50)

    # Raft floats downstream at (70, 150)
    mock_raft.state.position = Position(x=70, y=150)

    # Player 1 on bridge deck: voluntary movement only, submerged=False
    player = mock_board.player()
    player.state.position = Position(x=70, y=50)
    player.state.velocity = Velocity(vx=5.0, vy=0.0)

    # Crate immersed directly in fluid channel: acquires flow velocity (0, 40)
    mock_crate.state.position = Position(x=70, y=250)
    mock_crate.state.velocity = Velocity(vx=0.0, vy=0.0)

    # NPC Sprite aboard the raft: inherits raft velocity
    sprite = mock_board.instances(AssetInstances.SPRITES.value)[0]
    sprite.state.layer = "0"
    sprite.state.position = Position(x=70, y=150)
    sprite.state.velocity = Velocity(vx=0.0, vy=0.0)

    all_entities = [mock_raft, player, mock_crate, sprite]
    fields.update(all_entities, mock_board, 0.016)

    # 1. Player on bridge deck
    assert player.state.velocity.vx == 5.0
    assert player.state.velocity.vy == 0.0
    assert player.state.mutators.triggers.submerged is False

    # 2. Crate in water corridor
    assert mock_crate.state.velocity.vy == 40.0
    assert mock_crate.state.mutators.triggers.submerged is True

    # 3. Sprite aboard drifting raft
    assert sprite.state.velocity.vy == 40.0
    assert sprite.state.mutators.triggers.submerged is False