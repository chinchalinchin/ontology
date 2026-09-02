"""
# Ontology: app.asset.animations.core

Package for Asset Animation implementations.
"""
# Application Libraries
import app.config.settings as settings
from app.config.enums import Statuses
from app.assets.base import Animation
from app.models.properties import AssetProperties
from app.models.state import AssetState

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
        if state.mutators and state.mutators.triggers:
            if not state.mutators.triggers.animated:
                state.animation.frame = 0
                state.animation.tick = 0
                return state

        action_props = properties.actions[state.animation.action]
        delay = getattr(action_props, 'delay', 1)

        state.animation.tick += 1

        # Only advance the frame if the tick accumulator reaches the delay threshold
        if state.animation.tick >= delay:
            state.animation.tick = 0
            state.animation.frame += 1

            if state.animation.frame >= action_props.count:
                state.animation.frame = 0

        return state