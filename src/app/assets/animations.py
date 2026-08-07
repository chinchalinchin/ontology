"""
# Ontology: Animations

Package for Asset Animation implementations.
"""
# Application Libraries
import app.config.constants as constants
from app.assets.base import Animation
from app.models.properties import AssetProperties
from app.models.state import AssetState

class BinaryAnimation(Animation):

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame = constants.ON if state.switch else constants.OFF
        return state
        
class PersistentAnimation(Animation):

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame += 1

        if state.animation.frame > properties.count:
            state.animation.frame = 0

        return state
    
class TemporaryAnimation(Animation):

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        if state.animation.frame <= properties.count:
            state.animation.frame += 1

        return state

class StateAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame += 1

        if state.animation.frame > properties.actions[state.animation.action].count:
            state.animation.frame = 0

        return state