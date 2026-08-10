"""
# Ontology: Devices
"""

# Standard Libraries
from typing import Dict

# Application Libraries
from app.config.enums import Directions, Actions, Extensions

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
            self.mapping['directions']['up'],
            self.mapping['directions']['down'],
            self.mapping['directions']['left'],
            self.mapping['directions']['right'],
            self.mapping['extensions']['interact'],
            self.mapping['extensions']['sprint']
        )

    def poll(self) -> dict:
        # 1. Update SDL's internal array
        sdl.pump()
        
        # 2. Retrieve C-level array values
        state = sdl.poll(self._scancodes)
        
        # 3. Translate raw array values into game semantics
        return {
            "direction": self._resolve_direction(state[0:4]),
            "action": Actions.WALK if any(state[0:4]) else None,
            "interact": state[4] == 1,
            "sprint": state[5] == 1
        }

    def _resolve_direction(self, dir_state: tuple) -> str:
        # Resolve conflicting inputs (e.g., pressing Up and Down simultaneously)
        up, down, left, right = dir_state
        if up and not down: return Directions.UP
        if down and not up: return Directions.DOWN
        if left and not right: return Directions.LEFT
        if right and not left: return Directions.RIGHT
        return None

class Controller(Device):
    pass