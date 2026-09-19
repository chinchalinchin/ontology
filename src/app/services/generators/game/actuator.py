"""
# Ontology: app.services.generators.game.actuator

Package for constructing Fluid Effect flows.
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING: 
    from app.game.board import Board

class Actuator:

    def pump(fluid, board: Board):
        # TODO
        pass