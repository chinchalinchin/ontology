"""
@domain.automata
@domain.abstract
@app.base
@app.service

# Ontology: Source - app.services.translators.base

Abstract ISL ConditionBackend contract and finite-automaton Transition
Translator and Executor.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Sequence,
    Tuple
)

# ---------------------------------------------------------


class Backend(ABC):
    """
    Defines the shared ISL expression compilation and conjunction evaluation
    strategy (AST vs. Lambda), decoupled from both finite-automaton Executors
    and declarative GoalEvaluators.
    """

    @abstractmethod
    def conditionalize(self, condition: str) -> Any:
        """
        Compiles a single ISL condition string into a backend executable.
        Must fail fast by raising on invalid syntax.
        """
        pass

    def compile(self, conditions: Sequence[str]) -> Tuple[Any, ...]:
        """
        Compiles an ordered conjunction of ISL condition strings.
        Fails fast if any conjunct fails to compile.
        """
        return tuple(self.conditionalize(cond) for cond in conditions)

    @abstractmethod
    def evaluate(
        self,
        conditions: Sequence[Any],
        locals: Dict[str, Any]
    ) -> bool:
        """
        Short-circuit evaluates a compiled conjunction against dynamic locals.
        Returns False for empty condition sequences.
        """
        pass