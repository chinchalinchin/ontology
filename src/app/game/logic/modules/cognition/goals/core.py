"""
@domain.automata
@domain.concrete
@app.module
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.core
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Any,
    Dict,
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.game.logic.modules.cognition.goals.base import ResolutionContext
from app.game.logic.modules.cognition.goals.locators import LocatorOperator
from app.game.logic.modules.cognition.goals.reflexes import ReflexOperator
from app.game.logic.modules.cognition.goals.responses import ResponseOperator
from app.game.logic.modules.cognition.goals.outcomes import OutcomeOperator
from app.models.state.assets.cursors import AttachmentState
from app.models.state.assets.sheets import SpriteState
from app.models.state.core import AssetState
from app.static.semantics import (
    Expressions,
    ExpressionsPalette,
    Outcomes
)
from app.services.automaton import (
    GoalEvaluator,
    GoalRule
)


# -----------------------------------------------------


class GoalResolver:
    """
    Declarative Goal lifecycle resolver composing compiled GoalEvaluator
    classification with extensible ResponseOperator (Memory), ReflexOperator
    (Psyche), OutcomeOperator (Goal lifecycle), and LocatorOperator (spatial
    search) operators.
    """
    evaluator: GoalEvaluator
    responses: ResponseOperator
    reflexes: ReflexOperator
    outcomes: OutcomeOperator
    locators: LocatorOperator

    def __init__(
        self,
        evaluator: GoalEvaluator,
        responses: Optional[ResponseOperator] = None,
        reflexes: Optional[ReflexOperator] = None,
        outcomes: Optional[OutcomeOperator] = None,
        locators: Optional[LocatorOperator] = None
    ):
        self.evaluator = evaluator
        self.responses = responses if responses is not None else ResponseOperator()
        self.reflexes = reflexes if reflexes is not None else ReflexOperator()
        self.outcomes = outcomes if outcomes is not None else OutcomeOperator()
        self.locators = locators if locators is not None else LocatorOperator()

    def evaluate(
        self,
        state: SpriteState,
        sprites: Dict[str, Any],
        assets: Dict[str, AssetState]
    ) -> Optional[GoalRule]:
        """
        Pure predicate classifying a Sprite's active Goal against the compiled
        Goal Resolution Matrix without mutating State.
        """
        if not state.goal or not state.goal.category:
            return None

        return self.evaluator.evaluate(
            category=state.goal.category,
            locals={
                'sprite': state,
                'sprites': sprites,
                'assets': assets,
            }
        )

    def resolve(self, sprite: Asset, board: Board) -> Optional[Outcomes]:
        """
        Evaluates the Sprite's active Goal and dispatches the matched
        Outcome, Memory Responses, and Psyche Reflexes.
        Returns the matched Outcome, or None if no Goal is active or the Goal
        remains undetermined (free).
        """
        if not sprite.state.goal:
            return None

        sprites = board.characters()
        assets = board.states(sprite.state.layer)
        rule = self.evaluate(sprite.state, sprites, assets)

        if rule is None:
            return None

        def _spawn(
            palette: ExpressionsPalette,
            expression: Expressions
        ) -> Optional[AttachmentState]:
            if board.cradle is None:
                return None
            return board.cradle.spawn_expression(palette, expression, sprite)

        context = ResolutionContext(
            responses=self.responses,
            reflexes=self.reflexes,
            locators=self.locators,
            spawn=_spawn
        )

        return self.outcomes.resolve(
            rule=rule,
            sprite=sprite,
            board=board,
            context=context
        )