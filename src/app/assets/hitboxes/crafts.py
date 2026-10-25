"""
@domain.concrete
@app.asset
@asset.hitbox
@category.crafts
@modality.material
@workflow.compositions

# Ontology: Source - app.assets.hitboxes.crafts

Craft HitboxSchema implementations.
"""
# Standard Libraries
from typing import (
    Optional,
    List
)
import logging

# Application Libraries
from app.assets.base import (
    Frame,
    HitboxSchema
)
from app.game.logic.relations import MaterialIndex
from app.models.properties import CraftProperties
from app.models.state import (
    PlatformState,
    CraftState,
)

# Cython Libraries
from libs.core.models import (
    Hitbox,
    Position
)

logger = logging.getLogger(__name__)

class ElevatedHitbox(HitboxSchema):
    """
    Resolves relative tier-indexed hitboxes from CraftProperties.
    """
    def elevations(
        self,
        properties: CraftProperties,
        state: PlatformState
    ) -> List[int]:
        base_e = state.elevation if state.elevation is not None else 0
        if not properties.hitboxes:
            return [base_e]
        return [base_e + k for k in properties.hitboxes.keys()]

    def get(
        self,
        properties: CraftProperties,
        state: PlatformState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if not properties.hitboxes:
            return []
        base_e = state.elevation if state.elevation is not None else 0
        return properties.hitboxes.get(elevation - base_e, []) or []


class MaterialHitbox(HitboxSchema):
    """
    Resolves blueprint-dependent hitboxes for Crafts via MaterialIndex.
    Passable blueprints emit [] while obstacle blueprints emit active hitboxes.
    """

    def elevations(
        self,
        properties: CraftProperties,
        state: CraftState
    ) -> List[int]:
        if not MaterialIndex().is_obstacle(state.blueprint):
            return []
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: CraftProperties,
        state: CraftState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if not MaterialIndex().is_obstacle(state.blueprint):
            return []

        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        if properties.hitboxes is None:
            if properties.dimensions:
                return [Hitbox(Position(0, 0), properties.dimensions)]
            return []

        if isinstance(properties.hitboxes, dict):
            return properties.hitboxes.get(state.blueprint, []) or []

        return properties.hitboxes