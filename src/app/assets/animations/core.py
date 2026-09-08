"""
# Ontology: app.asset.animations.core

Package for Asset Animation implementations.
"""
# Application Libraries
import app.config.settings as settings
from app.assets.base import Animation
from app.models.properties import AssetProperties, SheetProperties
from app.models.state import AssetState, SpriteState

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
        state.animation.frame = settings.ON if state.switch else settings.OFF
        return state

        
class PersistentAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame += 1

        if state.animation.frame >= properties.count:
            state.animation.frame = 0

        return state

    
class TemporaryAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        if state.animation.frame <= properties.count:
            state.animation.frame += 1

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
