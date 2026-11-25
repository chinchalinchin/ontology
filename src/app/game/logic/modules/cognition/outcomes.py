"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.outcomes

Outcome implementations.
"""
from __future__ import annotations

# Standard Libraries
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
from app.game.logic.modules.cognition.base import (
    Locator,
    Operator,
    Outcome,
    ExpressionSpawner
)
from app.game.logic.modules.cognition.reflexes import ReflexOperator
from app.game.logic.modules.cognition.responses import ResponseOperator
from app.models.state.assets.sheets import Goal
from app.static.semantics import (
    Goals,
    Outcomes,
    Responses
)
from app.services.automaton import GoalRule


# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------

class TerminalOutcome(Outcome):
    """
    Terminal lifecycle handler executing configured Responses and Reflexes
    and clearing the active Goal to None (used for COMPLETE and LOST).
    """

    def apply(
        self,
        rule: GoalRule,
        sprite: Asset,
        board: Board,
        response: ResponseOperator,
        reflex: ReflexOperator,
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


class LayeredOutcome(Outcome):
    """
    Cross-layer lifecycle handler subsuming an active Goal with a prerequisite
    Goals.DOOR Goal when a portal is located, or demoting it directly to
    dormant episodic memory (Responses.STORE) when unreachable.
    """
    locator: Locator
    fallback_responses: Tuple[Responses, ...]

    def __init__(
        self,
        locator: Optional[Locator] = None,
        fallback_responses: Tuple[Responses, ...] = (Responses.STORE,)
    ):
        self.locator = locator
        self.fallback_responses = fallback_responses

    def apply(
        self,
        rule: GoalRule,
        sprite: Asset,
        board: Board,
        response: ResponseOperator,
        reflex: ReflexOperator,
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


class OutcomeOperator(Operator[Outcomes, Outcome]):
    """
    Dispatches matched GoalRule outcomes to registered OutcomeHandler objects.
    """

    @classmethod
    def defaults(cls) -> Dict[Outcomes, Outcome]:
        return {
            Outcomes.COMPLETE: TerminalOutcome(),
            Outcomes.LAYERED: LayeredOutcome(),
            Outcomes.LOST: TerminalOutcome(),
        }

    def resolve(
        self,
        rule: GoalRule,
        sprite: Asset,
        board: Board,
        response: ResponseOperator,
        reflex: ReflexOperator,
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