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

# TODO: everything should use fixtures

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
    sets submerged=True, and dispatches splash generation via Cradle.
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

    # Spy on Cradle.spawn_passive using the wired fixture testbed
    with patch.object(mock_board.cradle, "spawn_passive", wraps=mock_board.cradle.spawn_passive) as spy_spawn:
        fields.update([player], mock_board, 0.016)

        # Net velocity = voluntary (0, 10) + current (0, 40)
        assert player.state.velocity.vx == 0.0
        assert player.state.velocity.vy == 50.0
        assert player.state.mutators.triggers.submerged is True

        assert spy_spawn.call_count == 1
        call_args = spy_spawn.call_args[0]
        assert call_args[0] == "splash"
        assert call_args[1] == "0"
        assert call_args[2].x == 70
        assert call_args[2].y == 82  # 50 + (64 // 2)

        # Confirm splash entity is persisted to the active board layer
        passives = mock_board.instances(AssetInstances.PASSIVE.value, "0")
        assert len(passives) > 0


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
    Verify crossing shoreline into water applies orthogonal step-down displacement,
    toggles submerged=True, and spawns splash particles.
    """
    player = mock_board.player()
    player.state.position = Position(x=70, y=0)
    # Moving East (+X) into water against West shoreline (orientation=LEFT, normal=(1, 0))
    player.state.velocity = Velocity(vx=4.0, vy=0.0)
    player.state.mutators.triggers.submerged = False

    mock_board.add([mock_shoreline])

    fields.update([player], mock_board, 0.016)

    # Position nudged by thickness (8px) along inward water normal (1, 0) -> x = 70 + 8 = 78
    assert player.state.position.x == 78
    assert player.state.mutators.triggers.submerged is True

    # Verify splash particle spawned
    passives = mock_board.instances(AssetInstances.PASSIVE.value, "0")
    assert len(passives) > 0


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