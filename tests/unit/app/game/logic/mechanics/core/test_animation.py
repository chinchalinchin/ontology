"""
@domain.test
@test.unit
@app.core
@app.mechanic

# Ontology: Tests - tests.unit.app.game.logic.mechanics.core.test_animation

Unit tests for the AnimationMechanics implementation.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Mechanics,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_core,
    pytest.mark.asset_animation,
    pytest.mark.workflow_rendering,
]

# -----------------------------------------------------


def test_animation_mechanics_update(mock_board, mock_mechanic, mock_bus):
    """
    Ensure AnimationMechanics mutates animation frames on active Sheets and Effects
    and decrements Reactable cooldowns on the Board when unpaused.
    """
    mechanic = mock_mechanic(Mechanics.ANIMATION.value)
    payload = mock_board.device.poll()
    mock_board.paused = False

    # 1. Sheet animations (Pixie uses StateAnimation; Player uses SpriteAnimation)
    pixie = mock_board.instances(AssetInstances.PIXIES.value)[0]
    pixie_action = pixie.properties.actions[pixie.state.animation.action]
    pixie.state.animation.frame = 0
    pixie.state.animation.tick = pixie_action.delay

    player = mock_board.player()
    player_action = player.properties.actions[player.state.animation.action]
    player.state.mutators.triggers.animated = True
    player.state.animation.frame = 0
    player.state.animation.tick = player_action.delay

    # 2. Effect animations (Torch uses FrequencyAnimation)
    torch = mock_board.instances(AssetInstances.PASSIVE.value)[0]
    torch.state.mutators.triggers.animated = True
    torch.state.animation.frame = 0
    torch.state.animation.tick = torch.properties.frequency.delay

    # 3. Reactable cooldowns
    dummy = mock_board.instances(AssetInstances.REACTABLES.value)[0]
    dummy.state.active = True
    initial_cooldown = dummy.state.cooldown

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert pixie.state.animation.frame == 1
    assert pixie.state.animation.tick == 0
    assert player.state.animation.frame == 1
    assert player.state.animation.tick == 0
    assert torch.state.animation.frame == 1
    assert dummy.state.cooldown != initial_cooldown or dummy.state.active is False


def test_animation_mechanics_paused_board_noop(mock_board, mock_mechanic, mock_bus):
    """
    Ensure AnimationMechanics skips world asset frame mutations when the Board is paused.
    """
    mechanic = mock_mechanic(Mechanics.ANIMATION.value)
    payload = mock_board.device.poll()
    mock_board.paused = True

    pixie = mock_board.instances(AssetInstances.PIXIES.value)[0]
    pixie_action = pixie.properties.actions[pixie.state.animation.action]
    pixie.state.animation.frame = 0
    pixie.state.animation.tick = pixie_action.delay

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert pixie.state.animation.frame == 0
    assert pixie.state.animation.tick == pixie_action.delay