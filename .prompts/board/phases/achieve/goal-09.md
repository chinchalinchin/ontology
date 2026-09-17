#### Achieve: Goal 09 - CLI Handling

**Overview**

Normalize CLI startup parameters to decouple direct state loading from Main Menu navigation, and remediate interpreter-level teardown faults. Specifically, convert `<board-key>` into an optional short-circuit on the `start` command, implement a graceful signal-trapping shutdown routine, eliminate use-after-free conditions across the Cython-to-SDL boundary, and instrument diagnostic tracing for segmentation faults.

##### Bug B008: Segmentation Fault on Process Exit via Post-SDL_Quit Texture Deallocation

**STATUS**: OPEN

**SEVERITY**: High

**Description**

When `cli.py start` exits (either normally or via `^C`), the CLI executes `quit_sdl()`, which destroys the active `SDL_Renderer` and calls `SDL_Quit()`. However, `TexturePtr` and `TTFFont` objects cached in `Registry` and `Screen` still exist in Python memory. During subsequent Python interpreter teardown (`Py_FinalizeEx`), the garbage collector invokes the Cython `__dealloc__` methods on these wrappers, calling `SDL_DestroyTexture` and `TTF_CloseFont` against freed driver memory. This causes an immediate segmentation fault during process exit.

**Steps to Replicate**

1. Run `python src/cli.py start world-01`.
2. Wait for the engine to boot into the game loop.
3. Terminate the process using `Ctrl + C`.
4. Observe the console output:

```bash
2026-09-16 18:14:45,746 - INFO - __main__ - CLI processes completed.
Segmentation fault (core dumped)

```

**Proposed Remediation**

Introduce explicit texture destruction routines in `Registry` and `Screen`. In `cli.py`, invoke `engine.stop()`, purge all cached textures, and force a `gc.collect()` to guarantee all `TexturePtr` and `TTFFont` instances are freed before invoking `quit_sdl()`. In Cython (`libs/graphics/render.pyx` and `registry.pyx`), add sentinel checks confirming `_renderer != NULL` before calling `SDL_DestroyTexture`.

##### Goal: Optional Board Key CLI Short-Circuit

Refactor the CLI parser and orchestration bootstrapping so `board_key` is optional for live game execution (`start`), while remaining strictly required for headless export utilities (`prerender`, `render`, `map`).

When `board_key` is omitted:

* The CLI orchestrates an unhydrated board.
* The Engine enqueues an initial `MenuEvent(id=Menus.MAIN.value)` onto the bus.
* The player enters the Main Menu to trigger new or saved world generation.

When `board_key` is provided:

* The CLI bypasses the Main Menu entirely.
* The Engine suppresses `MenuEvent(id=Menus.MAIN.value)` and enqueues `StateEvent(id=board_key)`.
* Execution proceeds straight into time-sliced hydration for the target state.

```python
# app/cli.py
p_start = subparsers.add_parser("start")
p_start.add_argument("board_key", type=str, nargs="?", default=None,
                     help="Optional board key to bypass the Main Menu and start immediately.")

```

```python
# app/services/orchestration/constructors.py -> Orchestrator.orchestrate
if state_key is not None:
    engine.bus.append(StateEvent(id=state_key))
else:
    engine.bus.append(MenuEvent(id=Menus.MAIN.value))

```

##### Goal: Teardown Order & Post-SDL_Quit Deallocation Remediation

The segmentation fault occurring immediately after `CLI processes completed.` is a textbook C-extension destruction ordering fault:

1. **Renderer/Texture Inversion**: In SDL2, all `SDL_Texture` handles instantiated by a renderer must be destroyed *before* calling `SDL_DestroyRenderer`.
2. **Post-Quit Garbage Collection**: Cython extension types (`TexturePtr`, `TTFFont`) implement `__dealloc__` to invoke `SDL_DestroyTexture` and `TTF_CloseFont`. In `cli.py`, `quit_sdl()` destroys `_renderer` and calls `SDL_Quit()` while references to `TexturePtr` and `TTFFont` remain anchored in `Registry`, `Screen`, or stack frames.
3. **Interpreter Finalization (`Py_FinalizeEx`)**: When the Python interpreter exits, cyclic GC sweeps the remaining objects. `TexturePtr.__dealloc__` attempts to call `SDL_DestroyTexture` against a destroyed renderer and closed video subsystem, causing an invalid memory pointer dereference (`SIGSEGV`).
4. **Intensive Session Freezing**: Unhandled segmentation faults trigger Linux core dump handlers (such as `systemd-coredump` or `apport`), writing massive memory dumps to disk in the background while holding GPU locks, producing visible system lockups.

```
+-----------------------------------------------------------------------------------+
| Faulting Teardown Flow (Current)                                                  |
| cli.py -> del engine -> quit_sdl() [SDL_Quit] -> Py_FinalizeEx -> __dealloc__ -> SIGSEGV |
+-----------------------------------------------------------------------------------+
| Normalized Teardown Flow (Remediated)                                             |
| Engine.stop() -> Registry.clear() -> Screens.clear() -> gc.collect() -> quit_sdl()|
+-----------------------------------------------------------------------------------+

```

##### Goal: Fault Diagnostics & Signal Telemetry Plan

To isolate any lingering low-level faults or race conditions during interruption:

* **Python Trace Trapping**: Run with Python fault handling enabled (`PYTHONFAULTHANDLER=1 python src/cli.py ...`), forcing Python to dump the exact C call stack on SIGSEGV.
* **Signal Decoupling**: Register POSIX signal handlers (`signal.SIGINT`, `signal.SIGTERM`) that toggle `engine.running = False` rather than raising asynchronous `KeyboardInterrupt` exceptions inside active C memory operations.
* **Core Dump Throttling**: If core dumps continue during debugging, inspect stack traces via `coredumpctl gdb` and temporarily restrict dump creation with `ulimit -c 0`.

##### Tasks

**1. Task: CLI Board Key Argument Decoupling**

*Objective*: Allow `start` to boot without arguments into the Main Menu while preserving headless subcommands.

* [x] Subtask: Update `cli.py` argument parser to define `board_key` as `nargs="?"`, defaulting to `None` for the `start` subcommand.
* [x] Subtask: Keep `board_key` as required positional argument for `prerender`, `render`, and `map`.
* [x] Subtask: Update `Orchestrator.orchestrate` to handle `state_key=None` by populating only core menus and emitting `MenuEvent(id=Menus.MAIN.value)`.
* [x] Subtask: Add conditional check in `Orchestrator` to emit `StateEvent(id=state_key)` directly when `state_key` is provided.

**2. Task: Clean Resource Teardown and Shutdown Pipeline**

*Objective*: Enforce strict destruction order so all SDL textures and surfaces are released before calling `quit_sdl()`.

* [x] Subtask: Implement `Registry.clear()` to explicitly iterate, destroy, and nullify all `TexturePtr` and `TTFFont` objects held in `_textures` and `_fonts`.
* [x] Subtask: Implement `Engine.stop()` to drain active screens, destroy screen canvas textures, and clear all board references.
* [x] Subtask: Update `cli.py` teardown to invoke `engine.stop()`, clear `Screen` references, and execute `gc.collect()` *prior* to calling `quit_sdl()`.
* [x] Subtask: Add null pointer checks (`if target.ptr != NULL and _renderer != NULL`) inside `TexturePtr.__dealloc__` and `render.destroy` to prevent calling SDL against a torn-down driver.

**3. Task: Signal Handling and Diagnostic Instrumentation**

*Objective*: Prevent abrupt `KeyboardInterrupt` corruption during rendering operations and verify C-level stack traces.

* [x] Subtask: Install graceful signal handlers in `cli.py` for `signal.SIGINT` and `signal.SIGTERM` setting `engine.running = False`.
* [x] Subtask: Enable `faulthandler.enable()` at CLI entry point to output C-level tracebacks if a segmentation fault occurs.
* [x] Subtask: Verify consecutive start/stop iterations with `^C` execute without segmentation faults or resource leakage.
