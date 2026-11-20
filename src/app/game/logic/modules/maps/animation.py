"""
@domain.logic
@app.module
@modality.intention
@workflow.combat

# Ontology: Source - app.game.maps.animation

Animation Maps for mapping SpriteState to Equipment Frames.
"""
# Standard Libraries
from typing import Optional

# Application Libraries
from app.static.semantics import (
    Actions,
    Directions,
    Intentions,
    StaticIntentions
)
from app.models.groups import EquipmentGroup
from app.models.state import SheetState

# Cython Libraries
from libs.core.models import Position


class AnimationMap:
    """
    Stateless projection from Intentional/Spatial state and Equipment slots
    into Animation Space (Action, Direction). Acts as the Equipment admissibility
    gate for equipment-bound Intentions.
    """

    @staticmethod
    def action(
        state: SheetState,
        equipment: EquipmentGroup,
        intention: Optional[str] = None
    ) -> Optional[Actions]:
        """
        Resolves a Sheet Intention and slotted Equipment to its Animation Action.
        Returns None when an equipment-gated Intention (ATTACK, MINE, BUILD) lacks
        the required slotted Equipment or configured Actions.

        - state: sheet or sprite state
        - equipment: board equipment group
        - intention: optional candidate intention override for transition gating
        """
        target_intention = intention if intention is not None else state.intention

        if target_intention in StaticIntentions:
            return Actions.WALK

        if target_intention in (
            Intentions.ATTACK,
            Intentions.MINE,
            Intentions.BUILD
        ):
            if not state.slots:
                return None

            eq = state.slots.equipment
            if target_intention == Intentions.ATTACK:
                asset = equipment.weapons.get(eq.weapon) if eq.weapon else None
            elif target_intention == Intentions.MINE:
                asset = equipment.tools.get(eq.tool) if eq.tool else None
            else:
                asset = equipment.utilities.get(eq.utility) if eq.utility else None

            if asset and asset.properties.actions:
                return next(iter(asset.properties.actions))

            return None

        if target_intention in (
            Intentions.INTERACT,
            Intentions.WANDER,
            Intentions.FIND,
            Intentions.FOLLOW,
            Intentions.HUNT,
            Intentions.ESCAPE,
            Intentions.RETURN
        ):
            return Actions.WALK

        return Actions.WALK

    @staticmethod
    def direction(position: Position, target: Position) -> str:
        """
        Projects a source coordinate and target coordinate to a cardinal Direction.
        """
        dx = target.x - position.x
        dy = target.y - position.y

        # In graphics coordinates, larger y is physically lower.
        if dy > dx:
            # Lower than both diagonals means it is physically DOWN
            return Directions.DOWN if dy > -dx else Directions.LEFT

        # Higher than both diagonals means it is physically UP
        return Directions.RIGHT if dy > -dx else Directions.UP