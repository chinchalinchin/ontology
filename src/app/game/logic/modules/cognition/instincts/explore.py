"""
@domain.concrete
@domain.logic
@app.module
@category.sheets
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.instincts.explore

Exploratory fallback Instincts (WanderInstinct).
"""
from __future__ import annotations

# Standard Libraries
import random
from typing import (
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.game.logic.modules.cognition.instincts.base import Instinct
from app.models.state.assets.sheets import Goal
from app.static.semantics import (
    Goals,
    Intentions
)

# -----------------------------------------------------


class WanderInstinct(Instinct):
    """
    Exploratory fallback Instinct sampling a Layer-clamped coordinate within
    vision.radius as a Goals.POSITION ('wander'). Executes strictly in IDLE
    so wander -> idle exits remain reachable (B075).
    """

    def generate(self, sprite: Asset, board: Board) -> Optional[Goal]:
        """Samples a Layer-bounded wander coordinate strictly while IDLE."""
        state = sprite.state
        if state.intention != Intentions.IDLE:
            return None

        if state.mutators.parameters is None:
            return None

        vision_radius = state.mutators.parameters.vision.radius
        offset_x = random.randint(-vision_radius, vision_radius)
        offset_y = random.randint(-vision_radius, vision_radius)

        target_pos = self.clamp(
            state.position.x + offset_x,
            state.position.y + offset_y,
            sprite,
            board
        )

        return Goal(
            name=Intentions.WANDER.value,
            category=Goals.POSITION,
            layer=state.layer,
            position=target_pos
        )