"""
@workflow.main

# Ontology: app.asset.animations.core

Package for Asset Animation implementations.
"""
# Application Libraries
from app.assets.base import (
    Animation
)
from app.models.properties import (
    AssetProperties
)
from app.models.state import (
    AssetState
)

# --------------------------------------------------

class NoAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        return state