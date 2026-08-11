
"""
# Ontology: Player
"""

# Application Libraries
from app.assets.base import Asset, Taxonomy
from app.assets.animations import StateAnimation
from app.assets.frames import StateFrame
from app.config.enums import Devices
from app.input.devices import (
    Keyboard, 
    Controller, 
    Device
)
from app.models.state import (
    PlayerState, 
    AnimationState, 
    Character, 
    Inventory, 
    Intention,
    Meters, 
    Magic, 
    Health
)
from app.models.properties import PlayerProperties

# Cython Libraries
from libs.core import Position, Dimensions

class Player(Asset):
    device: Device

    def __init__(self, 
        device: Devices,
        **kwargs
    ):
        super().__init__(**kwargs)
        if device == Devices.CONTROLLER:
            # load controller State <-> Input mapping
            mapping = "TODO"
            self.device = Controller(mapping)
        elif device == Devices.KEYBOARD:
            # load keyboard State <-> Input mapping
            mapping = "TODO"
            self.device = Keyboard(mapping)

    def poll(self) -> Intention:
        # TODO: Map device to intention
        return Intention(
            # TODO: init
        )