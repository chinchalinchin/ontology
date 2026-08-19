"""
# Ontology: app.assets.frames

Package for Asset Frame implementations.
"""
# Stamdard Libraries
from typing import List

# Application Libraries
import app.config.settings as settings
from app.assets.base import Frame
from app.models.state import AssetState

def _safe_dim(properties: dict) -> tuple[int, int]:
    """Extract dimensions safely whether it's a raw dict or a Cython object bypassing asdict()"""
    dim = properties.get("dimensions")
    if hasattr(dim, 'w'):
        return dim.w, dim.l
    elif isinstance(dim, dict):
        return dim.get("w", 0), dim.get("l", 0)
    return 0, 0

class NoFrame(Frame):
    """
    ## NoFrame
    """

    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [id]
            
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        return {id: (0, 0, 0, 0)}
        
class SingleFrame(Frame):
    """
    ## SingleFrame
    """

    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [id]
        
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w, l = _safe_dim(properties)
        return {id: (0, 0, w, l)}
        
class IterableFrame(Frame):
    """
    ## IterableFrame
    """
    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [settings.SEPARATOR.join([
            id, 
            str(state.animation.frame)
        ])]
        
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w, l = _safe_dim(properties)
        crops = {}
        count = properties.get("count", 1)
        for f in range(count):
            crops[f"{id}-{f}"] = (f * w, 0, w, l)
        return crops
    
class StateFrame(Frame):
    """
    ## StateFrame
    """

    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [settings.SEPARATOR.join([
            id, 
            state.animation.action, 
            state.animation.direction,
            str(state.animation.frame)
        ])]

    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w, l = _safe_dim(properties)
        crops = {}
        
        # Handle dict format since this goes through dataclasses.asdict()
        for action, action_prop in properties.get("actions", {}).items():
            for direction, dir_prop in action_prop.get("directions", {}).items():
                row = dir_prop["row"]
                count = action_prop["count"]
                for f in range(count):
                    frame_key = f"{id}-{action}-{direction}-{f}"
                    crops[frame_key] = (f * w, row * l, w, l)
        return crops

class SpriteFrame(StateFrame):
    """
    ## SpriteFrame

    Specialized Frame component for Sprites that yields a strict Z-indexed list of frame keys based on the Sprite's inventory.
    """

    def keys(self, id: str, state: AssetState) -> List[str]:
        # Start with the base Persona frame key
        frame_keys = super().keys(id, state)
        
        # Iterate over active equipment in strict Z-index order: Base -> Armor -> Utility -> Tool -> Weapon
        if hasattr(state, 'inventory') and state.inventory and state.inventory.equipment:
            eq = state.inventory.equipment
            for eq_key in (eq.armor, eq.utility, eq.tool, eq.weapon, eq.shield):
                if eq_key:
                    frame_keys.append(settings.SEPARATOR.join([
                        eq_key,
                        state.animation.action,
                        state.animation.direction,
                        str(state.animation.frame)
                    ]))
        
        return frame_keys