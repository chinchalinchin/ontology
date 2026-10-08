"""
# Ontology: app.assets.hitboxes.core
"""
# Standard Libraries
from typing import (
    List,
    Optional
)

# Application Libraries
from app.assets.base import (
    Frame,
    HitboxSchema
)
from app.models.properties import AssetProperties
from app.models.state import AssetState

# Cython Libraries
from libs.core.models import (
    Hitbox,
    Position
)

class StaticHitbox(HitboxSchema):
    """
    Resolves static hitboxes declared on immutable AssetProperties.
    """

    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if properties.hitboxes is None and properties.dimensions:
            return [Hitbox(Position(0, 0), properties.dimensions)]
        return properties.hitboxes

class DynamicHitbox(HitboxSchema):
    """
    Resolves mutable hitboxes declared on AssetState.
    """

    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if state.hitboxes is None:
            if properties.hitboxes is None and properties.dimensions:
                return [Hitbox(Position(0, 0), properties.dimensions)]
            return properties.hitboxes
        return state.hitboxes


class NoHitbox(HitboxSchema):
    """
    Null strategy for passable assets (tiles, passive effects, overlays).
    """

    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        return []