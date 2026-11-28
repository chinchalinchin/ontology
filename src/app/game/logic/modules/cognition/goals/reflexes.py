"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.reflexes

Reflex implementations.
"""
# Standard Libraries
from typing import (
    Dict,
    Iterable,
)

# Application Libraries
from app.models.state.assets.sheets import (
    Goal,
    Psyche
)
from app.static.semantics import (
    Expressions,
    ExpressionsPalette,
    Reflexes
)
from app.game.logic.modules.cognition.goals.base import (
    Operator,
    ExpressionSpawner,
    Reflex
)

# -----------------------------------------------------------------------

class ExpressionReflex(Reflex):
    """
    Reusable parameterized Reflex that spawns and attaches an Expression
    cursor to a Sprite's Psyche.
    """
    palette: ExpressionsPalette
    expression: Expressions

    def __init__(
        self,
        palette: ExpressionsPalette,
        expression: Expressions
    ):
        self.palette = palette
        self.expression = expression

    def apply(
        self,
        goal: Goal,
        psyche: Psyche,
        spawn: ExpressionSpawner
    ) -> None:
        attachment = spawn(self.palette, self.expression)
        if attachment is not None:
            psyche.expression = attachment


class ConfusionReflex(ExpressionReflex):
    """
    Involuntary confusion bubble reflex triggered when a Sprite abandons a
    lost Character Goal.
    """

    def __init__(self):
        super().__init__(
            palette=ExpressionsPalette.BUBBLES,
            expression=Expressions.CONFUSION
        )


class AngerReflex(ExpressionReflex):
    """
    
    """

    def __init__(self):
        super().__init__(
            palette=ExpressionsPalette.BUBBLES,
            expression=Expressions.ANGER
        )

class SurpriseReflex(ExpressionReflex):
    """
    
    """

    def __init__(self):
        super().__init__(
            palette=ExpressionsPalette.BUBBLES,
            expression=Expressions.SURPRISE
        )

# -----------------------------------------------------


class ReflexOperator(Operator[Reflexes, Reflex]):
    """
    Dispatches declarative Goal Reflexes to registered Reflex objects
    operating strictly on a Sprite's Psyche state.
    """

    @classmethod
    def defaults(cls) -> Dict[Reflexes, Reflex]:
        return {
            Reflexes.CONFUSION: ConfusionReflex(),
            Reflexes.ANGER: AngerReflex(),
            Reflexes.SURPRISE: SurpriseReflex()
        }

    def resolve(
        self,
        reflexes: Iterable[Reflexes],
        goal: Goal,
        psyche: Psyche,
        spawn: ExpressionSpawner
    ) -> None:
        """
        Executes each configured Psyche Reflex operator in order.
        """
        for key in reflexes:
            self.get(key).apply(goal, psyche, spawn)