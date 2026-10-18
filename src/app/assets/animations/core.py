"""
# Ontology: app.asset.animations.core

Package for Asset Animation implementations.
"""
# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    Frequencies,
    Switches
)
from app.assets.base import Animation
from app.models.properties import (
    AssetProperties, 
    EffectProperties,
    SheetProperties
)
from app.models.state import (
    AssetState, 
    SpriteState,
    EffectState
)

class NoAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        return state


class BinaryAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame = Switches.ON.value if state.switch else Switches.OFF.value
        return state


class FrequencyAnimation(Animation):
    """
    """

    def cooldown(self, state: EffectState, properties: EffectProperties) -> EffectState:
        """
        """
        limit = (
            properties.count - 1 
            if properties.frequency.persist else 
            properties.count
        )
        if state.animation.frame >= limit:
            state.cooldown -= 1
            if state.cooldown <= 0:
                state.active = False
                state.animation.frame = 0
                state.animation.tick = 0
                state.cooldown = properties.frequency.cooldown
        return state


    def animate(self, state: EffectState, properties: EffectProperties) -> EffectState:
        """
        """
        frequency = properties.frequency
        anim = state.animation
        anim.tick += 1

        if not state.active:
            anim.frame = 0
            anim.tick = 0
            return state
        
        if frequency.type == Frequencies.CONTINUOUS.value:
            if anim.tick >= frequency.delay:
                anim.tick = 0
                anim.frame = (anim.frame + 1) % properties.count

        elif frequency.type == Frequencies.TEMPORARY.value:
            limit = properties.count - 1 if frequency.persist else properties.count
            if anim.frame < limit:
                if anim.tick >= frequency.delay:
                    anim.tick = 0
                    anim.frame += 1

        elif frequency.type == Frequencies.PERIODIC.value:
            active_duration = properties.count * frequency.delay
            if anim.tick < active_duration:
                anim.frame = anim.tick // frequency.delay
            else:
                anim.frame = 0
            
            if anim.tick >= max(frequency.frequency, active_duration):
                anim.tick = 0
                anim.frame = 0

        return state

    
class StateAnimation(Animation):
    """
    Advances frame based on configured action delay.
    """
    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        action_props = properties.actions[state.animation.action]
        state.animation.tick += 1

        # Only advance the frame if the tick accumulator reaches the delay threshold
        if state.animation.tick >= action_props.delay:
            state.animation.tick = 0
            state.animation.frame += 1

            if state.animation.frame >= action_props.count:
                state.animation.frame = 0

        return state


class SpriteAnimation(StateAnimation):
    """
    """
    def animate(self, state: SpriteState, properties: SheetProperties):
        if not state.mutators.triggers.animated:
            state.animation.frame = 0
            state.animation.tick = 0
            return state

        super().animate(state, properties)

        # NOTE: handle players
        if getattr(state, 'psyche', None) is None:
            return state
        
        if state.psyche.expression:
            state.psyche.expression.ttl -= 1
            if state.psyche.expression.ttl <= 0:
                state.psyche.expression = None

