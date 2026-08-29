"""
# Ontology: app.game.devices

"""
# Standard Libraries
import logging 

# Application Libraries
from app.config.enums import DeviceContexts
from app.models.config import DeviceMapping
from app.models.state import (
    DevicePayload,
    WorldPayload,
    MenuPayload
)

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
    """
    """
    def __init__(self, mapping: DeviceMapping):
        super().__init__(mapping)   
        self._context = None
        self.context(DeviceContexts.WORLD)

    def context(self, map: str) -> None:
        # Guard clause: Do not wipe the input buffer if the context isn't changing
        if getattr(self, '_context', None) == map:
            return
            
        self._context = map 
        if map == DeviceContexts.WORLD:
            i_codes = [v for v in self.mapping.world.intentions.values() if v is not None]
            g_codes = [v for v in self.mapping.world.goals.values() if v is not None]
            m_codes = [v for v in self.mapping.world.menus.values() if v is not None]
            self._scancodes = tuple(set(i_codes + g_codes + m_codes))

        elif map == DeviceContexts.MENU:
            t_codes = [v for v in self.mapping.menu.traversal.values() if v is not None]
            i_codes = [v for v in self.mapping.menu.interactions.values() if v is not None]
            self._scancodes = tuple(set(t_codes + i_codes))

        self._last_state = {code: 0 for code in self._scancodes}

        logger.debug(f"SDL Scancodes: {self._scancodes}")

    def poll(self) -> DevicePayload:
        sdl.pump()
        current_state = sdl.poll(self._scancodes)
        current_dict = dict(zip(self._scancodes, current_state))
        
        world_payload = WorldPayload()
        menu_payload = MenuPayload()
        
        if self._context == DeviceContexts.WORLD:
            # Edge-triggered, singular resolution
            for k, v in self.mapping.world.intentions.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    world_payload.intention = k
                    break
            
            # Edge-triggered, singular resolution
            for k, v in self.mapping.world.menus.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    world_payload.menu = k
                    break
            
            # Level-triggered, polymorphic accumulation
            for k, v in self.mapping.world.goals.items():
                if v is not None and current_dict.get(v):
                    world_payload.goals.append(k)
                    
        elif self._context == DeviceContexts.MENU:
            # Edge-triggered, singular resolution
            for k, v in self.mapping.menu.traversal.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    menu_payload.traversal = k
                    break
            
            # Edge-triggered, singular resolution
            for k, v in self.mapping.menu.interactions.items():
                if v is not None and current_dict.get(v) and not self._last_state.get(v):
                    menu_payload.interaction = k
                    break
        
        self._last_state = current_dict
        return DevicePayload(world=world_payload, menu=menu_payload)

class Controller(Device):
    pass