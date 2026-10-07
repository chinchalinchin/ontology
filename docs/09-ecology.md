# Ontology: Ecology

The Ecology of the Board is a collection of interacting systems. Assets form the "particles" of this system, while Mechanics play the role of "natural laws". 

**References**

- See [FluidMechanics](./05-mechanics.md#fluidmechanics) for more information on Fluid logic.
- See [SeasonMechanics](./05-mechanics.md#seasonmechanics) for more information on Season mechanics.

## Asset Specifications

### Category: Effects

#### Instance: Fluids

Fluids are directional Effects that project along a `source` Direction until obstructed by an obstacle. Once obstructed, Fluids form Pools around the obstacle and bifuricate into secondary streams.

!!! note
    Because Fluid assets span multiple grid units, they bypass standard geometric height calculation (`pos.y + dim.l`).

**Z-Ordering & Sorting**

Fluids declare an explicit `height: 0` and `depth: -1`. This ensures the [rendering pipeline](./11-architecture.md#graphics) sorts the resulting stream above Tiles but underneath other mutable Assets.

**Branch Model**

* `position: Position`: Absolute origin of the branch corridor.
* `source: str`: Flow direction vector matching or orthogonal to parent stream.
* `flow: int`: Attenuated flow intensity ($flow_{\text{parent}} - 1$).
* `length: int`: Raycast truncation distance.
* `hitboxes: List[Hitbox]`: Compound hitboxes covering the secondary stream corridor.

**Frame: FluidFrame**

* `keys(id, state): returns [ ("{id}-{state.animation.frame}-{slices(state.pool, state.length)}", 0, 0)]` 
* `index(id, properties): returns { "{id}-{properties.count}-{slice(dimensions, directions)}": ( base_x, base_y, slice_w, slice_l ) }`: 

**State: FluidState**

* `layer: Optional[str]`
* `position: Position`
* `source: Directions`
* `flow: int`
* `length: int`
* `pool: Optional[Pool]`
* `branches: List[Branch]`
* `hitboxes: List[Hitbox]`
* `dirty: bool = True`
* `height: Optional[int] = 0`
* `depth: int = -1`
* `_keys: Dict[int, List[Tuple[str, int, int]]] = field(default_factory=dict)` (*Cache for pre-computing fluid keys*)

### Category: Geography

#### Instance: Shorelines

Shorelines are procedural, inanimate Geography sensors instantiated along unoccluded environmental water margins. Rather than belonging to individual fluid emitters, Shorelines are derived at the layer level: `FluidMechanics` aggregates all active fluid streams and annular pools on a layer, derives the outer perimeter hull via `geometry.contours()`, samples bordering substrate tiles from `Board`, and coalesces contiguous segments into cohesive shoreline entities.

**Frame: CardinalFrame**

* Indexes 4 cardinal orientation rows:
    * Row 0: `up`    (Land North/Up, Water South/Down)
    * Row 1: `left`  (Land West/Left, Water East/Right)
    * Row 2: `down`  (Land South/Down, Water North/Up)
    * Row 3: `right` (Land East/Right, Water West/Left)
* `keys(id, state)` emits repeating full tiles along `state.length` and a fractional distal slice for remainders.

**State: ShorelineState**

* `layer: str`
* `position: Position`
* `orientation: str`
* `length: int`
* `thickness: int`
* `bidirectional: bool = True`
* `hitboxes: List[Hitbox]`
* `_keys: Optional[List[Tuple[str, int, int]]] = None` (*Cache for pre-computing frame keys*)

### Category: Resources

Resources are mutable assets deployed onto the Board that progress through discrete structural or biological stages governed by macro-temporal seasons and hydrological fluid diffusion.

**State: ResourceState**

All resource instances (`crops`, `trees`, `ore`) share a unified, slotted state model:

* `layer: str`: Current board layer.
* `position: Position`: Physical coordinate.
* `depth: int = 0`: Dynamic Z-sorting tie-breaker.
* `height: Optional[int] = None`: Geometric height override.
* `stage: str`: Active biological or geological stage key.
* `retention: float = 0.0`: Cumulative moisture level absorbed from adjacent fluid channels.
* `harvested: bool = False`: Flag indicating whether the bloom stage has been harvested.

Stage transitions are evaluated through discrete `Executor` instances mapped to the asset's immutable `properties.lifespan` (`annual`, `perennial`, `centennial`).

#### Instance: Crops

Crops are biological resources whose stage transitions are governed by macro-temporal seasons and soil fluid retention.

- Crop Stages: `sprout`, `growth`, `stalk`, `bloom`, `stump`

#### Instance: Trees

Trees are perennial biological resources that cycle through three life phases (Genesis, Homeostasis, and Apoptosis) based on seasonal calendars and moisture retention thresholds.

- Tree Stages: `sapling`, `bush`, `branch`, `adult`, `vibrant`, `healthy`, `abscise`, `snowcapt`, `dying`, `dead`, `stump`

**Epicycles**

A natural feature of Tree Stage Transitions is the cyclic topology of a finite automata embodying perennial epicycles, i.e. Trees changing colors during the progression of Seasons or possibly dying due to environmental circumstances. Based on the conditions defined in the [Stage Configuration](./appendices/01-schemas.md#configuration-stage), the Tree life cycle is composed of three distinct *epicycles*,

- Genesis
- Homeostasis
- Apoptosis

TODO: mermaid diagram and markdown table

#### Instance: Ores

Ores are mineral resources that transition through structural stages when acted upon by geological forces.

- Ore Stages: `trace`, `deposit`, `nugget`, `vein`, `crystal`, `alloy`

### Category: Tiles

#### Instance: Back

TODO

## Principles

This section contains the Ecological Principles of the game engine.

### Seasons

Tiles undergo Seasons. The Season of a Tile has ripple effects on surrounding Assets. 

1. The Board accumulates the passage of time. 
2. A Season is approximately one hour in realtime. This can be adjusted in `app.config.settings`.
3. Seasons iterate continuously through `spring`, `summer`, `autumn` and `winter`. 
4. Each Season has a Cycle: `onset`, `peak`, `decline`.
5. Each Cycle has an Period. A Period is three frames.
6. The Tile frame that is rendered is dependent on the Season, Cycle and Period.

### Fluid Flow

- Governed by [FluidMechanics](./05-mechanics.md#fluidmechanics)

1. (**Source**) A Fluid has a `source`. A `source` is a Direction. Fluid flows in the Direction of its `source`. 
2. (**Obstruction**) Fluids are obstructed by obstacles. Fluids form Pools around obstacles, determined by their `flow` rate.
3. (**Bifurication**) When a Fluid meets an obstacle, it bifuricates across its orthogonal axes (e.g., a `down` flowing Fluid bifuricates in the `left` and `right` directions) and then continues flowing in its original `source` Direction (e.g. `down`). The number of times a Fluid may bifuricate is equal to its `flow`, e.g. a `flow = 3` means the Fluid may bifuricate three times. In other words, everytime a Fluid bifuricates, its `flow` decreases by 1.
4. (**Fields**) When dynamic Assets (Sprites, Crates, etc.) intersect a Fluid, they acquire a Velocity in the Direction of `source`, getting "swept" away. The speed imparted to an Asset by a Fluid is proportional to its `flow`, i.e. the higher the `flow`, the faster the resulting speed of the "swept" Asset.

### Crop Growth

- Governed by [SeasonMechanics](./05-mechanics.md#seasonmechanics)

1. Crops begin the first Stage of their lifecycle in the first Period of `spring-onset`.
2. Crops end the last Stage of their lifecycle in last Period of `autumn-decline`.
3. Crops can only be harvested in `autumn`, i.e. the `bloom` Stage must occur in `autumn`.
4. Each stage of a Crop lifecycle requires preconditions to be met in order to pass into the next stage, where $\theta_{\text{season}}$ is a Resource property (not setting, i.e. unique to the Instance, but static):
    * $\text{sprout} \to \text{growth}$: $\text{board.season} \in \{\text{spring}, \text{summer}\} \land \text{crop.state.retention} > \theta_{\text{growth}}$
    * $\text{growth} \to \text{stalk}$: $\text{board.season} \in \{\text{spring}, \text{summer}\} \land \text{crop.state.retention} > \theta_{\text{stalk}}$
    * $\text{stalk} \to \text{bloom}$: $\text{board.season} = \text{autumn} \land \text{crop.state.retention} > \theta_{\text{bloom}}$
    * $\text{bloom} \to \text{stump}$: $(\text{board.season} = \text{autumn} \land \text{crop.state.harvested}) \lor \text{board.season} = \text{winter}$

```mermaid
--8<-- "static/mmd/executor-annual-transitions.mmd"
```

--8<-- "static/md/executor-annual-transitions.md"

### Tree Epicycles

- Governed by [SeasonMechanics](./05-mechanics.md#seasonmechanics)

Trees cycle through three epicycles:

1. **Genesis**:
    - $\text{sapling} \to \text{bush} \iff (\text{season} = \text{Spring}) \land (\text{cycle} = \text{Peak}) \land (\text{retention} \ge 15.0)$
    - $\text{bush} \to \text{branch} \iff (\text{season} = \text{Spring}) \land (\text{cycle} = \text{Decline}) \land (\text{retention} \ge 20.0)$
    - $\text{branch} \to \text{adult} \iff (\text{season} = \text{Summer}) \land (\text{cycle} = \text{Onset}) \land (\text{retention} \ge 25.0)$ 
    - $\text{adult} \to \text{healthy} \iff (\text{season} = \text{Summer}) \land (\text{cycle} = \text{Peak}) \land (\text{retention} \ge 25.0)$
2. **Homeostasis**:
    - $\text{healthy} \to \text{abscise} \iff (\text{season} = \text{Autumn}) \land (\text{retention} \ge 15.0)$     
    - $\text{abscise} \to \text{snowcapt} \iff (\text{season} = \text{Winter}) \land (\text{retention} \ge 10.0)$
    - $\text{snowcapt} \to \text{vibrant} \iff (\text{season} = \text{Spring}) \land (\text{retention} \ge 15.0)$     
    - $\text{vibrant} \to \text{healthy} \iff (\text{season} = \text{Summer}) \land (\text{retention} \ge 20.0)$
3. **Apoptosis**:
    - $S_{\text{homeo}} = \{\text{vibrant}, \text{healthy}, \text{abscise}, \text{snowcapt}\}$
    - $\forall s \in S_{\text{homeo}}, \quad s \to \text{dying} \iff \text{retention} < 5.0$
    - $\text{dying} \to \text{vibrant} \iff (\text{season} = \text{Spring}) \land (\text{retention} \ge 20.0)$
    - $\text{dying} \to \text{healthy} \iff (\text{season} = \text{Summer}) \land (\text{retention} \ge 20.0)$     
    - $\text{dying} \to \text{dead} \iff (\text{season} = \text{Autumn}) \land (\text{retention} < 5.0)$     
    - $\text{dead} \to \text{stump} \iff \text{season} = \text{Winter}$     
    - $\text{stump} \to \text{sapling} \iff (\text{season} = \text{Spring}) \land (\text{cycle} = \text{Onset}) \land (\text{period} = 0) \land (\text{retention} \ge 15.0)$

```mermaid
--8<-- "static/mmd/executor-perennial-transitions.mmd"
```

--8<-- "static/md/executor-perennial-transitions.md"

### Ore Veining

TODO

```mermaid
--8<-- "static/mmd/executor-centennial-transitions.mmd"
```

--8<-- "static/md/executor-centennial-transitions.md"
