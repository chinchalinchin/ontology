"""
@app.core
@asset.hitbox

# Ontology: app.assets.hitboxes.core

Core Asset HitboxSchema implementations.
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

    def elevations(self, properties: AssetProperties, state: AssetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]
    
    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        if properties.hitboxes is None:
            if properties.dimensions:
                return [Hitbox(Position(0, 0), properties.dimensions)]
            return []
        return properties.hitboxes

    
class DynamicHitbox(HitboxSchema):
    """
    Resolves mutable hitboxes declared on AssetState.
    """

    def elevations(self, properties: AssetProperties, state: AssetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]
    
    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        if state.hitboxes is None:
            if properties.hitboxes is None:
                if properties.dimensions:
                    return [Hitbox(Position(0, 0), properties.dimensions)]
                return []
            return properties.hitboxes
        return state.hitboxes


class OrientedHitbox(HitboxSchema):
    """
    """

    def elevations(self, properties: AssetProperties, state: AssetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]
        
    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        return properties.hitboxes.get(state.orientation, []) or []


class DirectedHitbox(HitboxSchema):
    """
    """

    def elevations(self, properties: AssetProperties, state: AssetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        return properties.hitboxes.get(state.direction, []) or []
    
    
class NoHitbox(HitboxSchema):
    """
    Null strategy for passable assets (tiles, passive effects, overlays).
    """

    def elevations(self, properties: AssetProperties, state: AssetState) -> List[int]:
        return []

    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        return []