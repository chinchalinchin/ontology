"""
@domain.concrete
@app.asset
@asset.hitbox
@category.crafts
@modality.material

# Ontology: Source - app.assets.hitboxes.crafts

Craft HitboxSchema implementations.
"""
# Standard Libraries
from typing import (
    List,
    Optional,
)
import logging

# Application Libraries
from app.assets.base import HitboxSchema
from app.game.logic.relations import MaterialIndex
from app.models.properties import CraftProperties
from app.models.state import (
    CraftState,
)

# Cython Libraries
from libs.core.models import Hitbox

logger = logging.getLogger(__name__)


class ElevatedHitbox(HitboxSchema):
    """
    Resolves relative tier-indexed hitboxes from CraftProperties.
    """

    def elevations(
        self,
        properties: CraftProperties,
        state: CraftState
    ) -> List[int]:
        base_e = max(0, state.elevation if state.elevation is not None else 0)
        if properties.hitboxes is None:
            return [base_e] if properties.dimensions else []
        if not properties.hitboxes:
            return []
        return [max(0, base_e + k) for k in properties.hitboxes.keys()]

    def get(
        self,
        properties: CraftProperties,
        state: CraftState,
        elevation: int
    ) -> List[Hitbox]:
        base_e = max(0, state.elevation if state.elevation is not None else 0)
        target_e = max(0, elevation)
        if properties.hitboxes is None:
            if target_e != base_e:
                return []
            return self._dimension_fallback(properties.dimensions)
        if not properties.hitboxes:
            return []
        return properties.hitboxes.get(target_e - base_e, []) or []


class MaterialHitbox(HitboxSchema):
    """
    Resolves blueprint-dependent hitboxes for Crafts via MaterialIndex.
    Passable blueprints emit [] while obstacle blueprints emit active hitboxes.
    """
    _materials: Optional[MaterialIndex]

    def __init__(self, materials: Optional[MaterialIndex] = None) -> None:
        """Initializes flyweight MaterialHitbox with an optional injected MaterialIndex."""
        if not hasattr(self, "_materials") or materials is not None:
            self._materials = materials

    def set_materials(self, materials: MaterialIndex) -> None:
        """Injects the compiled MaterialIndex relation from orchestration."""
        self._materials = materials

    def _resolve_materials(self) -> MaterialIndex:
        """Returns the injected MaterialIndex, binding once on unconfigured test paths."""
        materials = self._materials
        if materials is None:
            materials = MaterialIndex()
            self._materials = materials
        return materials

    def is_obstacle(self, blueprint: Optional[str]) -> bool:
        """Evaluates blueprint obstacle classification via the injected MaterialIndex."""
        return self._resolve_materials().is_obstacle(blueprint)

    def elevations(
        self,
        properties: CraftProperties,
        state: CraftState
    ) -> List[int]:
        if not self.is_obstacle(state.blueprint):
            return []
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: CraftProperties,
        state: CraftState,
        elevation: int,
    ) -> List[Hitbox]:
        if not self.is_obstacle(state.blueprint):
            return []

        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        if properties.hitboxes is None:
            return self._dimension_fallback(properties.dimensions)

        return properties.hitboxes.get(state.blueprint, []) or []