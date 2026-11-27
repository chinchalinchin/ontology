"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.instincts.explore

ExploreInstinct implementation with directional inertia (Correlated Random Walk).
"""
from __future__ import annotations

# Standard Libraries
import math
import random
from typing import (
    Dict,
    Optional,
    Tuple,
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
    Directions,
    Goals,
    Intentions
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

HEADING_ANGLES: Dict[Directions, float] = {
    Directions.RIGHT: 0.0,
    Directions.DOWN: math.pi / 2.0,
    Directions.LEFT: math.pi,
    Directions.UP: -math.pi / 2.0,
}

# -----------------------------------------------------


class ExploreInstinct(Instinct):
    """
    Exploratory fallback Instinct generating bounded Goals.POSITION wander
    coordinates using a forward-biased Correlated Random Walk (von Mises
    angular inertia) anchored to the Sprite's current velocity or facing.
    """
    kappa: float
    attempts: int
    _headings: Dict[str, Tuple[float, Directions]]

    def __init__(self, kappa: float = 2.0, attempts: int = 8):
        self.kappa = kappa
        self.attempts = attempts
        self._headings = {}

    def _heading(self, sprite: Asset) -> float:
        """
        Resolves the Sprite's inertial heading angle in radians.
        Prioritizes live velocity when moving, preserves the cached continuous
        wander angle across IDLE pauses when cardinal facing is unchanged, and
        otherwise initializes from sprite.state.animation.direction.
        """
        vel = sprite.state.velocity
        if math.hypot(vel.vx, vel.vy) > 1e-3:
            return math.atan2(vel.vy, vel.vx)

        facing = sprite.state.animation.direction
        cached = self._headings.get(sprite.name)
        if cached is not None and cached[1] == facing:
            return cached[0]

        return HEADING_ANGLES.get(facing, 0.0)

    def _sample(
        self,
        sprite: Asset,
        board: Board,
        heading: float,
        kappa: float,
        min_radius: int,
        max_radius: int,
        action_radius: int
    ) -> Optional[Tuple[Position, float]]:
        """Samples a single Layer-clamped dry candidate outside action.radius."""
        state = sprite.state
        angle = random.vonmisesvariate(heading, kappa)
        radius = random.uniform(min_radius, max_radius)

        candidate = self.clamp(
            state.position.x + math.cos(angle) * radius,
            state.position.y + math.sin(angle) * radius,
            sprite,
            board
        )

        # Reject candidates clamped too close to current position (wall/corner)
        if geometry.nearby(
            state.position.x,
            state.position.y,
            candidate.x,
            candidate.y,
            action_radius
        ):
            return None

        # Avoid sampling wander destinations inside ground-level Fluid corridors
        if (
            state.layer is not None
            and sprite.elevation == 0
            and board.fluid(state.layer, candidate)
        ):
            return None

        return (candidate, angle)

    def generate(self, sprite: Asset, board: Board) -> Optional[Goal]:
        """Generates a forward-weighted Goals.POSITION wander Goal."""
        state = sprite.state
        if state.mutators.parameters is None:
            return None

        vision_radius = max(1, state.mutators.parameters.vision.radius)
        action_radius = state.mutators.parameters.action.radius
        min_radius = min(
            vision_radius,
            max(action_radius * 2, int(vision_radius * 0.4))
        )

        heading = self._heading(sprite)
        chosen: Optional[Tuple[Position, float]] = None

        # First pass: forward-biased samples; final 2 retries relax kappa -> 0
        # so Sprites facing a wall or riverbank turn smoothly instead of stalling
        relax_at = max(1, self.attempts - 2)
        for attempt in range(self.attempts):
            effective_kappa = self.kappa if attempt < relax_at else 0.0
            chosen = self._sample(
                sprite=sprite,
                board=board,
                heading=heading,
                kappa=effective_kappa,
                min_radius=min_radius,
                max_radius=vision_radius,
                action_radius=action_radius
            )
            if chosen is not None:
                break

        if chosen is None:
            # Ultimate fallback: uniform clamped point
            angle = random.uniform(-math.pi, math.pi)
            radius = random.uniform(min_radius, vision_radius)
            target_pos = self.clamp(
                state.position.x + math.cos(angle) * radius,
                state.position.y + math.sin(angle) * radius,
                sprite,
                board
            )
        else:
            target_pos, angle = chosen

        next_dir = AnimationMap.direction(state.position, target_pos)
        self._headings[sprite.name] = (angle, next_dir)

        return Goal(
            name=Intentions.WANDER.value,
            category=Goals.POSITION,
            layer=state.layer,
            position=target_pos
        )