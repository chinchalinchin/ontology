"""
# Ontology: app.game.logic.relations.materials

Relational index mapping materials and blueprints
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    Tuple,
    Optional,
    Any,
    TYPE_CHECKING
)
import logging

if TYPE_CHECKING:
    from app.models.config import MaterialConfiguration

logger = logging.getLogger(__name__)

class MaterialIndex:
    materials: MaterialConfiguration

    def __init__(self, materials: MaterialConfiguration):
        self.materials = materials

    def from_configuration(self):
        pass