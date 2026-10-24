"""
@domain.concrete
@app.asset
@asset.animation
@workflow.intentions
@workflow.combat

# Ontology: Source - app.asset.animations.sheets

Sheet Animation implementations.
"""
# Application Libraries
from app.assets.animations.core import StateAnimation
from app.models.properties import SheetProperties
from app.models.state import SpriteState

# --------------------------------------------------

class SpriteAnimation(StateAnimation):
    """
    """
    def animate(self, state: SpriteState, properties: SheetProperties) -> SpriteState:
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

        return state

