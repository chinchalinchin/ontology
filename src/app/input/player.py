
"""
# Ontology: Player
"""

# Application Libraries
from app.assets.base import Asset, Taxonomy
from app.assets.animations import StateAnimation
from app.assets.frames import StateFrame
from app.config.enums import Devices
from app.input.devices import Keyboard, Controller, Device
from app.models.state import (
    PlayerState, 
    AnimationState, 
    Character, 
    Inventory, 
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
        device: Devices
    ):
        # PLACEHOLDER SUPER.__INIT__ FOR NOW
        #   CONSTRUCTING EVERYTHING MANUALLY...
        super().__init__(
            taxonomy =  Taxonomy(id="hero", name="hero", category="sheet", instance="sprite"),
            state = PlayerState(
                layer = 0,
                position = Position(x=0, y=0),
                animation = AnimationState(),
                character = Character(strength=10, defense=10, speed=10),
                inventory = Inventory(),
                meters = Meters(
                    health = Health(100, 100),
                    magic = Magic(100, 100)
                )
            ),
            properties = PlayerProperties(
                dimensions = Dimensions(w=64, l=64)
            ), # PLACEHOLDER
            frame = StateFrame(),
            animation = StateAnimation()
        )
        
        if device == Devices.CONTROLLER:
            # load controller State <-> Input mapping
            mapping = "TODO"
            self.device = Controller(mapping)
        elif device == Devices.KEYBOARD:
            # load keyboard State <-> Input mapping
            mapping = "TODO"
            self.device = Keyboard(mapping)

    def poll(self) -> PlayerState:
        # TODO: Map device to state
        return PlayerState(
            # TODO: init
        )