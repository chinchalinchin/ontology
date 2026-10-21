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
    SheetState,
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