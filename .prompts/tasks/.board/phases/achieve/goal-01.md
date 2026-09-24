##### Achieve: Goal 01 - Procedural Boundaries

**Overview**

Implementation of emergent spatial boundaries. The engine will dynamically derive an Inclusion Perimeter by calculating the simply-connected outer contour of all Tiles and Objects on a layer, wrapping the playable area without requiring manual YAML state configuration.

To implement a `PerimeterGenerator` module that utilizes a sweep-line algorithm to deduce the map's outer hull at runtime. These bounds are then injected directly into the Cython physics grid as static, invisible constraints.

##### Tasks

**1. Task: Cython Core - Contour Mathematics**

*Objective*: Implement the sweep-line and segment tree algorithms in the math core for maximum performance during map hydration.

* [x] Subtask: In `libs.core.math.geometry.pyx`, implement a 1D Segment Tree structure capable of tracking overlapping intervals and returning their union length.
* [x] Subtask: In `libs.core.math.geometry.pyx`, implement the Sweep-Line algorithm that ingests primitive AABBs and outputs a list of outer contour segments `[(x1, y1, x2, y2), ...]`.

**2. Task: Service Implementation - Perimeter Generator**

*Objective*: Create a high-level Python orchestrator to bridge the Board's Assets with the Cython contour algorithm.

* [x] Subtask: Create `app.services.generators.perimeter.PerimeterGenerator`.
* [x] Subtask: Implement an extraction method that iterates over `board.categories(TILES)` and `board.instances(OBJECTS)` for a specific layer, translating their states into the flattened `(min_x, min_y, max_x, max_y)` format required by the Cython layer.

**3. Task: Migrator Integration**

*Objective*: Hook the procedural generation into the game's loading lifecycle.

* [ ] Subtask: In `Migrator.step()`, add a finalization phase. Once the time-sliced ECS hydration completes for a board, invoke the `PerimeterGenerator` for each active layer.
* [ ] Subtask: Cache the resulting perimeter segments in a new `board.perimeters[layer]` dictionary as lightweight runtime metadata.

**4. Task: Physics Pipeline Injection**

*Objective*: Enforce the inclusion boundary using the existing spatial hash grid.

* [!] Subtask: In `SpatialMechanic.collisions()`, update the pre-processing loop. After hashing the dynamic Assets, iterate through `board.perimeters[layer]` and insert the perimeter segments into the Cython `Space` grid as static ($m=0$) objects.
* [!] Subtask: Ensure `CollisionMechanics` natively bounces dynamic Assets off these infinitely thin segments without requiring new collision math.
    * Replaced with further details. See next section.

##### Task: Physics Pipleine Injection

**1. The Cython Model: `Boundary`**

Instead of returning raw tuples or forcing the use of `Asset`, we introduce a new extension type in `libs.core.models.pyx` called `Boundary`.

* **Structure:** It contains exactly two fields: `Position` and `Dimensions`.
* **Conversion:** When `sweep_contour` generates a segment `(x1, y1, x2, y2)`, it initializes a `Boundary`.
    * If it is a vertical line, `width = 1` and `length = y2 - y1`.
    * If it is a horizontal line, `width = x2 - x1` and `length = 1`.
* **Result:** The `Board` now stores strongly-typed data: `board.perimeters: Dict[str, List[Boundary]]`.

**2. The Two-Phase Spatial Workflow**

In `CollisionMechanics.update()`, we are currently resolving everything in one giant loop. We should split this into two distinct phases. Resolving environmental constraints *before* dynamic body collisions prevents bugs where an Asset is pushed through a wall by another Asset.

```python
# Phase 1: Environmental Constraints (Asset vs Boundary)
# Halt dynamic bodies at the edge of the world.
boundary_collisions = self.constrain(weights, board.perimeters[layer])
for asset, boundary in boundary_collisions:
    self._resolve_boundary(asset, boundary)

# Phase 2: Dynamic Collisions (Asset vs Asset)
# Transfer momentum between physical entities.
asset_collisions = self.collisions(weights)
for asset_a, asset_b in asset_collisions:
    self._resolve_asset(asset_a, asset_b)
```

**3. The Cython Bridge: Bypassing the Hitbox Dilemma**

To make `self.constrain()` work without dummy hitboxes, we create a parallel C-level pipeline optimized specifically for AABB-to-AABB intersection.

**In `geometry.pyx`:**

We decouple the core intersection logic. We write a pure C-level `cdef bint aabb_overlap(...)` function that takes raw coordinates and dimensions.

* The existing `intersects(asset, asset)` function uses this inside its nested hitbox loops.
* We expose a new function, `intersects_boundary(asset, boundary)`, which bypasses hitboxes entirely and just checks the Asset's hitboxes against the Boundary's absolute `aabb_overlap`.

**In `physics.pyx`:**

We introduce a new `cpdef list boundaries(list asset_data, list boundary_data, Space grid)`.

* This function accepts the boundary data natively (no dummy hitboxes required).

**4. Grid Management**

Because we split `CollisionMechanics` into two phases, the `Space` grid becomes extremely elegant to use:

**During `self.constrain()`:**

1. `grid.clear()`
2. Insert the `Boundary` primitives into the grid (assigning them negative IDs to differentiate them from Assets).
3. Insert the `Asset` primitives into the grid.
4. Query the grid. When unpacking the colliding pairs, if an ID is negative, the C-code knows it is a Boundary and routes it to `intersects_boundary()`.
5. Return `List[Tuple[Asset, Boundary]]`.

**During `self.collisions()` (The existing method):**

1. `grid.clear()` (Wiping out the boundaries).
2. Insert only `Asset` primitives.
3. Query and return `List[Tuple[Asset, Asset]]`.

