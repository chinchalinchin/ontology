"""
@domain.automata
@domain.logic
@app.service
@modality.intention
@workflow.plot
@workflow.seasons
@workflow.transitions

# Ontology: Source - app.services.translators.executors.transitions

Executors for the Intention Transition Matrix.
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
from app.services.translators.base import Backend


@dataclass(slots=True, frozen=True)
class Transition:
    """
    Immutable compiled finite-automaton transition rule.
    """
    next: str
    conditions: Tuple[Any, ...]  # Holds Callables (Lambda) or CodeType objects (AST)


class TransitionExecutor:
    """
    Evaluates finite-automaton state transitions (intentions, plots, stages)
    using an injected ConditionBackend.
    """
    transitions: Dict[str, Tuple[Transition, ...]]
    backend: Backend

    def __init__(
        self,
        transitions: Dict[str, Tuple[Transition, ...]],
        backend: Backend
    ):
        self.transitions = transitions
        self.backend = backend

    def evaluate(self, current_state: str, locals: Dict[str, Any]) -> Optional[str]:
        """
        Evaluates the dynamic locals against the compiled ISL conditions for a
        given state.

        Returns the string key for the next valid state transition,
        or None if no transitions evaluate to True.
        """
        state_transitions = self.transitions.get(current_state)
        if not state_transitions:
            return None

        for transition in state_transitions:
            if self.backend.evaluate(transition.conditions, locals):
                return transition.next

        return None


class TransitionTranslator:
    """
    Compiles raw finite-automaton transition rules into an Executor backed by
    the injected ConditionBackend.
    """
    backend: Backend

    def __init__(self, backend: Backend):
        self.backend = backend

    def compile(self, raw_configs: Dict[str, List[Any]]) -> TransitionExecutor:
        """
        Compiles string conditions into backend executables and constructs an
        Executor capable of evaluating them at runtime.
        """
        compiled_transitions: Dict[str, Tuple[Transition, ...]] = {
            state_str: tuple(
                Transition(
                    next=config.next,
                    conditions=self.backend.compile(config.conditions)
                )
                for config in configs
            )
            for state_str, configs in raw_configs.items()
        }

        return TransitionExecutor(
            transitions=compiled_transitions,
            backend=self.backend
        )