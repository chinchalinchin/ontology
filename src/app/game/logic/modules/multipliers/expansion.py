"""
@domain.concrete
@domain.logic
@app.module
@category.crafts
@workflow.compositions

# Ontology: Source - app.game.logic.modules.multiplers.expansion

Expansion multiplication strategy implementation.
"""
# Standard Libraries
from typing import (
    List,
    Tuple
)

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.game.logic.modules.multipliers import Multiplier
from app.models.state import CraftState
from app.models.properties import CraftProperties
from app.models.config import Recipe
from app.static.semantics import Columns

# Cython Libraries
from libs.core.models import Position

# ---------------------------------------------------

class ExpansionMultiplier(Multiplier):
    """
    Interface for Multiplier implementation of MultiplicationStrategies
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
        """"""
        w = props.dimensions.w
        l = props.dimensions.l
        units: List[Asset] = []
        base_anchor = int(state.anchor or 0)
        idx = 0

        for ix in range(nx):
            col_x = base_pos.x + ix * w
            base_y = base_pos.y + (ny + 1) * l
            base_ground = base_y + l
            segments: List[Tuple[str, int]] = [
                (Columns.CROWNS.value, base_pos.y)
            ]
            for k in range(ny):
                segments.append(
                    (Columns.SHAFTS.value, base_pos.y + (k + 1) * l)
                )
            segments.append((Columns.BASES.value, base_y))

            for bp_part, seg_y in segments:
                unit_name = settings.SEPARATOR.join([base_name, bp_part, str(idx)])
                idx += 1
                seg_anchor = int(base_ground + base_anchor - (seg_y + l))
                units.append(
                    self._unit(
                        state,
                        props,
                        recipe,
                        category,
                        instance,
                        unit_name,
                        layer,
                        Position(col_x, seg_y),
                        bp_part,
                        seg_anchor
                    )
                )
        return units