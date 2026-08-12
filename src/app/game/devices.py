"""
# Ontology: Devices
"""

# Standard Libraries
from typing import Dict

# Application Libraries
from app.config.enums import Directions, Actions

# Cython Libraries
import libs.input as sdl

class Device:
    mapping: Dict

    def __init__(self, mapping):
        self.mapping = mapping

class Keyboard(Device):
    def __init__(self, mapping: dict):
        super().__init__(mapping)
        # Pre-calculate the tuple of scancodes to query every frame
        self._scancodes = (
            # TODO
        )

    def poll(self) -> dict:
        # 1. Update SDL's internal array
        sdl.pump()
        
        # 2. Retrieve C-level array values
        state = sdl.poll(self._scancodes)
        
        # 3. Translate raw array values into game semantics
        return {
           # TODO:
        }

class Controller(Device):
    pass