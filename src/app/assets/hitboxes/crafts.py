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
    Resolves biological/geological stage-indexed hitboxes from ResourceProperties.
    """

    def get(
        self,
        properties: CraftProperties,
        state: AssetState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        return properties.hitboxes.get(state.elevation, []) or []
