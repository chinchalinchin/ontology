#### Refactor: Phase 10.01 - Stage Hitboxes

**Overview**

Refactor resource hitbox schemas to support stage-dependent collision geometry across biological and geological lifecycles. Allow `ResourceProperties.hitboxes` to be defined as either uniform lists or stage-indexed dictionaries in property indices, resolve hitboxes dynamically in `Asset.hitboxes` without heap allocation, prevent erroneous whole-dimension fallback when empty collision bounds are intentional, and configure stage-accurate trunk and juvenile footprints for trees and crops in asset configurations.

##### Architectural Analysis

#### 1. The Conflict with Static Hitbox Architecture

In `src/app/assets/base.py`, hitbox resolution evaluates as follows:

```python
@property
def hitboxes(self) -> List[Hitbox]:
    state_hbs = getattr(self.state, "hitboxes", None)
    if state_hbs is not None:
        return state_hbs
    hbs = self.properties.hitboxes
    if not hbs and self.dimensions:
        hbs = [Hitbox(Position(0, 0), self.dimensions)]
    return hbs

```

When `hitboxes: null` is configured on `ResourceProperties`:

1. `hbs` resolves to `None`.
2. `if not hbs and self.dimensions` assigns a fallback hitbox covering the entire entity bounding box (`(0, 0, 94, 137)` for a deciduous tree).
3. This creates two simulation bugs:
* **Full-Canopy Obstruction**: In top-down 2.5D perspective, characters must walk behind the tree canopy (depth sorted by $y + l$). Obstructing the full $94 \times 137$ box makes the entire air canopy impassable.
* **Juvenile Collision Imbalance**: A `sapling` (a 12px plant) shares the identical physical obstacle footprint as a mature $94 \times 137$ `adult` tree.



#### 2. Constraints

* **Immutability of Properties**: `AssetProperties` are static and must never mutate at runtime.
* **Zero Allocation in the Inner Loop**: Reconstructing `Hitbox` objects or allocating lists on each collision frame degrades performance.
* **Uniform Sprite Atlas Bounds**: In `StageFrame`, each stage cell occupies an identical $(w, l)$ slice ($94 \times 137$) along the horizontal strip. The coordinate space for hitboxes across all stages remains normalized relative to the cell's top-left origin $(0, 0)$.

#### 3. Resolution: Stage-Indexed Hitbox Mapping

Mirror the existing `SheetProperties.attackboxes` pattern:

* Allow `ResourceProperties.hitboxes` to accept either:
* A static `List[Hitbox]` (for uniform entities like boulders or ores).
* A stage dictionary `Dict[str, List[Hitbox]]` mapping biological stages (`sapling`, `bush`, `adult`, `stump`) to localized collision boxes.


* Update `Asset.hitboxes` to evaluate:
```python
if isinstance(hbs, dict):
    stage = getattr(self.state, "stage", None)
    if stage and stage in hbs:
        return hbs[stage]
    return hbs.get("default", [])

```


* Because `ResourceProperties` is pre-instantiated at boot, indexing `hbs[stage]` returns a cached `List[Hitbox]` in $O(1)$ time with zero heap allocation. When `SeasonMechanics` mutates `resource.state.stage`, the active collision footprint updates on the following frame.

---

##### Specifications

###### Hitbox Mapping Schema

In `/src/assets/resources/main.yaml`, `hitboxes` accepts stage-keyed dictionary mappings:

```yaml
resources:
  trees:
    deciduous:
      dimensions:
        w: 94
        l: 137
      lifespan: perennial
      loot: wood
      mass: 0
      hitboxes:
        sapling:
          - position: { x: 42, y: 122 }
            dimensions: { w: 10, l: 12 }
        bush:
          - position: { x: 36, y: 114 }
            dimensions: { w: 22, l: 20 }
        branch:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        adult:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        vibrant:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        healthy:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        abscise:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        snowcapt:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        dying:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        dead:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        stump:
          - position: { x: 30, y: 115 }
            dimensions: { w: 34, l: 18 }

```

###### Fallback Correction

In `Asset.hitboxes`, the condition `if not hbs and self.dimensions:` erroneously converts intentional empty hitboxes (`hitboxes: []` or `hitboxes: { sapling: [] }`) into full-dimension obstacles. The fallback must only trigger when `hbs is None`.

##### Architectural Analysis

###### Zero-Allocation Resolution in Inner Loops

`CollisionMechanics` and `NavigationMechanics` query `asset.hitboxes` and `asset.primitive()` at 60 Hz.
By compiling the stage dictionary into static Pydantic/Cython `Hitbox` model instances during boot-time YAML loading, querying `hbs[resource.state.stage]` is an $O(1)$ reference lookup returning an existing immutable list.

```
Frame Loop (60 Hz)
  │
  ├─► CollisionMechanics / NavigationMechanics:
  │     Query asset.hitboxes
  │       │
  │       ├─► 1. Check state.hitboxes (Dynamic overrides: fluids, shorelines)
  │       │
  │       ├─► 2. Check properties.hitboxes:
  │       │     ├─► Is dict: Return properties.hitboxes.get(state.stage, default)
  │       │     └─► Is list: Return properties.hitboxes
  │       │
  │       └─► 3. Fallback: If hbs is None, return [Hitbox(0, 0, dimensions)]

```

###### Decoupling from SeasonMechanics

Because `Asset.hitboxes` references `state.stage` directly, `SeasonMechanics` does not need to synchronize hitboxes or dispatch collision invalidation events upon stage transitions. Updating `resource.state.stage` instantly changes the spatial boundary seen by all spatial queries on the subsequent frame.

##### Goals

###### Goal: Polymorphic Hitbox Property Modeling

Extend `ResourceProperties.hitboxes` to support `Union[List[Hitbox], Dict[str, List[Hitbox]], None]`. Ensure Pydantic type adapters validate both linear lists and stage-keyed dictionaries seamlessly.

###### Goal: Dynamic Stage Resolution in Foundational Asset

Refactor `Asset.hitboxes` in `app.assets.base` to inspect `self.state.stage` when `self.properties.hitboxes` is a dictionary, and fix the `not hbs` fallback check to preserve intentionally passable entities (`[]`).

###### Goal: Environmental Footprint Calibration

Author stage-accurate trunk and base hitboxes for `deciduous` trees, passability rules for `lettuce` crops, and update the CLI state dump template to serialize stage hitbox dictionaries cleanly.

##### Tasks

**1. Task: Resource Hitbox Schema & Model Extension**

*Objective*: Support stage-indexed hitbox dictionaries across data models and YAML schemas.

* [ ] Subtask: Update `ResourceProperties` in `app.models.properties` to type `hitboxes: Optional[Union[List[Hitbox], Dict[str, List[Hitbox]]]]`.
* [ ] Subtask: Verify Pydantic adapter validation in `app.models.adapters` for stage-keyed dictionary structures.
* [ ] Subtask: Configure stage hitboxes for `trees.deciduous` in `/src/assets/resources/main.yaml` constraining adult collision to trunk bounds (`(36, 110, 22, 24)`).
* [ ] Subtask: Configure passable hitboxes (`null` or `[]`) for juvenile stages and crops in `/src/assets/resources/main.yaml`.

**2. Task: Asset Hitbox Retrieval Refactoring**

*Objective*: Update `Asset.hitboxes` to dynamically resolve stage hitboxes with zero allocations.

* [ ] Subtask: Update `Asset.hitboxes` in `app.assets.base` to check `isinstance(self.properties.hitboxes, dict)` and return `self.properties.hitboxes.get(self.state.stage, [])`.
* [ ] Subtask: Replace `if not hbs and self.dimensions` with `if hbs is None and self.dimensions` to prevent converting empty lists into full bounding boxes.
* [ ] Subtask: Ensure `Asset.primitive()` cleanly passes the resolved stage hitboxes into Cython spatial collision arrays.

**3. Task: State Dump Serialization & Verification**

*Objective*: Support stage hitbox dictionaries in diagnostic dumping tools and test suites.

* [ ] Subtask: Update `/src/data/templates/state.md` to handle `props.hitboxes` when structured as a stage dictionary.
* [ ] Subtask: Write unit tests verifying that `tree.hitboxes` reflects trunk dimensions when `stage = "adult"` and stump dimensions when `stage = "stump"`.
* [ ] Subtask: Execute live verification via `python src/cli.py --dump-state start` ensuring character navigation walks behind tree canopies without collision stalls.