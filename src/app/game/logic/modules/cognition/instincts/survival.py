"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.instincts.survival

Survival-tier Instincts (FleeInstinct).
"""
from __future__ import annotations

# Standard Libraries
import math
from typing import (
    List,
    Optional,
    Tuple,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.game.logic.modules.cognition.instincts.base import Instinct
from app.models.state.assets.sheets import Goal
from app.static.semantics import (
    Directions,
    Goals,
    Intentions,
    Relationships
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

OPPOSITE_HEADING = {
    Directions.UP: (0.0, 1.0),
    Directions.DOWN: (0.0, -1.0),
    Directions.LEFT: (1.0, 0.0),
    Directions.RIGHT: (-1.0, 0.0),
}

CARDINAL_FALLBACKS: Tuple[Tuple[float, float], ...] = (
    (1.0, 0.0),
    (-1.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
)

# -----------------------------------------------------


class FleeInstinct(Instinct):
    """
    Survival Instinct active whenever triggers.frightened is True.
    Derives a threat centroid from visible living same-layer FOE or ATTACKing
    characters (falling back safely when frightened solely by low health) and
    projects a Layer-clamped flee coordinate with zero-delta and tangential
    corner-deflection fallbacks (B072).
    """

    @staticmethod
    def _threats(sprite: Asset, board: Board) -> List[Position]:
        """Collects positions of visible living same-layer FOE/ATTACKing threats."""
        state = sprite.state
        sprite_pos = state.position
        sprite_layer = state.layer
        relationships = state.memory.relationships

        vision_radius = state.mutators.parameters.vision.radius
        fear_radius = (
            state.mutators.parameters.fear.radius
            if state.mutators.parameters.fear is not None
            else vision_radius
        )
        search_radius = max(vision_radius, fear_radius)

        threats: List[Position] = []
        for other_name, other_state in board.characters().items():
            if other_name == sprite.name:
                continue
            if other_state.layer != sprite_layer:
                continue
            if other_state.mutators.triggers.dead:
                continue
            if not geometry.nearby(
                other_state.position.x,
                other_state.position.y,
                sprite_pos.x,
                sprite_pos.y,
                search_radius
            ):
                continue

            is_foe = relationships.get(other_name) == Relationships.FOE
            is_attacking = other_state.intention == Intentions.ATTACK
            if is_foe or is_attacking:
                threats.append(other_state.position)

        return threats

    def _fallback_direction(
        self,
        sprite: Asset,
        board: Board
    ) -> Tuple[float, float]:
        """
        Selects a safe unit direction when no threat is visible or threat delta
        vanishes: steers toward Layer interior, falling back to opposite facing.
        """
        bound_w, bound_l = self.bounds(sprite, board)
        if bound_w > 0 or bound_l > 0:
            dx = (bound_w / 2.0) - sprite.state.position.x
            dy = (bound_l / 2.0) - sprite.state.position.y
            mag = math.hypot(dx, dy)
            if mag > 0.0:
                return (dx / mag, dy / mag)

        return OPPOSITE_HEADING.get(
            sprite.state.animation.direction,
            (1.0, 0.0)
        )

    def _deflect(
        self,
        ux: float,
        uy: float,
        flee_distance: int,
        action_radius: int,
        ref_x: float,
        ref_y: float,
        sprite: Asset,
        board: Board
    ) -> Optional[Position]:
        """
        Evaluates tangential and cardinal escape directions when the primary
        flee coordinate clamps inside action.radius (e.g. map corners), picking
        the candidate outside action.radius furthest from (ref_x, ref_y).
        """
        sprite_pos = sprite.state.position
        directions: Tuple[Tuple[float, float], ...] = (
            (-uy, ux),
            (uy, -ux),
            *CARDINAL_FALLBACKS,
        )

        best_pos: Optional[Position] = None
        best_score: float = -1.0

        for tx, ty in directions:
            candidate = self.clamp(
                sprite_pos.x + (tx * flee_distance),
                sprite_pos.y + (ty * flee_distance),
                sprite,
                board
            )
            if geometry.nearby(
                sprite_pos.x,
                sprite_pos.y,
                candidate.x,
                candidate.y,
                action_radius
            ):
                continue

            dx = candidate.x - ref_x
            dy = candidate.y - ref_y
            score = dx * dx + dy * dy
            if score > best_score:
                best_score = score
                best_pos = candidate

        return best_pos

    def generate(self, sprite: Asset, board: Board) -> Optional[Goal]:
        """Generates a synthetic escape Goals.POSITION when frightened."""
        state = sprite.state
        if not state.mutators.triggers.frightened:
            return None

        if state.mutators.parameters is None:
            return None

        sprite_pos = state.position
        vision_radius = state.mutators.parameters.vision.radius
        action_radius = state.mutators.parameters.action.radius
        flee_distance = max(vision_radius, action_radius * 2, 1)

        threats = self._threats(sprite, board)
        if threats:
            ref_x = sum(p.x for p in threats) / len(threats)
            ref_y = sum(p.y for p in threats) / len(threats)
            dx = sprite_pos.x - ref_x
            dy = sprite_pos.y - ref_y
            mag = math.hypot(dx, dy)
            if mag > 0.0:
                ux, uy = dx / mag, dy / mag
            else:
                ux, uy = self._fallback_direction(sprite, board)
        else:
            ref_x = float(sprite_pos.x)
            ref_y = float(sprite_pos.y)
            ux, uy = self._fallback_direction(sprite, board)

        target_pos = self.clamp(
            sprite_pos.x + (ux * flee_distance),
            sprite_pos.y + (uy * flee_distance),
            sprite,
            board
        )

        # Corner deflection: prevent immediate arrival completion inside action.radius
        if geometry.nearby(
            sprite_pos.x,
            sprite_pos.y,
            target_pos.x,
            target_pos.y,
            action_radius
        ):
            deflected = self._deflect(
                ux=ux,
                uy=uy,
                flee_distance=flee_distance,
                action_radius=action_radius,
                ref_x=ref_x,
                ref_y=ref_y,
                sprite=sprite,
                board=board
            )
            if deflected is not None:
                target_pos = deflected

        return Goal(
            name=Intentions.ESCAPE.value,
            category=Goals.POSITION,
            layer=state.layer,
            position=target_pos
        )