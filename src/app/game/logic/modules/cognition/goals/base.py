"""
@domain.abstract
@domain.automata
@app.base
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.base

Abstract interfaces for the Cognitive pipeline.
"""
from __future__ import annotations

# Standard Libraries
from abc import (
    ABC, 
    abstractmethod
)
from dataclasses import dataclass
from typing import (
    Callable,
    Dict,
    FrozenSet,
    Generic,
    Optional,
    TypeVar,
    TYPE_CHECKING
)
import logging

# Application Libraries
from app.assets.base import Asset
from app.models.state.assets.cursors import AttachmentState
from app.models.state.assets.sheets import (
    Goal,
    Psyche,
    Memory
)
from app.static.semantics import (
    Expressions,
    ExpressionsPalette,
)
from app.services.automaton import GoalRule

if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.logic.modules.cognition.goals.locators import LocatorOperator
    from app.game.logic.modules.cognition.goals.reflexes import ReflexOperator
    from app.game.logic.modules.cognition.goals.responses import ResponseOperator
    
# -----------------------------------------------------

K = TypeVar('K')
Op = TypeVar('Op')
ExpressionSpawner = Callable[
    [ExpressionsPalette, Expressions],
    Optional[AttachmentState]
]

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------


@dataclass(slots=True, frozen=True)
class ResolutionContext:
    """
    Immutable bundle of orthogonal cognitive operators, expression spawner,
    and excluded stalled Asset names passed into Outcome execution during Goal
    resolution.
    """
    responses: ResponseOperator
    reflexes: ReflexOperator
    locators: LocatorOperator
    spawn: ExpressionSpawner
    excluded: FrozenSet[str] = frozenset()


class Operator(ABC, Generic[K, Op]):
    """
    Abstract dispatcher mapping semantic keys to extensible operator objects.
    Supports constructor injection of custom operator sets as well as dynamic
    registration for archetype- or Recipe-driven Sprite behaviors.
    """
    operators: Dict[K, Op]

    def __init__(self, operators: Optional[Dict[K, Op]] = None):
        self.operators = (
            dict(operators) if operators is not None else self.defaults()
        )

    @classmethod
    @abstractmethod
    def defaults(cls) -> Dict[K, Op]:
        """Constructs the default operator mapping for this resolver."""
        pass

    def register(self, key: K, operator: Op) -> None:
        """Registers or overrides an operator object for the given key."""
        self.operators[key] = operator

    def get(self, key: K) -> Op:
        """
        Retrieves the registered operator for key, failing fast if absent.
        """
        operator = self.operators.get(key)
        if operator is None:
            raise KeyError(
                f"{type(self).__name__} has no operator registered for '{key}'."
            )
        return operator

# -----------------------------------------------------

class Locator(ABC):
    """
    Abstract strategy for locating an Asset.
    """

    @abstractmethod
    def locate(
        self,
        sprite: Asset,
        board: Board,
        excluded: FrozenSet[str] = frozenset()
    ) -> Optional[Asset]:
        """Locate an Asset, skipping any Asset names in excluded."""
        pass

# -----------------------------------------------------


class Response(ABC):
    """
    Abstract interface for a stateless Memory operator executed in response
    to a resolved Goal outcome.
    """

    @abstractmethod
    def apply(self, goal: Goal, memory: Memory) -> None:
        """Mutates memory for the given Goal."""
        pass

# -----------------------------------------------------


class Reflex(ABC):
    """
    Abstract interface for an involuntary Psyche operator triggered by a
    Goal outcome, decoupled from Board and Cradle via ExpressionSpawner.
    """

    @abstractmethod
    def apply(
        self,
        goal: Goal,
        psyche: Psyche,
        spawn: ExpressionSpawner
    ) -> None:
        """Mutates psyche in response to the resolved Goal."""
        pass


class Outcome(ABC):
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
        context: ResolutionContext
    ) -> None:
        """Applies Memory responses, Psyche reflexes, and active Goal updates."""
        pass