"""
@domain.concrete
@app.asset
@asset.animation
@category.widgets
@workflow.menus

# Ontology: Source - app.asset.animations.widgets

Widget Animation implementations.
"""
# Application Libraries
from app.assets.base import Animation
from app.models.properties import WidgetProperties
from app.models.state import AssetState

# --------------------------------------------------

class TraversalAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: WidgetProperties) -> AssetState:
        """
        """
        state.animation.action = state.status
        return state

# --------------------------------------------------

class MeterAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: WidgetProperties) -> AssetState:
        """
        """
        if getattr(state, 'unit', 0) > 0:
            pct = state.reading / state.unit
        else:
            pct = 0.0
        res = int(round(pct * 100))
        state.animation.frame = max(0, min(100, res))
        return state