"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.outcomes

Abstract PortalLocator and OutcomeHandler interfaces, concrete lifecycle
implementations, and OutcomeResolver dispatcher.
"""
from __future__ import annotations

# Standard Libraries
from abc import ABC, abstractmethod
import logging
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
from app.game.logic.modules.cognition.base import Locator
from app.models.state.assets.sheets import Goal
from app.static.semantics import (
    AssetInstances,
    Goals,
    Outcomes,
    Responses
)

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------

class DoorLocator(Locator):
    """
    Locates Doors (both LayerProjections.IN and
    LayerProjections.OUT) on the Sprite's current Layer. Prioritizes the
    nearest mapped door in memory.doors targeting goal.layer, falling back
    to the nearest unmapped door within vision.radius.
    """

    @staticmethod
    def _distance_sq(p1: Position, p2: Position) -> int:
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return dx * dx + dy * dy

    def locate(self, sprite: Asset, board: Board) -> Optional[Asset]:
        goal = sprite.state.goal
        if not goal or sprite.state.layer is None:
            return None

        doors = board.instances(AssetInstances.DOORS, sprite.state.layer)
        if not doors:
            return None

        sprite_pos = sprite.state.position
        memory_doors = sprite.state.memory.doors

        # 1. Prioritize nearest mapped door known to reach goal.layer
        mapped_candidates = [
            portal for portal in doors
            if memory_doors.get(portal.name) == goal.layer
        ]
        if mapped_candidates:
            return min(
                mapped_candidates,
                key=lambda d: self._distance_sq(sprite_pos, d.state.position)
            )

        # 2. Fall back to nearest unmapped door within vision.radius
        vision_radius = sprite.state.mutators.parameters.vision.radius
        unmapped_candidates = [
            portal for portal in doors
            if (
                portal.name not in memory_doors
                or memory_doors[portal.name] == sprite.state.layer
            )
            and geometry.nearby(
                portal.state.position.x,
                portal.state.position.y,
                sprite_pos.x,
                sprite_pos.y,
                vision_radius
            )
        ]
        if unmapped_candidates:
            return min(
                unmapped_candidates,
                key=lambda d: self._distance_sq(sprite_pos, d.state.position)
            )

        return None


# -----------------------------------------------------


class OutcomeHandler(ABC):
    """
    Abstract interface for executing the Goal lifecycle transition associated
    with a matched GoalRule outcome.
    """

    @abstractmethod
    def apply(
        self,
        rule: GoalRule,
        sprite: Asset,
        board: Board,
        response: ResponseOperators,
        reflex: ReflexOperators,
        spawn: ExpressionSpawner
    ) -> None:
        """Applies Memory responses, Psyche reflexes, and active Goal updates."""
        pass


class TerminalOutcome(OutcomeHandler):
    """
    Terminal lifecycle handler executing configured Responses and Reflexes
    and clearing the active Goal to None (used for COMPLETE and LOST).
    """

    def apply(
        self,
        rule: GoalRule,
        sprite: Asset,
        board: Board,
        response: ResponseOperators,
        reflex: ReflexOperators,
        spawn: ExpressionSpawner
    ) -> None:
        goal = sprite.state.goal
        response.resolve(rule.responses, goal, sprite.state.memory)
        reflex.resolve(rule.reflexes, goal, sprite.state.psyche, spawn)
        sprite.state.goal = None
        logger.info(
            f"{sprite.name} resolved Goal("
            f"category={goal.category}, name={goal.name}, layer={goal.layer}, "
            f"outcome={rule.outcome})"
        )


class LayeredOutcome(OutcomeHandler):
    """
    Cross-layer lifecycle handler subsuming an active Goal with a prerequisite
    Goals.DOOR Goal when a portal is located, or demoting it directly to
    dormant episodic memory (Responses.STORE) when unreachable.
    """
    locator: Locator
    fallback_responses: Tuple[Responses, ...]

    def __init__(
        self,
        locator: Optional[PortalLocator] = None,
        fallback_responses: Tuple[Responses, ...] = (Responses.STORE,)
    ):
        self.locator = (
            locator if locator is not None else BidirectionalDoorLocator()
        )
        self.fallback_responses = fallback_responses

    def apply(
        self,
        rule: GoalRule,
        sprite: Asset,
        board: Board,
        response: ResponseResolver,
        reflex: ReflexResolver,
        spawn: ExpressionSpawner
    ) -> None:
        goal = sprite.state.goal
        target_door = self.locator.locate(sprite, board)

        if target_door is not None:
            response.resolve(rule.responses, goal, sprite.state.memory)
            reflex.resolve(rule.reflexes, goal, sprite.state.psyche, spawn)
            sprite.state.goal = Goal(
                name=target_door.name,
                category=Goals.DOOR,
                layer=sprite.state.layer,
                position=Position(
                    x=target_door.state.position.x,
                    y=target_door.state.position.y
                )
            )
            logger.info(
                f"{sprite.name} subsumed Goal("
                f"category={goal.category}, name={goal.name}, layer={goal.layer}"
                f") with Door({target_door.name})"
            )
            return

        # Unreachable portal: demote directly to dormant episodic memory
        # without pushing onto memory.stack to prevent Recall -> Sync loops
        response.resolve(self.fallback_responses, goal, sprite.state.memory)
        reflex.resolve(rule.reflexes, goal, sprite.state.psyche, spawn)
        sprite.state.goal = None
        logger.info(
            f"{sprite.name} demoted unreachable layered Goal("
            f"category={goal.category}, name={goal.name}, layer={goal.layer})"
        )


# -----------------------------------------------------


class OutcomeResolver(OperatorResolver[Outcomes, OutcomeHandler]):
    """
    Dispatches matched GoalRule outcomes to registered OutcomeHandler objects.
    """

    @classmethod
    def defaults(cls) -> Dict[Outcomes, OutcomeHandler]:
        terminal = TerminalOutcome()
        return {
            Outcomes.COMPLETE: terminal,
            Outcomes.LAYERED: LayeredOutcome(),
            Outcomes.LOST: terminal,
        }

    def resolve(
        self,
        rule: GoalRule,
        sprite: Asset,
        board: Board,
        response: ResponseResolver,
        reflex: ReflexResolver,
        spawn: ExpressionSpawner
    ) -> Outcomes:
        """
        Executes the OutcomeHandler registered for rule.outcome and returns
        the matched Outcome.
        """
        self.get(rule.outcome).apply(
            rule=rule,
            sprite=sprite,
            board=board,
            response=response,
            reflex=reflex,
            spawn=spawn
        )
        return rule.outcome