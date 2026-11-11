"""
@domain.concrete
@app.asset
@asset.hitbox
@category.sheets

# Ontology: Source - app.assets.hitboxes.sheets

Sheet HitboxSchema implementations.
"""
# Standard Libraries
from typing import List

# Application Libraries
import app.static.settings as settings
from app.assets.base import HitboxSchema
from app.models.properties import SheetProperties
from app.models.state import SheetState

# Cython Libraries
from libs.core.models import Hitbox

# ---------------------------------------------------------

class AttackHitbox(HitboxSchema):
    """
    Resolves directional and frame-keyed attackboxes from SheetProperties.
    """
    def elevations(self, properties: SheetProperties, state: SheetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: SheetProperties,
        state: SheetState,
        elevation: int
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        action_key = settings.SEPARATOR.join([
            state.animation.action,
            state.animation.direction,
            str(state.animation.frame)
        ])
        return properties.attackboxes.get(action_key, []) if properties.attackboxes else []