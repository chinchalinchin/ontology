"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.responses

Abstract Response operator interface, concrete Memory operators, and
ResponseResolver dispatcher.
"""
# Standard Libraries
from typing import (
    Dict,
    Iterable
)

# Application Libraries
from app.models.state.assets.sheets import (
    Goal,
    Memory
)
from app.static.semantics import Responses
from app.game.logic.modules.cognition.base import (
    Response,
    Operator
)

# -----------------------------------------------------


class ForgetResponse(Response):
    """Evicts the Goal's identity from episodic memory."""

    def apply(self, goal: Goal, memory: Memory) -> None:
        if goal.name:
            memory.goals.pop(goal.name, None)


class StoreResponse(Response):
    """Marks the Goal dormant and commits it into episodic memory."""

    def apply(self, goal: Goal, memory: Memory) -> None:
        goal.dormant = True
        if goal.name:
            memory.goals[goal.name] = goal


class PushResponse(Response):
    """
    Pushes a suspended parent Goal onto the LIFO commitment stack while
    preventing consecutive duplicate top entries.
    """

    def apply(self, goal: Goal, memory: Memory) -> None:
        if memory.stack:
            top = memory.stack[-1]
            if (
                top is goal
                or (
                    top.name == goal.name
                    and top.category == goal.category
                    and top.layer == goal.layer
                )
            ):
                memory.stack[-1] = goal
                return
        memory.stack.append(goal)


class UnwindResponse(Response):
    """
    Pops the top suspended parent Goal from memory.stack, marks it dormant,
    and demotes it into episodic memory.
    """

    def apply(self, goal: Goal, memory: Memory) -> None:
        if not memory.stack:
            return
        parent = memory.stack.pop()
        parent.dormant = True
        if parent.name:
            memory.goals[parent.name] = parent


# -----------------------------------------------------


class ResponseOperators(Operator[Responses, Response]):
    """
    Dispatches declarative Goal Responses to registered Response objects
    operating strictly on a Sprite's Memory state.
    """

    @classmethod
    def defaults(cls) -> Dict[Responses, Response]:
        return {
            Responses.FORGET: ForgetResponse(),
            Responses.STORE: StoreResponse(),
            Responses.PUSH: PushResponse(),
            Responses.UNWIND: UnwindResponse(),
        }

    def resolve(
        self,
        responses: Iterable[Responses],
        goal: Goal,
        memory: Memory
    ) -> None:
        """
        Executes each configured Memory Response operator in order.
        """
        for key in responses:
            self.get(key).apply(goal, memory)