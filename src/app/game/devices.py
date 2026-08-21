"""
# Ontology: app.game.devices

"""
# Standard Libraries
import logging 

# Application Libraries
from app.models.config import Mapping

# Cython Libraries
import libs.core.input as sdl

logger = logging.getLogger(__name__)

class Device:
    """
    """

    mapping: Mapping

    def __init__(self, mapping: Mapping):
        self.mapping = mapping

class Keyboard(Device):
    def __init__(self, mapping: Mapping):
        super().__init__(mapping)
        
        i_codes = [v for v in mapping.intentions.values() if v is not None]
        g_codes = [v for v in mapping.goals.values() if v is not None]
        self._scancodes = tuple(set(i_codes + g_codes))
        
        # Track the snapshot of the previous frame
        self._last_state = {code: 0 for code in self._scancodes}
        
        logger.debug(f"Keyboard initialized mapping to SDL scancodes: {self._scancodes}")

    def poll(self) -> Mapping:
        sdl.pump()
        current_state = sdl.poll(self._scancodes)
        current_dict = dict(zip(self._scancodes, current_state))
        
        res = {"intentions": [], "goals": []}
        
        # 1. Edge-Triggered Intentions (Only trigger if 0 -> 1)
        for k, v in self.mapping.intentions.items():
            if v is not None and current_dict.get(v):
                if not self._last_state.get(v):  # The key was NOT held last frame
                    key_val = k.value if hasattr(k, 'value') else k
                    res["intentions"].append(key_val)
        
        # 2. Level-Triggered Goals (Movement is continuous)
        for k, v in self.mapping.goals.items():
            if v is not None and current_dict.get(v):
                key_val = k.value if hasattr(k, 'value') else k
                res["goals"].append(key_val)
        
        # 3. Update the state tracker for the next tick
        self._last_state = current_dict
        
        return Mapping(**res)

class Controller(Device):
    pass