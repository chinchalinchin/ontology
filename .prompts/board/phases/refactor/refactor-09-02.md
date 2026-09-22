### Architectural Analysis: Shorelines & Virtual Edge Hydrodynamics

---

### 1. Taxonomy & Asset Placement

#### `Category: Effects` vs. Dedicated `Category: Geography`

In the engine’s Entity-Component-System (ECS) architecture:

* **Category** dictates the *Properties Model* (`AssetProperties`) loaded at boot time via `src/assets//main.yaml`.
* **Instance** dictates the *State Model* (`AssetState`) hydrated dynamically on the `Board`.

Placing Shorelines under `AssetCategories.EFFECTS` as `AssetInstances.SHORELINES` (or `GEOGRAPHY`) has distinct advantages:

1. **Property Alignment:** Shorelines frequently require frame-animation for water lapping, waves, or foam cascades. `EffectProperties` already contains `LifecycleProperties` (`continuous`, `periodic`, `temporary`), `count`, and `dimensions`, avoiding the creation of an entirely redundant Category root in `PropertiesSchema`.
2. **Dynamic Generation:** If shorelines are generated procedurally by `Actuator` when a fluid stream pumps or truncates, they behave as environmental effects coupled to the life of the fluid emitter rather than static terrain tiles.

```
                  AssetCategories.EFFECTS
                             │
     ┌──────────────┬────────┴─────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼              ▼
  fluids         passive        hazards      collectables    shorelines
(FluidState)  (AnimatorState) (HazardState)   (LotState)   (ShorelineState)

```

---

### 2. State & Actuator Coupling: Independent Assets vs. Child Geometry

A key design fork is whether Shorelines exist on the `Board` as independent `Asset` instances or as composite geometric metadata within `FluidState`.

#### The Dynamic Churn Problem

When a Crate is pushed across a fluid stream, `FluidMechanics` sets `fluid.state.dirty = True`. `Actuator.pump()` recalculates raycasts, truncates lengths, and resizes pools.

* **If Shorelines are Independent Board Assets:** `Actuator` must continuously call `board.remove(old_shores)` and `board.add(new_shores)`, invalidating `Board` spatial grid caches, layer caches, and character tables on every tick a dynamic body moves.
* **If Shorelines are Bound to Fluid:** `FluidState` holds a collection of procedural perimeter descriptors (e.g., `shores: List[ShorelineBoundary]`). `Actuator.pump()` updates them in-place.

**Recommendation:** Treat Shorelines as independent `Asset` instances managed through `Cradle`, but assign them a direct parent reference `fluid_name: str`. When `Actuator.pump()` executes, it clears and rebuilds only the shoreline assets tagged with that fluid's name, preventing full board cache churn.

---

### 3. The "Virtual Edge" & Ledge Transition Mechanics

The proposal to treat the shoreline as a virtual edge that triggers a "fall" / hop into the water solves the visual ambiguity of the submersion channel.

```
       [ DRY TERRAIN ]             [ SHORELINE ]              [ FLUID STREAM ]
                                 (w_shore / l_shore)
     ──┬─────────────────────────┬───────────────────────────┬───────────────────
       │                         │                           │
       │                         │  Footprint crosses edge:  │
       │                         │  1. Positional Shift (Δs) ───►  Submerged = True
       │                         │  2. Cradle.spawn(splash)  │     Current Applied
       │                         │                           │

```

#### Traversal Mechanics

1. **The Crossing Condition:**
Immersion should trigger when the entity’s *sensory anchor / footprint* $(x + \frac{w}{2}, y + l)$ crosses the shoreline sensor boundary from the dry side to the wet side.
2. **Positional Shift ($\vec{\delta}_{\text{shore}}$):**
When the entity commits across the virtual edge, add an orthogonal displacement vector pointing into the water:

$$\vec{\delta}_{\text{shore}} = \begin{cases}    (0,\, +l_{\text{shore}}) & \text{North bank (entering South)} \\    (0,\, -l_{\text{shore}}) & \text{South bank (entering North)} \\    (+w_{\text{shore}},\, 0) & \text{West bank (entering East)} \\    (-w_{\text{shore}},\, 0) & \text{East bank (entering West)}    \end{cases}$$

