
"""
# Ontology: Player
"""

# Standard Libraries
from enum import Enum

# Application Libraries
from app.assets.base import Asset
from app.input.devices import Keyboard, Controller
from app.models.state import SpriteState

class Device(str, Enum):
    CONTROLLER  = "controller"
    KEYBOARD    = "keyboard"

class Player(Asset):
    device: Device

    def __init__(self, 
        device: Device,
        **kwargs
    ):
        super().__init__(**kwargs)
        if device == Device.CONTROLLER:
            # load controller State <-> Input mapping
            mapping = "TODO"
            self.device = Controller(mapping)
        elif device == Device.KEYBOARD:
            # load keyboard State <-> Input mapping
            mapping = "TODO"
            self.device = Keyboard(mapping)

    def poll(self) -> SpriteState:
        # TODO: Map device to state
        return SpriteState(
            # TODO: init
        )