"""
# Ontology: tests.unit.test_app_assets_animations
"""
from unittest.mock import MagicMock
from app.assets.animations.core import (
    NoAnimation, 
    BinaryAnimation, 
    LifecycleAnimation, 
    StateAnimation, 
    SpriteAnimation
)
from app.config.enums import Lifecycles
from app.models.properties import EffectProperties, Lifecycle
from app.models.state import (
    AssetState, 
    AnimationState, 
    SpriteState, 
    EffectState,
    ReactableState,
    Psyche, 
    Mutators, 
    MutatorTriggers
)
from app.models.state.objects import AttachmentState
from libs.core.models import Dimensions


def test_no_animation():
    animation = NoAnimation()
    state = AssetState(id="test")
    assert animation.animate(state, None) == state


def test_binary_animation():
    animation = BinaryAnimation()
    state = MagicMock(switch=True, animation=AnimationState())
    animation.animate(state, None)
    
    # Settings ON/OFF mapped to frames 1 and 0
    assert state.animation.frame == 1
    
    state.switch = False
    animation.animate(state, None)
    assert state.animation.frame == 0


def test_lifecycle_animation_inactive():
    animation = LifecycleAnimation()
    lifecycle = Lifecycle(type=Lifecycles.CONTINUOUS.value, delay=1)
    properties = EffectProperties(dimensions=Dimensions(32, 32), count=4, lifecycle=lifecycle)
    state = EffectState(id="effect-1", active=False, animation=AnimationState(frame=2, tick=3))

    animation.animate(state, properties)
    assert state.animation.frame == 0
    assert state.animation.tick == 0


def test_lifecycle_animation_continuous():
    animation = LifecycleAnimation()
    lifecycle = Lifecycle(type=Lifecycles.CONTINUOUS.value, delay=2)
    properties = EffectProperties(dimensions=Dimensions(32, 32), count=3, lifecycle=lifecycle)
    state = EffectState(id="torch", active=True, animation=AnimationState(frame=0, tick=0))

    # Tick 1: Pacing delay threshold not reached
    animation.animate(state, properties)
    assert state.animation.tick == 1
    assert state.animation.frame == 0

    # Tick 2: Delay reached, frame increments
    animation.animate(state, properties)
    assert state.animation.tick == 0
    assert state.animation.frame == 1

    # Advance to end of cycle and verify modulo wrap
    state.animation.frame = 2
    state.animation.tick = 1
    animation.animate(state, properties)
    assert state.animation.tick == 0
    assert state.animation.frame == 0


def test_lifecycle_animation_temporary_non_persisting():
    animation = LifecycleAnimation()
    lifecycle = Lifecycle(type=Lifecycles.TEMPORARY.value, delay=1, persist=False)
    properties = EffectProperties(dimensions=Dimensions(32, 32), count=3, lifecycle=lifecycle)
    state = EffectState(id="slash-spark", active=True, animation=AnimationState(frame=0, tick=0))

    # Advances through frames up to count
    animation.animate(state, properties)
    assert state.animation.frame == 1

    state.animation.frame = 3
    animation.animate(state, properties)
    # Beyond count, frame advancement halts for garbage collection
    assert state.animation.frame == 3


def test_lifecycle_animation_temporary_persisting():
    animation = LifecycleAnimation()
    lifecycle = Lifecycle(type=Lifecycles.TEMPORARY.value, delay=1, persist=True)
    properties = EffectProperties(dimensions=Dimensions(32, 32), count=3, lifecycle=lifecycle)
    state = EffectState(id="dummy", active=True, animation=AnimationState(frame=0, tick=0))

    state.animation.frame = 1
    animation.animate(state, properties)
    assert state.animation.frame == 2

    # Clamps to count - 1 when persist=True
    animation.animate(state, properties)
    assert state.animation.frame == 2


def test_lifecycle_animation_periodic():
    animation = LifecycleAnimation()
    lifecycle = Lifecycle(type=Lifecycles.PERIODIC.value, delay=2, frequency=8)
    properties = EffectProperties(dimensions=Dimensions(32, 32), count=2, lifecycle=lifecycle)
    state = EffectState(id="geyser", active=True, animation=AnimationState(frame=0, tick=0))

    # Active duration = 2 * 2 = 4 ticks. Frame 0 during ticks 0-1
    animation.animate(state, properties) # tick 1
    assert state.animation.frame == 0

    animation.animate(state, properties) # tick 2
    assert state.animation.frame == 1

    animation.animate(state, properties) # tick 3
    assert state.animation.frame == 1

    animation.animate(state, properties) # tick 4 -> idle resting frame
    assert state.animation.frame == 0

    state.animation.tick = 7
    animation.animate(state, properties) # tick 8 reaches frequency limit
    assert state.animation.tick == 0
    assert state.animation.frame == 0


def test_lifecycle_animation_cooldown_and_reset():
    animation = LifecycleAnimation()
    lifecycle = Lifecycle(type=Lifecycles.TEMPORARY.value, delay=1, cooldown=60, persist=True)
    properties = EffectProperties(dimensions=Dimensions(32, 32), count=3, lifecycle=lifecycle)
    state = ReactableState(id="dummy", active=True, cooldown=2, animation=AnimationState(frame=2, tick=0))

    # Frame matches clamp limit (count - 1): decrement cooldown
    animation.cooldown(state, properties)
    assert state.cooldown == 1
    assert state.active is True

    # Cooldown expires: resets state and restores base cooldown
    animation.cooldown(state, properties)
    assert state.cooldown == 60
    assert state.active is False
    assert state.animation.frame == 0
    assert state.animation.tick == 0


def test_state_animation():
    animation = StateAnimation()
    state = SpriteState(id="test")
    state.animation = AnimationState(action="walk", frame=0, tick=0)
    state.mutators = Mutators(triggers=MutatorTriggers(animated=True))
    
    action_prop = MagicMock(delay=2, count=3)
    properties = MagicMock(actions={"walk": action_prop})
    
    # Tick 1: Should not advance frame yet due to delay=2
    animation.animate(state, properties)
    assert state.animation.tick == 1
    assert state.animation.frame == 0
    
    # Tick 2: Should advance frame and reset tick
    animation.animate(state, properties)
    assert state.animation.tick == 0
    assert state.animation.frame == 1
    
    # Test non-animated trigger reset
    state.mutators.triggers.animated = False
    state.animation.frame = 2
    state.animation.tick = 1
    animation.animate(state, properties)
    assert state.animation.frame == 0
    assert state.animation.tick == 0


def test_sprite_animation():
    animation = SpriteAnimation()
    state = SpriteState(id="npc")
    state.animation = AnimationState(action="walk", frame=0, tick=0)
    state.mutators = Mutators(triggers=MutatorTriggers(animated=True))
    state.psyche = Psyche(
        expression=AttachmentState(id="bubble", layer="0", icon="loquacity", offset=None, ttl=2)
    )
    
    action_prop = MagicMock(delay=1, count=3)
    properties = MagicMock(actions={"walk": action_prop})
    
    # Tick 1: Frame advances, Expression TTL decays
    animation.animate(state, properties)
    assert state.psyche.expression is not None
    assert state.psyche.expression.ttl == 1
    
    # Tick 2: Frame advances, Expression TTL reaches 0 and is garbage collected
    animation.animate(state, properties)
    assert state.psyche.expression is None