This instantaneous shift visually simulates stepping down off a bank or hopping off a ledge, clearing the edge boundary in a single frame.
3. **Transition Triggering:**
The moment $\vec{\delta}_{\text{shore}}$ applies:

* `mutators.triggers.submerged` switches to `True`.
* `Cradle.spawn_passive("splash", layer, pos)` instantiates the water splash particle.
* The entity is now squarely inside the fluid hitbox; `fields.py` immediately begins imparting $\vec{v}_{\text{current}}$.

4. **Bi-Directional vs. One-Way Ledges:**
* **Cliffs / Sheer Banks:** One-way. Once in the water, the shoreline edge acts as an obstacle ($m = 0$) preventing the sprite from climbing back out.
* **Beaches / Shallow Banks:** Bi-directional. Crossing from water onto the shore clears `submerged = False` and negates current velocity.



---

### 4. Rendering & Frame Multipliers (`FluidFrame` Reuse)

Can `FluidFrame` be reused for shorelines?

Yes. `FluidFrame` already handles:

1. Dynamic length expansion.
2. Integer multiple tile repetition (`length // dim`).
3. Fractional sub-pixel truncation slicing (`length % dim`).

#### Necessary Adaptation: Orthogonal Orientation

In `FluidFrame`, the textures tile *along* the direction of the fluid (`source`). A shoreline, however, tiles *along* the border of the stream (e.g., an East shoreline runs along the Y-axis for a North-South fluid, but its visual face points West into the water).

* Either parameterize `FluidFrame` with an `axis: Axis.PARALLEL | Axis.ORTHOGONAL` setting, or create a specialized `ShorelineFrame(Frame)` that accepts `(orientation: Directions, length: int)`.
* **Z-Ordering:** Shorelines must declare:

$$\text{depth} = 0, \quad \text{height} = 0$$

This ensures the shoreline sorts *above* the underlying water (`depth: -1`) so the transparent water-lapping foam renders over the fluid, while characters (`depth: 0, height = y + l`) sort cleanly on top.

---

### Codebase Changes Required

1. **Schemas & Enums (`models/properties.py`, `config/enums.py`):**
* Add `SHORELINES = "shorelines"` to `AssetInstances`.
* Add `shorelines: Dict[str, EffectProperties]` to `EffectPropertyInstances`.


2. **State Models (`models/state/objects.py`):**
* Create `ShorelineState(AssetState)`: contains `position`, `orientation: Directions`, `length: int`, `bidirectional: bool`, `parent_fluid: str`.


3. **Asset Frame (`assets/frames/core.py`):**
* Generalize `FluidFrame` or implement `ShorelineFrame` to tile cardinal border segments (`north`, `south`, `east`, `west`) with distal edge slicing.


4. **Actuator Perimeter Decomposition (`services/generators/game/actuator.py`):**
* Update `Actuator` to calculate perimeter flanks of active streams and annular pools.
* Dispatch shoreline generation to construct bounding shore sensors along unoccluded fluid borders.


5. **Environmental Motion & Virtual Edge (`logic/modules/motion/fields.py`):**
* Intercept shoreline crossings.
* Apply positional shift $\vec{\delta}_{\text{shore}}$, spawn splash particles, and toggle `mutators.triggers.submerged`.



---

### Task Board Phase Specification

```markdown
#### Backlog: Phase 09.02 - Shorelines & Virtual Edge Hydrodynamics

**Overview**

Eliminates abrupt fluid boundary transitions and visual submersion-channel clipping by introducing procedural Shoreline assets along fluid perimeters. Implements virtual edge mechanics that simulate stepping down into water, applying an instantaneous positional shift, triggering waterline splash particles, and synchronizing character submersion states with environmental geometry.

##### Goal: Shoreline Taxonomy, Schemas & Recipes

Register `shorelines` under `AssetCategories.EFFECTS`. Define `ShorelineState` to track orientation, length, and parent fluid emitter links. Configure asset recipes supporting 4-way cardinal shoreline profiles (`north`, `south`, `east`, `west`) with animated foam lifecycles.

```yaml
# Property Recipe Concept
effects:
  shorelines:
    shoreline-grass-water:
      dimensions:
        w: 32
        l: 16
      lifecycle:
        type: continuous
        delay: 30
      count: 3
      hitboxes: null
      mass: -1

