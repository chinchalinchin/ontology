"""
@domain.concrete
@app.asset
@asset.animation
@category.sheets

# Ontology: Source - app.assets.animations.sheets

Sheet Animation implementations.
"""
# Application Libraries
from app.assets.animations.core import StateAnimation
from app.models.properties import SheetProperties
from app.models.state import (
    CharacterState,
    SpriteState
)

# -------------------------------------------------------------------------------------


class CharacterAnimation(StateAnimation):
    """
    Animation strategy for intentional Characters (Players and base for
    Sprites). Resets Action frame progression when triggers.animated is False.
    """

    def animate(
        self,
        state: CharacterState,
        properties: SheetProperties
    ) -> CharacterState:
        """Advances the Action frame when animated, or resets to idle frame 0."""
        if not state.mutators.triggers.animated:
            state.animation.frame = 0
            state.animation.tick = 0
            return state

        return super().animate(state, properties)

# -------------------------------------------------------------------------------------

class SpriteAnimation(CharacterAnimation):
    """
    Animation strategy for autonomous Sprites. Delegates Action progression to
    CharacterAnimation and decays Psyche expression TTL unconditionally.
    """

    def animate(
        self,
        state: SpriteState,
        properties: SheetProperties
    ) -> SpriteState:
        """Updates Action frame progression and ticks down active expression TTL."""
        super().animate(state, properties)

        # Expression TTL decays unconditionally regardless of triggers.animated
        if state.psyche.expression is not None:
            state.psyche.expression.ttl -= 1
            if state.psyche.expression.ttl <= 0:
                state.psyche.expression = None

        return state