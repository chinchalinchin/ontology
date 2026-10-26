"""
@domain.abstract
@app.base
@app.core
@category.crafts

@app.module
@workflow.compositions

# Ontology: Source - app.game.logic.modules.multipliers.base

Base Multiplier interface
"""
# Standard Libraries
from abc import abstractmethod
import dataclasses
from typing import (
    List,
    Optional
)

# Application Libraries
from app.assets.base import Asset
from app.models.state import CraftState
from app.models.properties import CraftProperties
from app.models.config import Recipe
from app.models.abstracts import Singleton  
from app.services.factories.assets import AssetFactory
# Cython Libraries
from libs.core.models import (
    Position,
    Multiple
)

# ---------------------------------------------------

class Multiplier(Singleton):
    """
    Interface for Multiplier implementations of Multiplication Strategies
    """

    def _unit(
        self,
        state: CraftState,
        props: CraftProperties,
        recipe: Recipe,
        category: str,
        instance: str,
        unit_name: str,
        layer: str,
        pos: Position,
        blueprint: Optional[str],
        anchor: int
    ) -> Asset:
        unit_substrate = self.materials.substrate(instance, blueprint=blueprint)
        unit_state = dataclasses.replace(
            state,
            name=unit_name,
            layer=layer,
            position=pos,
            blueprint=blueprint,
            multiple=Multiple(1, 1),
            anchor=anchor
        )
        return AssetFactory.asset(
            category=category,
            instance=instance,
            properties=props,
            state=unit_state,
            recipe=recipe,
            substrate=unit_substrate
        )
    @abstractmethod
    def multiply(
        self,
        state: CraftState,
        props: CraftProperties,
        recipe: Recipe,
        category: str,
        instance: str,
        base_pos: Position,
        layer: str,
        base_name: str,
        nx: int,
        ny: int
    ) -> List[Asset]:
        """"""
        pass