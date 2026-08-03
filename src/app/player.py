
"""
# Ontology: Player
"""

# NOTE: pseudo code

from app.assets.base import Asset
from app.input.devices import Keyboard, Controller
from app.models.state import SpriteState


class Player(Asset):
    device: Controller | Keyboard

    def __init__(self, 
        device = Enum["controller" | "keyboard"],
        **kwargs
    ):
        super().__init__(**kwargs)
        if device == "controller":
            # load controller State <-> Input mapping
            mapping = "TODO"
            self.device = Controller(mapping)
        else:
            # load keyboard State <-> Input mapping
            mapping = "TODO"
            self.device = Keyboard(mapping)

    def poll(self) -> SpriteState:
        # TODO: Map device to state
        return SpriteState(
            # TODO: init
        )