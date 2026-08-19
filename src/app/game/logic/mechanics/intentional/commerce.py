"""
# Ontology: app.game.logic.mechanics.intentional

Package for intentional Mechanic implementations, i.e. Sprite and Player logic.
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.game.logic.mechanics import Mechanic


# ----------------------------------------------------------------------------------------

class CommerceMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass

# ----------------------------------------------------------------------------------------

class SpeechMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass