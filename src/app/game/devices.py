"""
@domain.user
@app.device

# Ontology: Source - app.game.devices

**IMPORTANT**: All `libs.core.input` imports should be routed through this module to isolate all input dependencies.
"""
# Standard Libraries
import logging
from typing import (
    Dict,
    Optional,
    Set,
    Tuple
)

# Application Libraries
from app.static.semantics import (
    DeviceContexts,
    Intentions
)
from app.models.configurations import DeviceMapping
from app.models.state import (
    DevicePayload,
    WorldPayload,
    MenuPayload
)

# Cython Libraries
import libs.core.input as sdl

# -------------------------------------------------------

logger = logging.getLogger(__name__)

# -------------------------------------------------------


class Device:
    """
    Abstract base class binding hardware input mappings to DevicePayloads.
    """

    mapping: DeviceMapping

    def __init__(self, mapping: DeviceMapping):
        self.mapping = mapping

    def context(self, map: str) -> None:
        """Switches the active input mapping context."""
        raise NotImplementedError

    def pump(self) -> bool:
        """
        Pumps hardware and OS events once per render frame.
        Returns True if an OS quit signal was observed, False otherwise.
        """
        raise NotImplementedError

    def poll(self) -> DevicePayload:
        """Resolves the active frame's input state into a DevicePayload."""
        raise NotImplementedError


class Keyboard(Device):
    """
    SDL keyboard polling device supporting context isolation, rising-edge
    singular triggers, and consecutive-tick hold accumulation per scancode.
    """

    _context: Optional[str]
    _scancodes: Tuple[int, ...]
    _last_state: Dict[int, int]
    _latched: Set[int]

    def __init__(self, mapping: DeviceMapping):
        super().__init__(mapping)
        self._context = None
        self._scancodes = ()
        self._last_state = {}
        self._latched = set()
        self.context(DeviceContexts.WORLD)

    def context(self, map: str) -> None:
        """Rebuilds active scancode bindings when switching between world and menu contexts."""
        # Guard clause: Do not wipe the input buffer if the context isn't changing
        if self._context == map:
            return

        self._context = map
        if map == DeviceContexts.WORLD:
            i_codes = [v for v in self.mapping.world.intentions.values() if v is not None]
            r_codes = [v for v in self.mapping.world.grips.values() if v is not None]
            g_codes = [v for v in self.mapping.world.goals.values() if v is not None]
            m_codes = [v for v in self.mapping.world.menus.values() if v is not None]
            self._scancodes = tuple(set(i_codes + r_codes + g_codes + m_codes))

        elif map == DeviceContexts.MENU:
            t_codes = [v for v in self.mapping.menu.traversal.values() if v is not None]
            i_codes = [v for v in self.mapping.menu.interactions.values() if v is not None]
            self._scancodes = tuple(set(t_codes + i_codes))

        self._last_state = {code: 0 for code in self._scancodes}
        self._latched.clear()

        logger.debug(f"SDL Scancodes: {self._scancodes}")

    def pump(self) -> bool:
        """
        Pumps the SDL OS event queue once per render frame, latching non-repeat
        keydown scancodes for consumption on the next fixed-timestep tick.
        Returns True if an SDL_QUIT event was observed.
        """
        quit_requested, pressed = sdl.pump()
        if pressed:
            self._latched.update(c for c in pressed if c in self._last_state)
        return quit_requested

    def _is_rising_edge(self, code: int, current_dict: Dict[int, int]) -> bool:
        """Returns True if scancode transitioned down via latched event or state delta."""
        return (code in self._latched) or (
            bool(current_dict.get(code)) and not self._last_state.get(code)
        )

    def poll(self) -> DevicePayload:
        """
        Polls active SDL scancodes, accumulates consecutive press ticks per code,
        and emits rising-edge singular triggers alongside active intention holds.
        """
        current_state = sdl.poll(self._scancodes)
        current_dict = {
            code: (
                1 if code in self._latched else self._last_state.get(code, 0) + 1
            ) if state else 0
            for code, state in zip(self._scancodes, current_state)
        }

        world_payload = WorldPayload()
        menu_payload = MenuPayload()

        if self._context == DeviceContexts.WORLD:
            # Edge-triggered, singular resolution + per-intention hold accumulation
            for k, v in self.mapping.world.intentions.items():
                if v is None:
                    continue
                hold_ticks = current_dict.get(v, 0)
                if hold_ticks:
                    world_payload.holds[k] = hold_ticks
                if world_payload.intention is None and self._is_rising_edge(v, current_dict):
                    world_payload.intention = k

            # Edge-triggered, singular grip resolution (parameterizes Intentions.USE)
            for k, v in self.mapping.world.grips.items():
                if v is not None and self._is_rising_edge(v, current_dict):
                    world_payload.grip = k
                    if not world_payload.intention:
                        world_payload.intention = Intentions.USE
                    break

            # Edge-triggered, singular resolution
            for k, v in self.mapping.world.menus.items():
                if v is not None and self._is_rising_edge(v, current_dict):
                    world_payload.menu = k
                    break

            # Level-triggered, polymorphic accumulation
            for k, v in self.mapping.world.goals.items():
                if v is not None and current_dict.get(v):
                    world_payload.goals.append(k)

        elif self._context == DeviceContexts.MENU:
            # Edge-triggered, singular resolution
            for k, v in self.mapping.menu.traversal.items():
                if v is not None and self._is_rising_edge(v, current_dict):
                    menu_payload.traversal = k
                    break

            # Edge-triggered, singular resolution
            for k, v in self.mapping.menu.interactions.items():
                if v is not None and self._is_rising_edge(v, current_dict):
                    menu_payload.interaction = k
                    break

        self._last_state = current_dict
        self._latched.clear()
        return DevicePayload(world=world_payload, menu=menu_payload)


class Controller(Device):
    pass