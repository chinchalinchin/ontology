# Ontology: Architecture

This section contains an in-depth presentation of the game engine's programmatic architecture.

## Initialization

1. Bootstrap
    * Load Configuration into memory
        - Load Asset properties YAML files from `/src/assets/**/main.yaml`
        - Load Asset recipes YAML File from `/src/assets/main.yaml`
        - Load Asset state YAML files from the `/src/data/boards/<board-key>` directory, where `<board-key>` is the selected board. There may be an arbitrary number of state files, with any filename, in the `<board-key>` directory.
        - Convert all heavy Pydantic DTOs into lightweight Plain Old Python Objects (POPOs) and Cython `cdef classes` for runtime use.
        - Initialize homogeneous lists of Asset components.
2. Create `Registry`
    * Load Assets into memory
        - Recursively load `/src/assets/**` using the `main.yaml` contained in each `/src/asset/<category>` directory. Pydantic Models (DTOs) are used *exclusively* during this phase to read `main.yaml` files and ensure strict schema validation.
        - Create a map using the key-values `<registry-key>: <frame>`, where `<registry-key>` is the Asset file name (`<asset-key>`), unless otherwise specified below:
            - Parse and index Chests, Gates and Plates so each frame is indexed with  `<asset-key>-<idle | activated>`.
            - Parse and index Pixie sheets so each frame is indexed with `<asset-key>-<direction>-<frame>`, with `<frame>` starting at 0.
            - Parse and index Sprite sheets so each frame is indexed with `<asset-key>-<action>-<direction>-<frame>`, with `<frame>` starting at 0.
3. Create `Board`
4. Register `Mechanics`
    - Initialize the Mechanics (e.g., `PhysicsMechanic`, `CollisionMechanic`, `AnimationMechanic`).

## Mechanics

The `Board.play()` method never changes when new game features are added. It simply iterates through the registered Mechanics:

```python
def play(self, delta_time: float) -> None:
    for mechanic in self.mechanics:
        mechanic.update(self, delta_time)
```

Mechanics act as filters. Rather than the Board passing arguments to a system, a Mechanic is responsible for querying the Board for the exact data it cares about.

For example, the `SwitchMechanics` system strictly queries `board.plates`, `board.gates`, and any heavy entities (like `crates` and `sprites`) to resolve trigger logic, leaving the rest of the board untouched. This keeps execution tight and game loops strictly separated by behavior, not nouns.

## Cython

While Python objects are fast enough for general logic, calculating collisions requires accessing absolute coordinates (potentially) millions of times per second.

Position, Velocity, and Shape data are modeled as Cython Extension Types (cdef class in `.pxd` definition files). This allows Geometry.intersects (in `libs/math.pyx`) to access properties like `pos.x` natively as C-integers on the stack.

By stripping out the Python Global Interpreter Lock (GIL) and dictionary lookups, collision math resolves with zero garbage collection overhead.

### SDL

The engine relies on a Cythonized bridge to C-level SDL2 bindings, completely skipping Python's Global Interpreter Lock (GIL) during rendering. The flow operates as follows (`libs/render.pyx`, `libs/registry.pyx`):

- **Context Initialization** (`init`): Sets up an off-screen SDL rendering context (`_render`er) and window.
- **VRAM Uploads** (`load`): Loads physical image assets from disk directly into the GPU memory, returning a safe, reference-counted Python wrapper (`TexturePtr`).
- **Background Compilation** (`canvas` & `construct`): A blank texture (`SDL_TEXTUREACCESS_TARGET`) is created on the GPU. By setting it as the active render target, `construct()` iteratively "stamps" all the static background tiles onto it. This creates a unified map texture, eliminating the need to re-render thousands of tiles on every single frame.
- **Frame Rendering** (`render`): During the main loop, render() clears the screen buffer, copies the entire static background texture onto it, stamps all moving active_assets over it, and swaps the buffer to the physical display (`SDL_RenderPresent`).