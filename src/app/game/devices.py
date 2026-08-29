"""
# Ontology: app.game.devices

"""
# Standard Libraries
import logging 

# Application Libraries
from app.models.config import DeviceMapping, WorldMapping, MenuMapping

# Cython Libraries
import libs.core.input as sdl

logger = logging.getLogger(__name__)

class Device:
    """
    """

    mapping: DeviceMapping

    def __init__(self, mapping: DeviceMapping):
        self.mapping = mapping

class Keyboard(Device):
    def __init__(self, mapping: DeviceMapping):
        super().__init__(mapping)   
        self.context('world')

    def context(self, map: str) -> None:
        self._context = map 
        if map == 'world':
            i_codes = [v for v in self.mapping.world.intentions.values() if v is not None]
            g_codes = [v for v in self.mapping.world.goals.values() if v is not None]
            m_codes = [v for v in self.mapping.world.menus.values() if v is not None]
            self._scancodes = tuple(set(i_codes + g_codes + m_codes))

        elif map == 'menu':
            t_codes = [v for v in self.mapping.menu.traversal.values() if v is not None]
            i_codes = [v for v in self.mapping.menu.interactions.values() if v is not None]
            self._scancodes = tuple(set(t_codes + i_codes))

        self._last_state = {code: 0 for code in self._scancodes}

        logger.debug(f"Keyboard initialized mapping to SDL scancodes: {self._scancodes}")

    def poll(self) -> DeviceMapping:
        sdl.pump()
        current_state = sdl.poll(self._scancodes)
        current_dict = dict(zip(self._scancodes, current_state))
        
        # Initialize all lists so Mapping constructor doesn't fail
        world_res = {
            "intentions": [], 
            "goals": [], 
            "menus": []
        }
        menu_res = {
            "traversal": [], 
            "interactions": []
        }
        
        if self._context == 'world':
            for k, v in self.mapping.world.intentions.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    world_res["intentions"].append(k.value if hasattr(k, 'value') else k)
            for k, v in self.mapping.world.menus.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    world_res["menus"].append(k.value if hasattr(k, 'value') else k)
            for k, v in self.mapping.world.goals.items():
                if v is not None and current_dict.get(v):
                    world_res["goals"].append(k.value if hasattr(k, 'value') else k)
                    
        elif self._context == 'menu':
            for k, v in self.mapping.menu.traversal.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    menu_res["traversal"].append(k.value if hasattr(k, 'value') else k)
            for k, v in self.mapping.menu.interactions.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    menu_res["interactions"].append(k.value if hasattr(k, 'value') else k)
        
        self._last_state = current_dict
        return DeviceMapping(
            world=WorldMapping(**world_res),
            menu=MenuMapping(**menu_res)
        )

class Controller(Device):
    pass