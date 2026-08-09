# Ontology: Architecture

This section contains an in-depth presentation of the game engine's programmatic architecture.

## Initialization

1. Entrypoint: `Orchestrate`
    * Load Configuration into memory
        - Load Asset Recipes YAML File from `/src/assets/main.yaml`
        - Load Asset Category properties YAML files from `/src/assets/<category>/main.yaml`
        - Load Asset state YAML files from the `/src/data/boards/<board-key>` directory, where `<board-key>` is the selected board. There may be an arbitrary number of state files, with any filename, in the `<board-key>` directory.
        - Convert all heavy Pydantic DTOs into lightweight Plain Old Python Objects (POPOs) and Cython `cdef classes` for runtime use.
        - Initialize list of Asset, injecting (Frame, Animation, Properties, State) components using Asset Recipes in concert with Asset Taxonomy (Category, Instance, ID).
2. Init: `Registry`
    * Load Assets into memory
        - Recursively load `/src/assets/**/*.png` (*not* `.mp3` or `.wav`!). Pydantic Models (DTOs) are used during this phase to read `main.yaml` files and ensure strict schema validation. 
        - Create a map using the key-values `<registry-key>: <frame>`, where `<registry-key>` is calculated according to the Frame schema,
            - Assets with SingleFrame index with `<asset-id>`
            - Assets with BinaryFrames indexed with  `<asset-id>-<idle | activated>`.
            - Assets with StateFrames indexed with `<asset-id>-<action>-<direction>-<frame>`, with `<frame>` starting at 0.
3. Init `Board`
    - Initialize and register the Mechanics (e.g., `PhysicsMechanic`, `CollisionMechanic`, `AnimationMechanic`).
4. Init `Screen`

TODO

### Orchestrator

TODO

### Factory

TODO

## Mechanics

The `Board.play()` method never changes when new game features are added. It simply iterates through the registered Mechanics:

```python
def play(self, delta_time: float) -> None:
    for mechanic in self.mechanics:
        mechanic.update(self, delta_time)
```

Mechanics act as filters. Rather than the Board passing arguments to a system, a Mechanic is responsible for querying the Board for the exact data it cares about.

For example, the `SwitchMechanics` system strictly queries `board.plates`, `board.gates`, and any heavy entities (like `crates` and `sprites`) to resolve trigger logic, leaving the rest of the board untouched. This keeps execution tight and game loops strictly separated by behavior, not nouns.

### General Mechanics

These Mechanics handle general game logic.

- `ProjectileMechanics`: Increment projectile positions, checks intersections and garbage collects, if applicable.
- `AnimationMechanic`: Translates current states into FrameKeys for the renderer.
- `PhysicsMechanic`: (Cython) Adds velocity to position, resolves wall/crate collisions, etc.

### Objective Mechanics

- `SwitchMechanics`: Binds the Gate and Plate states together based on their `switch`.

### Dispositional Mechanics

These Mechanics handle the logic governing the Sprite Disposition Transtion matrix.

- `IntentionMechanic`s: Runs the Disposition transition lambdas, etc.
- `MotionMechanics`: Translates Intentions (hunt, escape, etc.) into physical X/Y velocity vectors, etc.
- `CommerceMechanics`: Translate Intentions (barter, attract, etc.) into trades and price movements.
- `CombatMechanic`: (Cython) Resolves attack hitbox overlaps, decrements health, etc.

## Cython

While Python objects are fast enough for general logic, calculating collisions and processing rendering instructions for thousands of entities requires maximum performance. The engine strategically uses Cython to bridge this gap, adhering to a strict **"Zero Heap Allocation in the Inner Loop"** philosophy to prevent frame stutters caused by the Python Garbage Collector.

### Math & Geometry (`libs/math.pyx`)

Spatial data like are modeled as Cython Extension Types (`cdef class` in `.pxd` definition files).

- Position: 
    - x: int
    - y: int
- Multiple:
    - nx: int
    - ny: int
- Velocity:
    - vx: int
    - vy: int
- Hitbox:
    - position: Position
    - dimension Dimensions
- Attackbox
    - position: Position
    - dimensions: Dimensions

This structure allows geometry methods like `Geometry.intersects` to access spatial properties (e.g., `position.x`, `hb.dimensions.l`) natively at C-speeds.

The engine explicitly retains the Global Interpreter Lock (GIL) during geometry calculations. This safely manages Python reference counts and preserves readable, Pythonic syntax (like `for hb in hitboxes`), while executing the actual mathematical overlap checks inline using primitive C variables on the CPU stack.

### Hardware Rendering (`libs/render.pyx` & `libs/registry.pyx`)

The engine relies on a Cythonized bridge to C-level SDL2 bindings. To mitigate the overhead of crossing the Python-to-C boundary, the rendering pipeline does not pass heavy Python objects (like `SpriteState` or `Dimensions`) to the renderer. Instead, it extracts raw integers on the Python side and unpacks them cleanly onto the C-stack.

- **Context Initialization (`init`):** Sets up an off-screen SDL rendering context (`_renderer`) and window.
- **VRAM Uploads (`load`):** Loads physical image assets from disk directly into GPU memory, returning a safe, reference-counted Python wrapper (`TexturePtr`).
- **Background Compilation (`canvas` & `construct`):** A blank texture (`SDL_TEXTUREACCESS_TARGET`) is created on the GPU to match the full size of the Board. Python passes a single list of flattened integer tuples representing the source/destination coordinates and grid multipliers. Cython unpacks these primitives and executes thousands of `SDL_RenderCopy` calls natively on the GPU. This caches a unified map texture, eliminating the need to instantiate and re-render thousands of background tiles every frame.
- **Frame Rendering (`render`):** During the main game loop, `Screen.draw()` performs lightweight integer-based AABB camera culling natively in Python. This intentionally avoids paying the micro-transaction overhead of calling a Cython function repeatedly inside a massive Python loop. The visible assets are flattened into primitive integer tuples and passed across the C-boundary in a single list. `render()` then clears the screen buffer, copies the cropped background texture, stamps the active primitives, and swaps the buffer to the physical display (`SDL_RenderPresent`).