#### Refactor: Phase 09.01 - Fluid Flows

**Overview** 

Expand Fluid functionality and implement `flow` within FluidMechanics.

**Primary Objective**

- When Sprites and Players (and Pixies, not yet implemented) intersect a Fluid Effect, they should get swept along the Fluid's `source` direction.
- A specialized object called a Raft shall be introduced. It will not participate in Fluid obstruction, but instead obey the same physics as Sheet Assets, i.e. getting swept in the `source` direction
- The speed that is imparted to the "flowing" Asset should be proportional to the `flow` of the Fluid Effect `source`, i.e. the higher the `flow`, the faster the Asset will be swept away. 
- When an underlying Fluid adjusts velocity, Players and Sprites can still navigate, but no longer obey the laws of kinematic snapping. Instead, the Fluid `flow` is added vectorally to the Sheet velocity. 

**Secondary Concerns**

- Removing the obstacle dimensions from the Pool calculations was a mistake, as the background tiles are now visible along the transparent edges of the obstacle (i.e. the obstacle image doesn't fill its dimensions).
- Will probably need to add a mutator to the Sprite state for `submerged`. This needs to trigger a temporary Passive Temporary (Possibly Periodic) Effect, `splash`.
    - Evaluate the feasibility of "submerging" the Sheet Asset, so from the "waist down" (let's say half of `dimensions.l` for now, though we may need a property somewhere to parameterize it) the Sprite frame is darkened/opaque (mimicking the look of a submerged body), with a `splash` effect triggered along the boundary of the submersion. 
    - **NOTE**: This will require the Cradle to spawn the Splash effect.
- The goal of a Raft is to allow Sprites to use it to traverse bodies of Fluids. Consideration needs to be given on how to achieve this sort of relative motion, i.e. the Sprite can move relative to the Raft while aboard and in motion.
- The presence of Fluid flow should influence the RRT pathfinding velocity selection. The question is: in what capacity? Traversing a Fluid needs a "cost", so Sprites can path-find around it.