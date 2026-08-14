"""
# Ontology: app.assets.frames

Package for Asset Frame implementations.
"""
# Application Libraries
from app.config.enums import AnimationRecipe
import app.config.settings as settings
from app.assets.base import Frame
from app.models.state import AssetState

class SingleFrame(Frame):
    """
    """

    def key(self, id: str, state: AssetState) -> str:
        """
        """
        return id
        
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        w, l = properties["dimensions"]["w"], properties["dimensions"]["l"]
        return {id: (0, 0, w, l)}
        
class IterableFrame(Frame):

    def key(self, id: str, state: AssetState) -> str:
        """
        """
        return settings.SEPARATOR.join([
            id, 
            str(state.animation.frame)
        ])
        
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        w, l = properties["dimensions"]["w"], properties["dimensions"]["l"]
        crops = {}
        count = properties.get("count", 1)
        for f in range(count):
            crops[f"{id}-{f}"] = (f * w, 0, w, l)
        return crops

class StateFrame(Frame):
    """
    """

    def key(self, id: str, state: AssetState) -> str:
        """
        """
        return settings.SEPARATOR.join([
            id, 
            state.animation.action, 
            state.animation.direction,
            str(state.animation.frame)
        ])

    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        w, l = properties["dimensions"]["w"], properties["dimensions"]["l"]
        crops = {}
        for action, action_prop in properties.get("actions", {}).items():
            for direction, dir_prop in action_prop.get("directions", {}).items():
                row = dir_prop["row"]
                count = action_prop["count"]
                for f in range(count):
                    frame_key = f"{id}-{action}-{direction}-{f}"
                    crops[frame_key] = (f * w, row * l, w, l)
        return crops