"""
@domain.concrete
@domain.logic
@app.module
@category.crafts
@workflow.compositions

# Ontology: Source - app.game.logic.modules.multiplers.perimeter

Perimeter multiplication strategy implementation.
"""
# Standard Libraries
from typing import List

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.game.logic.modules.multipliers import Multiplier
from app.models.state import CraftState
from app.models.properties import CraftProperties
from app.models.config import Recipe
from app.static.semantics import Enclosures

# Cython Libraries
from libs.core.models import Position

# ---------------------------------------------------

class PerimeterMultiplier(Multiplier):
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
        """
        """
        w = props.dimensions.w
        l = props.dimensions.l
        units: List[Asset] = []
        idx = 0

        north_hbs = props.hitboxes.get(Enclosures.NORTH.value, []) if props.hitboxes else []
        north_bottom = max((hb.position.y + hb.dimensions.l for hb in north_hbs), default=l)
        north_anchor = int(north_bottom - l)

        # Horizontal caps/shafts across [0, nx + 1]
        for ix in range(nx + 2):
            seg_x = base_pos.x + ix * w
            n_name = settings.SEPARATOR.join([base_name, Enclosures.NORTH.value, str(idx)])
            idx += 1
            units.append(
                self._unit(
                    state,
                    props,
                    recipe,
                    category,
                    instance,
                    n_name,
                    layer,
                    Position(seg_x, base_pos.y),
                    Enclosures.NORTH.value,
                    north_anchor
                )
            )

            s_name = settings.SEPARATOR.join([base_name, Enclosures.SOUTH.value, str(idx)])
            idx += 1
            units.append(
                self._unit(
                    state,
                    props,
                    recipe,
                    category,
                    instance,
                    s_name,
                    layer,
                    Position(seg_x, base_pos.y + (ny + 1) * l),
                    Enclosures.SOUTH.value,
                    0
                )
            )

        # Vertical caps/shafts across [0, ny + 1] (superimposes at corners to seal L-hitboxes)
        for iy in range(ny + 2):
            seg_y = base_pos.y + iy * l
            w_name = settings.SEPARATOR.join([base_name, Enclosures.WEST.value, str(idx)])
            idx += 1
            units.append(
                self._unit(
                    state,
                    props,
                    recipe,
                    category,
                    instance,
                    w_name,
                    layer,
                    Position(base_pos.x, seg_y),
                    Enclosures.WEST.value,
                    0
                )
            )

            e_name = settings.SEPARATOR.join([base_name, Enclosures.EAST.value, str(idx)])
            idx += 1
            units.append(
                self._unit(
                    state,
                    props,
                    recipe,
                    category,
                    instance,
                    e_name,
                    layer,
                    Position(base_pos.x + (nx + 1) * w, seg_y),
                    Enclosures.EAST.value,
                    0
                )
            )

        return units