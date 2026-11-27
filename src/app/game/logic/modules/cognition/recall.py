"""
@domain.automata
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.recall

IDLE-only two-tier memory recall (commitment stack and episodic memory).
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.models.state.assets.sheets import Goal
from app.static.semantics import Intentions

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------


class Recall:
    """
    IDLE-only two-tier memory retrieval service. Pops suspended parent Goals
    from memory.stack (LIFO) before scanning non-dormant entries in
    memory.goals without Intention-affinity filtering.
    """

    def remember(
        self,
        sprite: Asset,
        board: Optional[Board] = None
    ) -> Optional[Goal]:
        """
        Returns the next eligible Goal from Memory strictly when the Sprite is
        in Intentions.IDLE with no active Goal, or None otherwise.
        """
        state = sprite.state
        if state.intention != Intentions.IDLE or state.goal is not None:
            return None

        memory = state.memory

        # Tier 2: LIFO commitment stack
        if memory.stack:
            goal = memory.stack.pop()
            logger.info(
                f"{sprite.name} resumed stacked Goal("
                f"category={goal.category}, name={goal.name}, layer={goal.layer})"
            )
            return goal

        # Tier 3: First non-dormant episodic Goal
        for key, candidate in list(memory.goals.items()):
            if candidate.dormant:
                continue
            goal = memory.goals.pop(key)
            logger.info(
                f"{sprite.name} recalled episodic Goal("
                f"category={goal.category}, name={goal.name}, layer={goal.layer})"
            )
            return goal

        return None