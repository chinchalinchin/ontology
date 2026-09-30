Backlog: Buoyancy

**0verview**

Generalize hydrodynamic flotation across dynamic objects using declarative `buoyant` properties while decoupling generator services from database cache mutation.

##### Architectural Analysis

###### Property-Driven Dynamic Buoyancy

Currently, `fields.py` explicitly whitelists crates (`asset.instance == AssetInstances.CRATES.value`) when applying current velocity and maintaining buoyancy.

**Proposal**:

* Add `buoyant: bool = False` to `ObjectProperties` in `src/app/models/properties.py`.
* In `fields.update()`, replace instance string matching with property inspection:

```python
if in_fluid:
    if getattr(asset.properties, "buoyant", False):
        asset.state.velocity.vx = flow_vx
        asset.state.velocity.vy = flow_vy
```

* Dynamic objects ($m > 0$) with `buoyant = True` (crates, barrels, wooden chests) float and drift with current flow, while non-buoyant dynamic objects (heavy stone blocks, metal iron crates) sink, maintain friction, and resist drift.

###### Data Model Updates

```python
# src/app/models/properties.py
@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    dimensions: Dimensions
    mass: int = 0
    count: int = 1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)
    buoyant: bool = False
```

###### Field Interception

```python
# src/app/game/logic/modules/motion/fields.py
def update(assets: List[Asset], board: Board, delta: float) -> None:
    rafts = [
        a for a in assets 
        if a.instance == AssetInstances.RAFTS.value
    ]
    _update_rafts(rafts, board)

    for asset in assets:
        if asset.instance in (AssetInstances.RAFTS.value, AssetInstances.PROJECTILES.value):
            continue

        layer = asset.state.layer

        # -------------------------------------------------------------
        # 1. SURFACE HIERARCHY INTERCEPTION (BRIDGES & RAFTS)
        # -------------------------------------------------------------
        # ...

        # -------------------------------------------------------------
        # 2. VIRTUAL EDGE CROSSING (SHORELINES)
        # -------------------------------------------------------------
        # ...

        # -------------------------------------------------------------
        # 3. DIRECT ENVIRONMENTAL FLUID IMMERSION (BUOYANCY)
        # -------------------------------------------------------------
        # ...
        if in_fluid:
            if asset.properties.buoyant:
                asset.state.velocity.vx = flow_vx
                asset.state.velocity.vy = flow_vy
            else:
                asset.state.velocity.vx += flow_vx
                asset.state.velocity.vy += flow_vy
```

##### Goal: Property-Driven Buoyancy & Frictional Decoupling

Incorporate `buoyant: bool = False` into `ObjectProperties`. Update `fields.py` to drive current drift based on property inspection rather than instance matching. Update `frictive.py` to suspend linear friction only for submerged, buoyant assets, allowing non-buoyant dynamic objects to sink, rest on the substrate, and resist water current. Decouple `Actuator` from `Board` cache mutation.

##### Tasks

**1. Task: Property-Driven Buoyancy & Friction Interplay**

*Objective*: Generalize hydrodynamic flotation across dynamic bodies and decouple friction decay based on buoyancy properties.

* [ ] Subtask: Add `buoyant: bool = False` to `ObjectProperties` in `src/app/models/properties.py`.
* [ ] Subtask: Update object configurations in `/src/assets/objects/main.yaml` (`wood-crate`, `wood-barrel` to `buoyant: True`; `iron-crate`, `stone-block` to `buoyant: False`).
* [ ] Subtask: Refactor `fields.py` to inspect `asset.properties.buoyant` on objects, applying current matching only to buoyant entities while sinking non-buoyant objects without current acceleration.
* [ ] Subtask: Refactor `frictive.py` to condition friction suspension on `asset.state.mutators.triggers.submerged and getattr(asset.properties, "buoyant", False)`.
