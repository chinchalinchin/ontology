"""
# Ontology: tests.unit.test_app_game_logic_modules_motion_fields
"""
# Standard Libraries
from unittest.mock import MagicMock

# Testing Libraries
from tests.unit.conftest import DummyFrame, DummyAnimation

# Application Libraires
from app.assets.base import Asset, Taxonomy
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from app.game.logic.modules.motion import fields
from app.models.properties import (
    ObjectProperties, 
    EffectProperties, 
    SheetProperties
)
from app.models.state import (
    EffectState,
    FluidState,
    PlayerState,
    MotorState,
    Mutators,
    MutatorTriggers
)
from app.models.groups import SpawnableGroup
from app.game.logic.modules.motion import fields
from app.services.generators.game.cradle import Cradle

# Cython Libraries
from libs.core.models import Position, Dimensions, Hitbox, Velocity


def test_direction_vectors():
    """
    Verify normalized direction vector mapping across cardinal directions.
    """
    assert fields._direction_vector(Directions.UP.value) == (0.0, -1.0)
    assert fields._direction_vector(Directions.DOWN.value) == (0.0, 1.0)
    assert fields._direction_vector(Directions.LEFT.value) == (-1.0, 0.0)
    assert fields._direction_vector(Directions.RIGHT.value) == (1.0, 0.0)
    assert fields._direction_vector("unknown") == (0.0, 0.0)


def test_fluid_velocity():
    """
    Verify current velocity calculation based on emitter source and flow intensity.
    """
    tax = Taxonomy("w1", "water", AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)
    props = EffectProperties(dimensions=Dimensions(w=32, l=32), count=3)
    state = FluidState(
        id="w1",
        layer="0",
        position=Position(x=0, y=0),
        source=Directions.DOWN.value,
        flow=2
    )
    fluid = Asset(tax, props, state, DummyFrame(), DummyAnimation())

    vx, vy = fields._fluid_velocity(fluid)
    assert vx == 0.0
    assert vy == 40.0  # 2 * BASE_FLOW_SPEED (20.0)


def test_raft_passively_drifts_in_fluid(mock_board, mock_raft):
    """
    Verify raft intersecting an active fluid corridor acquires current velocity.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    mock_raft.state.position = Position(x=70, y=50)

    fields.update([mock_raft], mock_board, 0.016)

    assert mock_raft.state.velocity.vx == 0.0
    assert mock_raft.state.velocity.vy == 40.0


def test_raft_halts_when_outside_fluid(mock_board, mock_raft):
    """
    Verify raft halts to zero velocity when not intersecting any fluid.
    """
    mock_raft.state.position = Position(x=300, y=300)
    mock_raft.state.velocity = Velocity(vx=10.0, vy=10.0)

    fields.update([mock_raft], mock_board, 0.016)

    assert mock_raft.state.velocity.vx == 0.0
    assert mock_raft.state.velocity.vy == 0.0


def test_surface_interception_passenger_on_raft(mock_board, mock_raft):
    """
    Verify passenger on a raft inherits raft drift and suppresses submersion.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    # Raft at (70, 50)
    mock_raft.state.position = Position(x=70, y=50)

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
    player.state.velocity.vx = 0
    player.state.velocity.vy = 10
    player.state.mutators.triggers.submerged = False


    # Configure a typed passive splash asset to satisfy Board.add assertions
    splash_tax = Taxonomy("splash", "splash-1", AssetCategories.EFFECTS.value, AssetInstances.PASSIVE.value)
    splash_props = EffectProperties(dimensions=Dimensions(w=60, l=12), count=3, mass=-1)
    splash_state = EffectState(id="splash", name="splash-1", layer="0", position=Position(x=70, y=66))
    splash_asset = Asset(splash_tax, splash_props, splash_state, DummyFrame(), DummyAnimation())

    mock_board.cradle = MagicMock()
    mock_board.cradle.spawn_passive.return_value = splash_asset

    fields.update([player], mock_board, 0.016)

    # Net velocity = voluntary (0, 10) + current (0, 40)
    assert player.state.velocity.vx == 0.0
    assert player.state.velocity.vy == 50.0
    assert player.state.mutators.triggers.submerged is True

    # Assert mock invocation and validate coordinates without Cython pointer equality mismatch
    assert mock_board.cradle.spawn_passive.call_count == 1
    call_args = mock_board.cradle.spawn_passive.call_args[0]
    assert call_args[0] == "splash"
    assert call_args[1] == "0"
    assert call_args[2].x == 70
    assert call_args[2].y == 66  # 50 + (32 // 2)

    assert splash_asset in mock_board.assets("0")


def test_continuous_immersion_does_not_retrigger_splash(mock_board):
    """
    Verify entity already submerged does not re-dispatch splash particles on subsequent frames.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.length = 100
    fluid.state.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 100))]

    player = mock_board.player()
    player.state.position.x = 70
    player.state.position.y = 50
    player.state.velocity.vx = 0.0
    player.state.velocity.vy= 0.0
    player.state.mutators.triggers.submerged = True


    mock_board.cradle = MagicMock()
    fields.update([player], mock_board, 0.016)

    assert player.state.mutators.triggers.submerged is True
    mock_board.cradle.spawn_passive.assert_not_called()


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