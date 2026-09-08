"""
# Ontology: tests.unit.test_app_assets_animations
"""
from unittest.mock import MagicMock
from app.assets.animations.core import (
    NoAnimation, 
    BinaryAnimation, 
    PersistentAnimation, 
    TemporaryAnimation, 
    StateAnimation, 
    SpriteAnimation
)
from app.models.state import (
    AssetState, 
    AnimationState, 
    SpriteState, 
    Psyche, 
    Mutators, 
    MutatorTriggers
)
from app.models.state.objects import AttachmentState

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

def test_persistent_animation():
    animation = PersistentAnimation()
    state = SpriteState(id="test")
    state.animation.frame = 0
    properties = MagicMock(count=3)
    
    animation.animate(state, properties)
    assert state.animation.frame == 1
    
    state.animation.frame = 2
    animation.animate(state, properties)
    assert state.animation.frame == 0

def test_temporary_animation():
    animation = TemporaryAnimation()
    state = SpriteState(id="test")
    state.animation.frame = 0
    properties = MagicMock(count=3)
    
    animation.animate(state, properties)
    assert state.animation.frame == 1
    
    # Should stop incrementing at count + 1 so RemoveMechanics can garbage collect
    state.animation.frame = 3
    animation.animate(state, properties)
    assert state.animation.frame == 4
    
    state.animation.frame = 4
    animation.animate(state, properties)
    assert state.animation.frame == 4

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