"""
@domain.automata
@domain.logic
@app.service
@modality.intention
@workflow.cognition

# Ontology: Source - app.services.translators.executors.resolutions

Executors for the Goal Resolution Matrix.
"""
# Standard Libraries
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple
)

# Application Libraries
from app.models.configurations.automata.goals import GoalConfiguration
from app.services.automaton.base import Backend
from app.static.semantics import (
    Goals,
    Outcomes,
    Reflexes,
    Responses
)

# ---------------------------------------------------------

OUTCOME_PRECEDENCE: Tuple[Outcomes, ...] = (
    Outcomes.COMPLETE,
    Outcomes.LAYERED,
    Outcomes.LOST,
)

# ---------------------------------------------------------


@dataclass(slots=True, frozen=True)
class GoalRule:
    """
    Immutable compiled Goal Resolution rule binding an Outcome to its
    orthogonal Memory responses, Psyche reflexes, and compiled ISL conditions.
    """
    outcome: Outcomes
    responses: Tuple[Responses, ...]
    reflexes: Tuple[Reflexes, ...]
    conditions: Tuple[Any, ...]


class GoalEvaluator:
    """
    Category-indexed rule classifier distinct from finite-automaton state
    Executors. Evaluates compiled GoalRules in canonical (COMPLETE, LAYERED,
    LOST) precedence and returns the first matched GoalRule, or None if the
    Goal remains undetermined (free).
    """
    rules: Dict[Goals, Tuple[GoalRule, ...]]
    backend: Backend

    def __init__(
        self,
        rules: Dict[Goals, Tuple[GoalRule, ...]],
        backend: Backend
    ):
        self.rules = rules
        self.backend = backend

    def evaluate(
        self,
        category: Goals,
        locals: Dict[str, Any]
    ) -> Optional[GoalRule]:
        """
        Classifies an active Goal category against dynamic locals.
        Returns the first matched GoalRule in canonical outcome precedence,
        or None if no outcome condition holds.
        """
        category_rules = self.rules.get(category)
        if not category_rules:
            return None

        # Ensure uniform 'target' binding across AST and Lambda backends when omitted
        eval_locals = locals if 'target' in locals else {**locals, 'target': None}

        for rule in category_rules:
            if self.backend.evaluate(rule.conditions, eval_locals):
                return rule

        return None


class GoalTranslator:
    """
    Compiles ConfigurationSchema.goals into a GoalEvaluator ordered by
    canonical (COMPLETE, LAYERED, LOST) outcome precedence.
    """
    backend: Backend

    def __init__(self, backend: Backend):
        self.backend = backend

    def compile(
        self,
        configs: Dict[Goals, Dict[Outcomes, GoalConfiguration]]
    ) -> GoalEvaluator:
        """
        Compiles category -> outcome -> GoalConfiguration tables into
        immutable GoalRule tuples. Fails fast on unsupported outcome keys
        or invalid ISL condition syntax.
        """
        compiled_rules: Dict[Goals, Tuple[GoalRule, ...]] = {}

        for category, outcome_map in configs.items():
            unknown = [
                outcome for outcome in outcome_map
                if outcome not in OUTCOME_PRECEDENCE
            ]
            if unknown:
                raise ValueError(
                    f"Unsupported goal outcome(s) for category '{category}': {unknown}"
                )

            ordered_rules: List[GoalRule] = []
            for outcome in OUTCOME_PRECEDENCE:
                config = outcome_map.get(outcome)
                if config is None:
                    continue

                compiled_conditions = self.backend.compile(config.conditions)
                ordered_rules.append(
                    GoalRule(
                        outcome=outcome,
                        responses=tuple(config.responses),
                        reflexes=tuple(config.reflexes),
                        conditions=compiled_conditions
                    )
                )

            compiled_rules[category] = tuple(ordered_rules)

        return GoalEvaluator(
            rules=compiled_rules,
            backend=self.backend
        )