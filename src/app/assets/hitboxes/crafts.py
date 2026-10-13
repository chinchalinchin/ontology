"""
# Ontology: app.assets.hitboxes.crafts

## TODO: phase 07-02
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
from app.models.properties import CraftProperties
from app.models.state import AssetState

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
        state: AssetState
    ) -> List[int]:
        base_e = state.elevation if state.elevation is not None else 0
        if not properties.hitboxes:
            return [base_e]
        return [base_e + k for k in properties.hitboxes.keys()]

    def get(
        self,
        properties: CraftProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if not properties.hitboxes:
            return []
        base_e = state.elevation if state.elevation is not None else 0
        return properties.hitboxes.get(elevation - base_e, []) or []