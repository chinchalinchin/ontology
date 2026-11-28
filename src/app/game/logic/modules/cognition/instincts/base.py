"""
@domain.abstract
@domain.automata
@app.base
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.instincts.base

Abstract Instinct interface for stateless Goal generation.
"""
from __future__ import annotations

# Standard Libraries
from abc import ABC, abstractmethod
from typing import (
    Optional,
    Tuple,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.models.state.assets.sheets import Goal

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------


class Instinct(ABC):
    """
    Stateless low-level Goal constructor reacting to physiological and local
    environmental state.
    """

    @abstractmethod
    def generate(self, sprite: Asset, board: Board) -> Optional[Goal]:
        """Produces a candidate Goal for sprite, or None if not triggered."""
        pass

    @staticmethod
    def bounds(sprite: Asset, board: Board) -> Tuple[int, int]:
        """
        Returns the maximum valid (x, y) origin coordinates for sprite on its
        active Layer, accounting for sprite dimensions. Returns (0, 0) if the
        Layer reports unbounded/zero dimensions.
        """
        layer_sizes = board.size(sprite.state.layer)
        if not layer_sizes:
            return (0, 0)

        max_w = layer_sizes[0].w
        max_l = layer_sizes[0].l
        bound_w = max(0, max_w - sprite.dimensions.w) if max_w > 0 else 0
        bound_l = max(0, max_l - sprite.dimensions.l) if max_l > 0 else 0
        return (bound_w, bound_l)

    @classmethod
    def clamp(
        cls,
        raw_x: float,
        raw_y: float,
        sprite: Asset,
        board: Board
    ) -> Position:
        """
        Clamps a floating-point coordinate to valid integer Layer boundaries
        for sprite, preventing origins from spilling off map edges.
        """
        layer_sizes = board.size(sprite.state.layer)
        max_w = layer_sizes[0].w if layer_sizes else 0
        max_l = layer_sizes[0].l if layer_sizes else 0

        bound_w, bound_l = cls.bounds(sprite, board)
        ix = int(round(raw_x))
        iy = int(round(raw_y))

        clamped_x = max(0, min(ix, bound_w)) if max_w > 0 else max(0, ix)
        clamped_y = max(0, min(iy, bound_l)) if max_l > 0 else max(0, iy)
        return Position(x=clamped_x, y=clamped_y)