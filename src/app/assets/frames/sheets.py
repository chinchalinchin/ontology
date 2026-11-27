"""
@domain.concrete
@app.asset
@asset.frame
@category.sheets

# Ontology: Source - app.assets.frames.sheets

Package for Sheet Frame implementations.
"""
# Standard Libraries
from typing import (
    Dict,
    List,
    Tuple
)
import logging

# Application Libraries
import app.static.settings as settings
from app.static.semantics import (
    Actions,
    Intentions,
    ExpressionsPalette,
)
from app.assets.base import Frame
from app.models.state import (
    CharacterState,
    SheetState,
    SpriteState
)
from app.models.properties import (
    SheetProperties,
)

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------


class StateFrame(Frame):
    """
    ## StateFrame

    TODO: should be called an "ActionFrame", since it's using the action field to generate the animation.
    """

    def keys(
        self,
        id: str,
        state: SheetState
    ) -> List[Tuple[str, int, int]]:
        """Generates the base (action, direction, frame) Registry key for a Sheet."""
        return [(settings.SEPARATOR.join([
            id,
            state.animation.action,
            state.animation.direction,
            str(state.animation.frame)
        ]), 0, 0)]

    def index(
        self,
        id: str,
        properties: SheetProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        """Partitions a Sheet atlas into (action, direction, frame) crop regions."""
        w = properties.dimensions.w
        l = properties.dimensions.l
        crops: Dict[str, Tuple[int, int, int, int]] = {}

        # Handle dict format since this goes through dataclasses.asdict()
        for action, action_prop in properties.actions.items():
            for direction, dir_prop in action_prop.directions.items():
                row = dir_prop.row
                count = action_prop.count
                for f in range(count):
                    frame_key = settings.SEPARATOR.join([
                        id,
                        action,
                        direction,
                        str(f)
                    ])
                    crops[frame_key] = (f * w, row * l, w, l)
        return crops


# -------------------------------------------------------------------------------------


class CharacterFrame(StateFrame):
    """
    ## CharacterFrame

    Frame component for intentional Characters (Players and base for Sprites)
    that yields a strict Z-indexed stack of base and active equipment keys.
    """

    def keys(
        self,
        id: str,
        state: CharacterState
    ) -> List[Tuple[str, int, int]]:
        """Generates Z-ordered base and active equipment frame keys."""
        # Start with the base Persona frame key
        frame_keys = super().keys(id, state)

        # Iterate over active equipment in strict Z-index order:
        # Base -> Armor -> Utility -> Tool (MINE) -> Weapon (ATTACK) -> Shield
        eq = state.slots.equipment
        is_implement_action = state.animation.action not in (
            Actions.WALK,
            Actions.DIE
        )
        active_slots = (
            eq.armor,
            eq.utility,
            eq.tool if (
                is_implement_action
                and state.intention == Intentions.MINE
            ) else None,
            eq.weapon if (
                is_implement_action
                and state.intention == Intentions.ATTACK
            ) else None,
            eq.shield,
        )
        for eq_key in active_slots:
            if eq_key:
                frame_keys.extend(super().keys(eq_key, state))

        if state.intention == Intentions.ATTACK:
            logger.debug(f"{type(self).__name__} generated keys: {frame_keys}")

        return frame_keys


# -------------------------------------------------------------------------------------


class SpriteFrame(CharacterFrame):
    """
    ## SpriteFrame

    Specialized Frame component for autonomous Sprites that appends active
    Psyche expression bubbles above the CharacterFrame equipment stack.
    """

    def keys(
        self,
        id: str,
        state: SpriteState
    ) -> List[Tuple[str, int, int]]:
        """Generates CharacterFrame keys plus any active Psyche expression overlay."""
        frame_keys = super().keys(id, state)

        if state.psyche.expression is not None:
            expr = state.psyche.expression
            expr_key = settings.SEPARATOR.join([
                ExpressionsPalette.BUBBLES,
                expr.icon
            ])
            frame_keys.append((expr_key, expr.offset.x, expr.offset.y))

        return frame_keys