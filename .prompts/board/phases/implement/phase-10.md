#### Implement: Phase 10 - Seasons

**Overview** 

Implement Seasonal Mechanics.

- Tile Seasons
- Resource Stages

**Context**

Currently Tiles are single frames with no animations. 

**Tile Specifications**

Tile Assets will be arranged in rows according to the following schema,

- Tile Seasons: `spring`, `summer`, `autumn`, `winter` 
    - Cycles per Season: `onset`, `peak`, `decline`
    - Frames Per Cycle: 3

For a total of 12 frames per row and a total count of 36 tiles. For example, the first row will be,

- `spring-onset-0`, `spring-onset-1`, `spring-onset-2`, `spring-peak-1`, `spring-peak-2`, `spring-peak-3`, `spring-decline-1`, `spring-decline-2`, `spring-decline-3`

Each row will denote a Season.

**Resource Specifications**

Resources will be arranged in horizontal rows according to Stages. Each Instance of Resource will have unique Stages.

- Crop Stages: `sprout`, `growth`, `stalk`, `bloom`, `stump`
    - **Note**: Distributed over `spring`, `summer` and `autumn`. Hibernates over `winter`. Initializes during the onset of `spring`.
- Ore Stages: `trace`, `deposit`, `nugget`, `vein`, `crystal`, `alloy`


!!! note
    Ore is not the principal target of this phase, but is included in the specification to ensure Resource properties are abstracted correctly for reuse.

**Seasonal Principles**

1. The Board accumulates the passage of time. 
2. A Season is approximately one hour in realtime. This can be adjusted in `app.config.settings`.
3. Seasons iterate continuously through `spring`, `summer`, `autumn` and `winter`. 
4. Each Season has a Cycle: `onset`, `peak`, `decline`.
5. Each Cycle has an `period`. A period is three frames.
6. The Tile frame that is rendered is dependent on the Season, Cycle and Period.

**Resource Lifecycles**

1. Crops begin their lifecycle in the first period of `spring-onset`.
2. Crops end their lifecycle in last period of `autumn-decline`.
3. Crops can only be harvested in `autumn`, i.e. the `bloom` lifecycle must occur in `autumn`.
4. Each stage of a Crop lifecycle requires preconditions to be met in order to pass into the next stage:
    - `if resource.state.stage == sprout and board.season in [spring, summer] and resource.state.fluid_retention > GROWTH_THRESHOLD: transition(growth)`
    - `if resource.state.stage == growth and board.season in [spring, summer] and resource.state.stage.fluid_retention > STALK_THRESHOLD: transition(stalk)`
    - `if resource.stage.stage == stalk and board.season == autumn and resource.state.stage.fluid_retention > BLOOM_THRESHOLD: transition(bloom)`
    - `if (resource.state.stage == bloom and board.season == autumn and resource.state.harvested) or (board.season == winter): transition(stump)`