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
from app.models.state.assets.cursors import AttachmentState
from app.models.state.assets.sheets import SpriteState
from app.models.state.core import AssetState
from app.static.semantics import (
    Expressions,
    ExpressionsPalette,
    Goals,
    Outcomes
)

# -----------------------------------------------------


class GoalResolver:
    """
    Declarative Goal lifecycle resolver composing compiled GoalEvaluator
    classification with extensible ResponseResolver (Memory), ReflexResolver
    (Psyche), and OutcomeResolver (Goal lifecycle) operators.
    """
    evaluator: GoalEvaluator
    response: ResponseResolver
    reflex: ReflexResolver
    outcomes: OutcomeResolver

    _door_locator: PortalLocator = BidirectionalDoorLocator()

    def __init__(
        self,
        evaluator: GoalEvaluator,
        response: Optional[ResponseResolver] = None,
        reflex: Optional[ReflexResolver] = None,
        outcomes: Optional[OutcomeResolver] = None
    ):
        self.evaluator = evaluator
        self.response = response if response is not None else ResponseResolver()
        self.reflex = reflex if reflex is not None else ReflexResolver()
        self.outcomes = outcomes if outcomes is not None else OutcomeResolver()

    @classmethod
    def door(cls, sprite: Asset, board: Board) -> Optional[Asset]:
        """
        Locates a bidirectional portal Door (LayerProjections.IN or OUT) on
        the Sprite's active Layer using the configured PortalLocator strategy.
        """
        return cls._door_locator.locate(sprite, board)

    @staticmethod
    def _target(
        sprite: Asset,
        board: Board,
        sprites: Dict[str, Any]
    ) -> Optional[AssetState]:
        """
        Resolves the active Goal's target AssetState in O(1) for ISL evaluation.
        """
        goal = sprite.state.goal
        if not goal or not goal.name or goal.category == Goals.POSITION:
            return None

        if goal.category == Goals.DOOR:
            layer = goal.layer if goal.layer is not None else sprite.state.layer
            target_asset = board.asset(goal.name, layer)
            return target_asset.state if target_asset is not None else None

        target_asset = (
            board.asset(goal.name, sprite.state.layer)
            or board.asset(goal.name)
        )
        if target_asset is not None:
            return target_asset.state

        if goal.category in (Goals.TARGET, Goals.SUBJECT):
            return sprites.get(goal.name)

        return None

    def evaluate(
        self,
        state: SpriteState,
        sprites: Dict[str, Any],
        target: Optional[AssetState] = None
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
                'target': target,
            }
        )

    def resolve(self, sprite: Asset, board: Board) -> Optional[Outcomes]:
        """
        Evaluates the Sprite's active Goal and dispatches the matched
        OutcomeHandler, Memory Responses, and Psyche Reflexes.
        Returns the matched Outcome, or None if no Goal is active or the Goal
        remains undetermined (free).
        """
        if not sprite.state.goal:
            return None

        sprites = board.characters()
        target = self._target(sprite, board, sprites)
        rule = self.evaluate(sprite.state, sprites, target)

        if rule is None:
            return None

        def _spawn(
            palette: ExpressionsPalette,
            expression: Expressions
        ) -> Optional[AttachmentState]:
            if board.cradle is None:
                return None
            return board.cradle.spawn_expression(palette, expression, sprite)

        return self.outcomes.resolve(
            rule=rule,
            sprite=sprite,
            board=board,
            response=self.response,
            reflex=self.reflex,
            spawn=_spawn
        )