"""
@domain.concrete
@app.core
@asset.animation

# Ontology: Source - app.asset.animations.core

Core Animation implementations.
"""
# Application Libraries
from app.assets.base import Animation
from app.models.properties import (
    AssetProperties,
    SheetProperties
)
from app.models.state import (
    AssetState,
    SheetState
)

# --------------------------------------------------

class NoAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        return state

class StateAnimation(Animation):
    """
    Advances frame based on configured action delay.
    """
    def animate(self, state: SheetState, properties: SheetProperties) -> AssetState:
        action_props = properties.actions[state.animation.action]
        state.animation.tick += 1

        # Only advance the frame if the tick accumulator reaches the delay threshold
        if state.animation.tick >= action_props.delay:
            state.animation.tick = 0
            state.animation.frame += 1

            if state.animation.frame >= action_props.count:
                state.animation.frame = 0

        return state