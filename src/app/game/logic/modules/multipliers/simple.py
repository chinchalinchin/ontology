"""
@domain.concrete
@domain.logic
@app.core
@app.module
@category.crafts
@workflow.compositions

# Ontology: Source - app.game.logic.modules.multipliers.simple

Simple Multiplier implementations.
"""
# Standard Libraries
from typing import List

# Application Libraries
import app.static.settings as settings
from app.static.semantics import Orientations
from app.assets.base import Asset
from app.models.config import Recipe
from app.models.state import CraftState
from app.models.properties import CraftProperties
from app.game.logic.modules.multipliers import Multiplier

# Cython Libraries
from libs.core.models import Position

# ---------------------------------------------------

class SimpleMultiplier(Multiplier):
    """
    """
    
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
        """
        """
        w = props.dimensions.w
        l = props.dimensions.l
        base_anchor = int(state.anchor or 0)
        units: List[Asset] = []
        idx = 0

        for iy in range(ny):
            for ix in range(nx):
                seg_pos = Position(base_pos.x + ix * w, base_pos.y + iy * l)
                unit_name = settings.SEPARATOR.join([base_name, str(idx)])
                idx += 1
                units.append(
                    self._unit(
                        state,
                        props,
                        recipe,
                        category,
                        instance,
                        unit_name,
                        layer,
                        seg_pos,
                        state.blueprint,
                        base_anchor
                    )
                )
        return units


class OrientedMultiplier(SimpleMultiplier):
    """
    """
    
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
        """
        """
        if state.blueprint == Orientations.HORIZONTAL.value:
            nx, ny = nx, 1
        else:
            nx, ny = 1, ny

        return super().multiply(
            state=state,
            props=props,
            recipe=recipe,
            category=category,
            instance=instance,
            base_pos=base_pos,
            layer=layer,
            base_name=base_name,
            nx=nx,
            ny=ny
        )