"""
# Ontology: app.assets.hitboxes.resources

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

logger = logging.getLogger(__name__)

class StageHitbox(HitboxSchema):
    """
    Resolves biological/geological stage-indexed hitboxes from ResourceProperties.
    """

    def get(
        self,
        properties: ResourceProperties,
        state: ResourceState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        return properties.hitboxes.get(state.stage, []) or []
