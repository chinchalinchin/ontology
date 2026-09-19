#### Phase 09: Hydrodynamics

**Overview** 

The overarching goal is setup a system for managing fluid flow.

- A Fluid instance will be separated out of Passive Effects into a distinct Category Instance of Effects.
- An Obstacle Object will be introduced with a Positional State for the sole purpose of blocking Fluid flow.

**Principles**

1. A Fluid Effect has a `source`. A `source` is a Direction.
3. Fluid flows in the Direction of its `source`.
    - In game, this means Fluid Effect assets are multiplied in the downward direction until they meet an Obstacle (m > 0). 
    - **NOTE**: This means a Fluid Effect with  `source = down` may be truncated into a fraction of its dimensions. For example, if a Fluid Effect of 32px x 32px is 48px away (measured from its top left corner) from an Obstacle, the Fluid Effect will be multiplied 1.5 times (32 + 16 = 48) in the `down` direction to achieve a resulting dimension of 32px x 48px.
4. All Board boundaries and non-zero weights are treated as Obstacles.
5. A Fluid effect has a `flow`.
6. A `flow` is a radial parameter that determines the boundaries of the resultant body of water that is formed *around* the obstacle. 
    - **Example**: Suppose an Obstacle with dimensions 10px x 10px at (100, 100) is met by a Fluid Effect with dimensions 10px x 10px travelling in the `down` direction with  `flow = 3`. The Fluid will thus multiply *around* the Obstacle to form a perimeter with vertices (70, 70), (70, 140), (140, 70), (140, 140) and a hole of dimensions 10px by 10px at (100, 100), where the Obstacle is rendered. In this example, `top_left_vertex = (obstacle.position.x - flow * effect.dimensions.w, obstacle.position.y - flow * effect.dimensions.l` and `bottom_right_vertex = (obstacle.position.x + obstacle.dimension.w + flow * effect.dimensions.w, obstacle.position.y + obstacle.dimension.l + flow * effect.dimensions.l)`