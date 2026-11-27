"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.instincts.combat

CombatInstinct implementation.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.game.logic.modules.cognition.instincts.base import Instinct
from app.game.logic.modules.maps import AnimationMap
from app.models.state.assets.sheets import Goal
from app.static.semantics import (
    Goals,
    Intentions,
    Relationships
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------


class CombatInstinct(Instinct):
    """
    Drive Instinct selecting the nearest visible living same-layer FOE as a
    Goals.TARGET when the Sprite has admissible ATTACK equipment.
    """

    def generate(self, sprite: Asset, board: Board) -> Optional[Goal]:
        """Generates a Goals.TARGET for the nearest visible living FOE."""
        state = sprite.state
        if state.mutators.parameters is None:
            return None

        relationships = state.memory.relationships
        if not relationships:
            return None

        # Gate hostile Goal acquisition on equipment admissibility for ATTACK
        if AnimationMap.action(
            state,
            board.equipment,
            intention=Intentions.ATTACK
        ) is None:
            return None

        sprite_pos = state.position
        sprite_layer = state.layer
        vision_radius = state.mutators.parameters.vision.radius

        best_name: Optional[str] = None
        best_state = None
        best_dist_sq: Optional[int] = None

        for other_name, other_state in board.characters().items():
            if other_name == sprite.name:
                continue
            if other_state.layer != sprite_layer:
                continue
            if other_state.mutators.triggers.dead:
                continue
            if relationships.get(other_name) != Relationships.FOE:
                continue
            if not geometry.nearby(
                other_state.position.x,
                other_state.position.y,
                sprite_pos.x,
                sprite_pos.y,
                vision_radius
            ):
                continue

            dx = other_state.position.x - sprite_pos.x
            dy = other_state.position.y - sprite_pos.y
            dist_sq = dx * dx + dy * dy
            if best_dist_sq is None or dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_name = other_name
                best_state = other_state

        if best_name is None or best_state is None:
            return None

        return Goal(
            name=best_name,
            category=Goals.TARGET,
            layer=best_state.layer,
            position=Position(
                x=best_state.position.x,
                y=best_state.position.y
            )
        )