"""
# Ontology: app.game.devices

"""
# Standard Libraries
from typing import Dict

# Application Libraries
from app.models.config import Mapping

# Cython Libraries
import libs.core.input as sdl

class Device:
    """
    """

    mapping: Mapping

    def __init__(self, mapping: Mapping):
        self.mapping = mapping

class Keyboard(Device):
    """
    """

    def __init__(self, mapping: Mapping):
        super().__init__(mapping)
        
        # Pre-calculate the tuple of scancodes to query every frame, stripping Nones
        i_codes = [v for v in mapping.intentions.values() if v is not None]
        g_codes = [v for v in mapping.goals.values() if v is not None]
        self._scancodes = tuple(set(i_codes + g_codes))

    def poll(self) -> Mapping:
        """
        """
        # 1. Update SDL's internal array
        sdl.pump()
        
        # 2. Retrieve C-level array values
        state = sdl.poll(self._scancodes)
        state_dict = dict(zip(self._scancodes, state))
        
        # 3. Translate raw array values into game semantics
        res = {"intentions": [], "goals": []}
        for k, v in self.mapping.intentions.items():
            if v is not None and state_dict.get(v):
                res["intentions"].append(k)
        
        for k, v in self.mapping.goals.items():
            if v is not None and state_dict.get(v):
                res["goals"].append(k)
        
        return Mapping(**res)

class Controller(Device):
    pass