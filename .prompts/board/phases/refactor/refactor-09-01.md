#### Refactor: Phase 09.01 - Fluid Flows

**Overview** 

Implementing Fluid flow mechanics.

**Objective**

- When Sprites, Players or Pixies intersect a Fluid Effect, they should get swept along the Fluid's `source` direction.
- A specialized object called a Raft shall be introduced. It will not participate in Fluid obstruction, but instead obey the same physics as Sheet Assets, i.e. getting swept in the diretion
- The speed that is imparted to the "flowing" Asset should be proportional to the `flow` of the Fluid Effect `source`, i.e. the higher the flow, the faster the Asset will be swept away. 
- When underying Fluid adjusted velocity, Players and Sprites can still navigate, but no longer obey the laws of kinematic snapping. Instead, the Fluid `flow` is added vectorally to the Sheet velocity. 

**Secondary Objective**

The presence of Fluid flow should influence the RRT pathfinding velocity selection. The question is: in what capacity? 