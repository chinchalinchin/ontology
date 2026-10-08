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

    def get(
        self,
        properties: SheetProperties,
        state: AssetState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if not frame:
            return []
        keys = frame.keys(state.id, state)
        if not keys:
            return []
        frame_key = keys[0][0]
        return properties.attackboxes.get(frame_key, [])