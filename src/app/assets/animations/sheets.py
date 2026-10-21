"""
# Ontology: app.asset.animations.sheets

Package for Sheet Animation implementations.
"""
# Application Libraries
from app.assets.base import Animation
from app.models.properties import (
    SheetProperties
)
from app.models.state import (
    AssetState, 
    SpriteState,
)

# --------------------------------------------------

class StateAnimation(Animation):
    """
    Advances frame based on configured action delay.
    """
    def animate(self, state: AssetState, properties: SheetProperties) -> AssetState:
        action_props = properties.actions[state.animation.action]
        state.animation.tick += 1

        # Only advance the frame if the tick accumulator reaches the delay threshold
        if state.animation.tick >= action_props.delay:
            state.animation.tick = 0
            state.animation.frame += 1

            if state.animation.frame >= action_props.count:
                state.animation.frame = 0

        return state

# --------------------------------------------------

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

