##### Bug B055: Phantom Rising-Edge Input Across Context Switches in `Keyboard.context`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/devices.py` (`Keyboard.context`), switching between `DeviceContexts.WORLD` and `DeviceContexts.MENU` unconditionally initializes `self._last_state = {code: 0 for code in self._scancodes}`. When a physical key is mapped in both contexts (e.g., `ESC` mapped to `world.menus.pause` and `menu.interactions.cancel`, or `SPACE`/`E` mapped to `world.intentions.interact` and `menu.interactions.select`), and remains physically depressed across the context transition (a typical human key press lasts 5–9 ticks at 60 FPS), the very next `Keyboard.poll()` observes `current_dict[code] == 1` and `self._last_state[code] == 0`, emitting a spurious rising edge in the new context. This causes a newly opened menu to be immediately cancelled/selected or a world action to fire immediately upon closing a menu.

**Steps to Replicate** 

1. Map the same SDL scancode (e.g., `ESC`) to `world.menus.pause` and `menu.interactions.cancel`.
2. Press and hold `ESC` in `DeviceContexts.WORLD` for > 2 ticks: tick 1 emits `WorldPayload(menu='pause')`, opening the Pause menu.
3. On context switch via `device.context(DeviceContexts.MENU)`, `self._last_state[ESC]` is reset to `0` while `ESC` is still down.
4. On the next tick, `device.poll()` emits `MenuPayload(interaction='cancel')`, immediately dismissing the Pause menu on the same physical keypress.

**Proposed Remeditation**

Seed `self._last_state` in `Keyboard.context` from the live keyboard state returned by `sdl.poll(self._scancodes)` (`{code: 1 if state else 0 for code, state in zip(self._scancodes, sdl.poll(self._scancodes))}`) so keys already held across a context switch must be released and pressed again before emitting a rising edge.
