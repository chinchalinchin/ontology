"""
# Ontology: app.asset.animations.effects

Package for Effect Animation implementations.
"""
# Application Libraries
from app.config.enums import (
    Frequencies,
)
from app.assets.base import Animation
from app.models.properties import (
    EffectProperties,
)
from app.models.state import (
    EffectState
)

# --------------------------------------------------

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