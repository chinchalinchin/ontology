#### Refactor: Phase 09.02 - Shorelines & Geography

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

##### User Review

**Core Problem To Keep In Mind**: Fluids are deployed by the state. Shorelines are dependent on Fluid deployments.

- It seems as though Geography would be better served as an Object, not an Effect. Shorelines aren't animated; they are an inanimate Asset. 
- To head off future refactors, it might be better to define and layout the whole procedural generation pipeline now rather than later. Shorelines are implicitly connected to the Fluid generation so they should probably stay in the `app.services.generators.game.actuator`, although with the introduction of Geography, it seems likely there will eventually be an `app.services.generators.game.terraformer` to construct physical Geography. Right now there is an implicit pipeline in the Migrator, starting with Perimeter, now with the addition of the Actuator.
- If Geography is separated into an Object, keeping it as an attribute of the FluidState is still the correct move, I believe.
- Perhaps Geography should be a category unto itself? It is a question of where the "concreteness" of Geography resides. When Actuator pumps a Fluid, it needs to generate a concrete instance of something, with the instantiation referring to a physical Asset file. If Geography is treated as a Category, and a Shoreline as an Instance, say, then the Actuator still has a "degree of a freedom" in which shoreline asset to deploy. Which actually maps to the Assets which are available, i.e. there are grassy shorelines, rocky shorelines, icy shorelines, etc., ready to be codified and added to the engine.
  - This would require some sort of additional field to either Fluid properties or Fluid state to account for what type of shoreline it generates.
- With respect to shorelines there is an added complication of how to arrange the frames. I think frames arranged in horizontal rows of (w, l) that correspond to the cardinal directions (NORTH, WEST, SOUTH, EAST). So the NORTH frame contains a shoreline along (0, 0) to (w, 0), WEST from (0, 0) to (0, l), SOUTH from (0, l) to (w, l) and EAST from (w, 0) to (w, l). 
  - But then, what defines the width of the shorelines themselves? The dimensions of the frame don't map to these dimensions. This is what hitboxes are for, actually.
- **Aesthetic (Very Unimportant) Question**: Is Geography the correct term here? Shouldn't it be Geology? 