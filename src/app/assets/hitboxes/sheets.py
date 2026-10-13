"""
# Ontology: app.assets.hitboxes.sheets

"""
# Standard Libraries
from typing import (
    Optional,
    List
)

# Application Libraries
from app.assets.base import (
    HitboxSchema,
    Frame
)
from app.models.properties import SheetProperties
from app.models.state import AssetState

# Cython Libraries
from libs.core.models import Hitbox

class AttackHitbox(HitboxSchema):
    """
    Resolves directional and frame-keyed attackboxes from SheetProperties.
    """
    def elevations(self, properties: SheetProperties, state: AssetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: SheetProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        if not frame:
            return []
        keys = frame.keys(state.id, state)
        if not keys:
            return []
        frame_key = keys[0][0]
        return properties.attackboxes.get(frame_key, [])