```

##### Goal: Procedural Shoreline Generation in Actuator

Expand `Actuator` to generate shoreline perimeters around active fluid corridors and annular pools during `pump()`. Shorelines are dynamically generated on unoccluded fluid flanks, tracking fluid stream lengths and truncations.

```python
# Actuator Perimeter Flank Calculation
def _generate_shorelines(self, fluid: Asset, stream_length: int, pool: Optional[Pool], board: Board) -> List[Asset]:
    # Compute perimeter flank bounding boxes along East, West, North, and South unoccluded boundaries
    # Construct ShorelineState instances tied to parent fluid name
    pass

```

##### Goal: Virtual Edge Traversals & Ledge Drop Mechanics

Implement virtual edge traversal logic in `fields.py`. When an entity's sensory footprint crosses a shoreline sensor into open water, apply an orthogonal positional shift equal to the shoreline thickness, spawn splash particles, toggle `mutators.triggers.submerged = True`, and impart environmental current.

```python
# Virtual Edge Spatial Shift
if crossing_shoreline_into_water:
    asset.state.position.x += shore_delta_x
    asset.state.position.y += shore_delta_y
    asset.state.mutators.triggers.submerged = True
    board.cradle.spawn_passive("splash", layer, splash_pos)

```

##### Goal: Sliced Shoreline Frame Component

Implement `ShorelineFrame` (or adapt `FluidFrame`) to dynamically tile and slice shoreline assets across variable corridor lengths and pool perimeters using cardinal orientation schemas.

##### Tasks

**1. Task: Schemas, Models & Asset Recipes**

*Objective*: Integrate shoreline definitions into engine taxonomy and configuration registries.

* [] Subtask: Add `SHORELINES` to `AssetInstances` enum in `app/config/enums.py`.
* [] Subtask: Add `shorelines: Dict[str, EffectProperties]` to `EffectPropertyInstances` schema in `app/models/properties.py`.
* [] Subtask: Implement `ShorelineState` with `orientation`, `length`, `bidirectional`, and `parent_fluid` fields in `app/models/state/objects.py`.
* [] Subtask: Add recipes for cardinal shoreline assets in `recipes/main.yaml`.

**2. Task: Shoreline Frame Indexing & Slicing**

*Objective*: Render repeating and sliced shoreline segments along variable stream lengths.

* [] Subtask: Implement `ShorelineFrame` in `app/assets/frames/core.py` supporting cardinal crop indexing (`north`, `south`, `east`, `west`).
* [] Subtask: Add fractional distal slicing for shoreline edges meeting truncated boundaries.
* [] Subtask: Verify shoreline Z-ordering defaults (`depth = 0`, `height = 0`) to layer foam over water tiles.

**3. Task: Procedural Shoreline Generation**

*Objective*: Automatically instantiate and synchronize shoreline entities with fluid geometry.

* [] Subtask: Add `_calculate_shoreline_flanks()` to `Actuator` in `app/services/generators/game/actuator.py`.
* [] Subtask: Generate flank bounds for linear stream corridors based on emitter `source` and `length`.
* [] Subtask: Generate outer flank bounds for annular obstacle pools.
* [] Subtask: Add `cradle.spawn_shoreline()` and manage child shoreline lifecycles during `Actuator.pump()`.

**4. Task: Virtual Edge Motion & Immersion Transitions**

*Objective*: Resolve edge crossing physics, positional shifting, and submersion gating.

* [] Subtask: Add shoreline sensor intersection checks in `app/game/logic/modules/motion/fields.py`.
* [] Subtask: Implement orthogonal positional shift $\vec{\delta}_{\text{shore}}$ upon water entry.
* [] Subtask: Gate `mutators.triggers.submerged = True` strictly to entities past the shoreline edge.
* [] Subtask: Dispatch `cradle.spawn_passive("splash", ...)` at the shoreline crossing coordinate.
* [] Subtask: Configure reverse traversal logic for bi-directional banks vs. one-way ledges.

```

```