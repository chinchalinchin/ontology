"""
@domain.test
@test.unit
@app.asset
@asset.animation

# Ontology: Test - tests.unit.app.assets.test_animations

Unit tests for Asset Animation implementations.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import Frequency
from app.models.state import AttachmentState
from app.static.semantics import (
    Actions,
    AssetCategories,
    AssetInstances,
    Frequencies,
)

# Cython Libraries
from libs.core.models import Position

pytestmark = [
    pytest.mark.app_asset,
    pytest.mark.asset_animation,
]


@pytest.mark.app_core
def test_no_animation(mock_asset):
    crate = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    assert crate.animation.animate(crate.state, crate.properties) == crate.state


@pytest.mark.category_effects
def test_frequency_animation_inactive(mock_asset):
    effect = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    effect.state.active = False
    effect.state.animation.frame = 2
    effect.state.animation.tick = 3

    effect.animation.animate(effect.state, effect.properties)
    assert effect.state.animation.frame == 0
    assert effect.state.animation.tick == 0


@pytest.mark.category_effects
def test_frequency_animation_continuous(mock_asset):
    effect = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    effect.properties.count = 3
    effect.properties.frequency = Frequency(
        type=Frequencies.CONTINUOUS.value,
        delay=2,
    )
    effect.state.active = True
    effect.state.animation.frame = 0
    effect.state.animation.tick = 0

    # Tick 1: Pacing delay threshold not reached
    effect.animation.animate(effect.state, effect.properties)
    assert effect.state.animation.tick == 1
    assert effect.state.animation.frame == 0

    # Tick 2: Delay reached, frame increments
    effect.animation.animate(effect.state, effect.properties)
    assert effect.state.animation.tick == 0
    assert effect.state.animation.frame == 1

    # Advance to end of cycle and verify modulo wrap
    effect.state.animation.frame = 2
    effect.state.animation.tick = 1
    effect.animation.animate(effect.state, effect.properties)
    assert effect.state.animation.tick == 0
    assert effect.state.animation.frame == 0


@pytest.mark.category_effects
def test_frequency_animation_temporary_non_persisting(mock_asset):
    effect = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    effect.properties.count = 3
    effect.properties.frequency = Frequency(
        type=Frequencies.TEMPORARY.value,
        delay=1,
        persist=False,
    )
    effect.state.active = True
    effect.state.animation.frame = 0
    effect.state.animation.tick = 0

    # Advances through frames up to count
    effect.animation.animate(effect.state, effect.properties)
    assert effect.state.animation.frame == 1

    effect.state.animation.frame = 3
    effect.animation.animate(effect.state, effect.properties)
    # Beyond count, frame advancement halts for garbage collection
    assert effect.state.animation.frame == 3


@pytest.mark.category_effects
def test_frequency_animation_temporary_persisting(mock_asset):
    effect = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    effect.properties.count = 3
    effect.properties.frequency = Frequency(
        type=Frequencies.TEMPORARY.value,
        delay=1,
        persist=True,
    )
    effect.state.active = True
    effect.state.animation.frame = 1
    effect.state.animation.tick = 0

    effect.animation.animate(effect.state, effect.properties)
    assert effect.state.animation.frame == 2

    # Clamps to count - 1 when persist=True
    effect.animation.animate(effect.state, effect.properties)
    assert effect.state.animation.frame == 2


@pytest.mark.category_effects
def test_frequency_animation_periodic(mock_asset):
    effect = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.PASSIVE.value,
    )
    effect.properties.count = 2
    effect.properties.frequency = Frequency(
        type=Frequencies.PERIODIC.value,
        delay=2,
        frequency=8,
    )
    effect.state.active = True
    effect.state.animation.frame = 0
    effect.state.animation.tick = 0

    # Active duration = 2 * 2 = 4 ticks. Frame 0 during ticks 0-1
    effect.animation.animate(effect.state, effect.properties)  # tick 1
    assert effect.state.animation.frame == 0

    effect.animation.animate(effect.state, effect.properties)  # tick 2
    assert effect.state.animation.frame == 1

    effect.animation.animate(effect.state, effect.properties)  # tick 3
    assert effect.state.animation.frame == 1

    effect.animation.animate(effect.state, effect.properties)  # tick 4 -> idle resting frame
    assert effect.state.animation.frame == 0

    effect.state.animation.tick = 7
    effect.animation.animate(effect.state, effect.properties)  # tick 8 reaches frequency limit
    assert effect.state.animation.tick == 0
    assert effect.state.animation.frame == 0


@pytest.mark.category_effects
def test_frequency_animation_cooldown_and_reset(mock_asset):
    reactable = mock_asset(
        AssetCategories.EFFECTS.value,
        AssetInstances.REACTABLES.value,
    )
    reactable.properties.count = 3
    reactable.properties.frequency = Frequency(
        type=Frequencies.TEMPORARY.value,
        delay=1,
        cooldown=60,
        persist=True,
    )
    reactable.state.active = True
    reactable.state.cooldown = 2
    reactable.state.animation.frame = 2
    reactable.state.animation.tick = 0

    # Frame matches clamp limit (count - 1): decrement cooldown
    reactable.animation.cooldown(reactable.state, reactable.properties)
    assert reactable.state.cooldown == 1
    assert reactable.state.active is True

    # Cooldown expires: resets state and restores base cooldown
    reactable.animation.cooldown(reactable.state, reactable.properties)
    assert reactable.state.cooldown == 60
    assert reactable.state.active is False
    assert reactable.state.animation.frame == 0
    assert reactable.state.animation.tick == 0


@pytest.mark.category_sheets
def test_state_animation(mock_asset):
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    walk_action = sprite.properties.actions[Actions.WALK.value]
    walk_action.delay = 2
    walk_action.count = 3

    sprite.state.animation.action = Actions.WALK.value
    sprite.state.animation.frame = 0
    sprite.state.animation.tick = 0
    sprite.state.mutators.triggers.animated = True

    # Tick 1: Should not advance frame yet due to delay=2
    sprite.animation.animate(sprite.state, sprite.properties)
    assert sprite.state.animation.tick == 1
    assert sprite.state.animation.frame == 0

    # Tick 2: Should advance frame and reset tick
    sprite.animation.animate(sprite.state, sprite.properties)
    assert sprite.state.animation.tick == 0
    assert sprite.state.animation.frame == 1

    # Non-animated trigger reset
    sprite.state.mutators.triggers.animated = False
    sprite.state.animation.frame = 2
    sprite.state.animation.tick = 1
    sprite.animation.animate(sprite.state, sprite.properties)
    assert sprite.state.animation.frame == 0
    assert sprite.state.animation.tick == 0


@pytest.mark.category_sheets
def test_sprite_animation(mock_asset):
    sprite = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
    )
    walk_action = sprite.properties.actions[Actions.WALK.value]
    walk_action.delay = 1
    walk_action.count = 3

    sprite.state.animation.action = Actions.WALK.value
    sprite.state.animation.frame = 0
    sprite.state.animation.tick = 0
    sprite.state.mutators.triggers.animated = True
    sprite.state.psyche.expression = AttachmentState(
        id="bubble",
        layer="0",
        icon="loquacity",
        offset=Position(0, 0),
        ttl=2,
    )

    # Tick 1: Frame advances, Expression TTL decays
    sprite.animation.animate(sprite.state, sprite.properties)
    assert sprite.state.psyche.expression is not None
    assert sprite.state.psyche.expression.ttl == 1

    # Tick 2: Frame advances, Expression TTL reaches 0 and is garbage collected
    sprite.animation.animate(sprite.state, sprite.properties)
    assert sprite.state.psyche.expression is None