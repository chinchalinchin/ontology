"""
@asset.hitbox
@category.resources

# Ontology: app.assets.hitboxes.resources

Resource HitboxSchema implementations.
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
from app.models.properties import ResourceProperties
from app.models.state import ResourceState

# Cython Libraries
from libs.core.models import Hitbox

# ---------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------

class StageHitbox(HitboxSchema):
    """
    Resolves biological/geological stage-indexed hitboxes from ResourceProperties.
    """
    def elevations(self, properties: ResourceProperties, state: ResourceState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: ResourceProperties,
        state: ResourceState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        return properties.hitboxes.get(state.stage, []) or []
