#### Implement: Phase 08 - RRT Pathfinding

**Goals**: Implement RRT (Rapidly-exploring Random Tree) based pathfinding for the Sprites.

**Toy Implementation of RRT (Pure Python, No Cython)**

```python
import math
import random

class Node:
    """A node in the RRT tree."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None

class RRT:
    def __init__(self, start, goal, obstacle_list, rand_area, step_size=1.0, max_iter=500):
        self.start = Node(start[0], start[1])
        self.goal = Node(goal[0], goal[1])
        self.min_rand, self.max_rand = rand_area
        self.step_size = step_size
        self.max_iter = max_iter
        self.obstacle_list = obstacle_list
        self.node_list = [self.start]

    def plan(self):
        """Executes the RRT algorithm and returns the path if found."""
        for _ in range(self.max_iter):
            rnd_node = self._sample_free_space()
            nearest_node = self._get_nearest_node(self.node_list, rnd_node)
            new_node = self._steer(nearest_node, rnd_node, self.step_size)

            if self._check_collision(nearest_node, new_node, self.obstacle_list):
                self.node_list.append(new_node)

                # Check if the new node is within step size of the goal
                if self._calc_dist(new_node, self.goal) <= self.step_size:
                    self.goal.parent = new_node
                    self.node_list.append(self.goal)
                    return self._generate_final_path()

        return None  # Max iterations reached without finding the goal

    def _sample_free_space(self):
        """Samples a random point in the defined continuous area."""
        # 5% chance to bias the sample directly at the goal to pull the tree forward
        if random.randint(0, 100) > 5:
            return Node(
                random.uniform(self.min_rand, self.max_rand),
                random.uniform(self.min_rand, self.max_rand)
            )
        return Node(self.goal.x, self.goal.y)

    def _steer(self, from_node, to_node, step_size):
        """Generates a new node a fixed step_size away from the nearest node."""
        new_node = Node(from_node.x, from_node.y)
        theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
        
        new_node.x += step_size * math.cos(theta)
        new_node.y += step_size * math.sin(theta)
        new_node.parent = from_node
        
        return new_node

    def _check_collision(self, near_node, new_node, obstacle_list):
        """Checks for intersection with any circular obstacle using point-line segment distances."""
        for (ox, oy, size) in obstacle_list:
            dx = new_node.x - near_node.x
            dy = new_node.y - near_node.y
            dist = math.hypot(dx, dy)
            
            # Sub-step along the segment to ensure the line doesn't cut through a circle
            steps = int(dist / (self.step_size / 2))
            for i in range(steps + 1):
                px = near_node.x + dx * (i / steps) if steps > 0 else near_node.x
                py = near_node.y + dy * (i / steps) if steps > 0 else near_node.y
                
                if math.hypot(px - ox, py - oy) <= size:
                    return False  # Collision detected
        return True  # Collision-free

    def _get_nearest_node(self, node_list, rnd_node):
        """Finds the closest existing node in the tree to the randomly sampled point."""
        distances = [(self._calc_dist(node, rnd_node), node) for node in node_list]
        distances.sort(key=lambda x: x[0])
        return distances[0][1]

    @staticmethod
    def _calc_dist(node1, node2):
        return math.hypot(node1.x - node2.x, node1.y - node2.y)

    def _generate_final_path(self):
        """Backtraces the parents from the goal to the start."""
        path = [[self.goal.x, self.goal.y]]
        node = self.goal.parent
        while node.parent is not None:
            path.append([node.x, node.y])
            node = node.parent
        path.append([self.start.x, self.start.y])
        return path[::-1] # Reverse to output start-to-finish

# Example Usage
if __name__ == '__main__':
    start_pos = (0.0, 0.0)
    goal_pos = (15.0, 15.0)
    # Format: (x, y, radius)
    obstacles = [(5.0, 5.0, 2.0), (8.0, 10.0, 3.0), (12.0, 5.0, 2.0)]
    bounds = (0.0, 20.0)

    rrt = RRT(start=start_pos, goal=goal_pos, obstacle_list=obstacles, rand_area=bounds, step_size=1.5)
    path = rrt.plan()

    if path:
        print("Path successfully found:")
        for point in path:
            print(f"({point[0]:.2f}, {point[1]:.2f})")
    else:
        print("Path blocked or max iterations reached.")
```

!!! note
    Actual implementation in game engine will need to be Cythonized.

##### Overview

**1. The RRT Data Translation (The FIFO Queue)**

The central question of the RRT architectural shift is: *"How does the Sprite step through the RRT return list?"*

In `SpriteState`, `memory.goals` is typed as `Dict[str, Goal]`. Because Python 3.7+ dictionaries preserve insertion order, `CognitionMechanics._remember()` acts as a strict **FIFO (First-In, First-Out) Queue**:

```python
if not sprite.state.goal:
    first = next(iter(sprite.state.memory.goals))
    sprite.state.goal = sprite.state.memory.goals.pop(first)
```

When the RRT algorithm generates a path to a Target (e.g., the Player), it returns a list of coordinates. We can translate this into gameplay by:

1. Converting each coordinate into a `Goal(category=POSITION)`.
2. Inserting them into `memory.goals` sequentially (e.g., keys `wp_1`, `wp_2`, etc.).
3. Re-inserting the overarching `TARGET` Goal at the very end of the dictionary.

As `CognitionMechanics._resolve()` naturally clears the `POSITION` goals when the Sprite gets within `action_radius`, the Sprite will "pop" the next Goal off the dictionary until it finally pops the original `TARGET` goal and resumes direct tracking.

**2. Scope & Bounding the RRT**

Running RRT across the entire `Board` dimensions is computationally wasteful and increases the chance of the tree branching into irrelevant corners of the map.

* **Solution:** The search space should be an Axis-Aligned Bounding Box (AABB) defined by the `Sprite`'s current position and the `Goal`'s current position, expanded by a ~20% padding factor (to be set in `settings.RRT_PADDING`) to allow the tree to route *around* obstacles that sit perfectly flush on the direct vector.

**3. Execution Frequency**

Generating a new RRT on every frame inside `_track()` would instantly lock the Python GIL and crash the framerate. RRT should be treated as an expensive, asynchronous-like operation triggered only by specific edge-case state changes:

1. **Initial Obscuration:** In `_track()`, if a Sprite acquires a `TARGET`/`SUBJECT`/`POSITION`, we project a line to the goal. If `geometry.intersects` detects an intervening Asset with `mass >= 0` (using `board.weights()`), we trigger RRT.
2. **Path Invalidation:** While a Sprite is following a waypoint (`wp_x`), if a dynamic asset (like a pushed `Crate`) moves into the waypoint vector, the path is invalidated. The Sprite dumps its `memory.goals` and recalculates.
3. **Target Deviation:** If the ultimate `TARGET` (e.g., the Player) moves outside a certain tolerance radius from where the RRT originally expected them to be, the path is dumped and recalculated.

**4. Collision Detection Strategy**

Application already possesses `Space` (the Cython spatial hash grid used by `physics.pyx`). However, RRT requires line-segment collision checks, not just AABB overlap.

Since we are avoiding C-level optimizations for now, the Python implementation of RRT can construct a temporary `Hitbox` that perfectly bounds the line segment between `nearest_node` and `new_node`. It can pass this virtual Hitbox to `SpatialMechanics.intersections()` to leverage the existing Cython broad-phase grid for rapid obstacle detection without reinventing the wheel.

##### Goal: RRT Algorithm Integration

Implement a pure Python RRT planner that utilizes the engine's existing spatial architecture for collision detection.

```python
# Pseudo-code for RRT Integration
def plan(start: Position, target: Position, board: Board) -> List[Position]:
    # 1. Define bounded search area (AABB of start/target + padding)
    # 2. Iterate RRT sampling
    # 3. For collision checks, construct a bounding Hitbox for the branch segment
    # 4. Use board.weights() + board.perimeters to check for mass >= 0 overlaps via geometry.intersects
    # 5. Return List[Position] waypoints.

```

##### Goal: Waypoint Memory Mapping

Translate the geometric output of the RRT algorithm into intentional data structures the engine already understands.

```python
# Pseudo-code for Path Injection
def inject_path(sprite: Asset, waypoints: List[Position], final_goal: Goal):
    # 1. Clear existing waypoints in memory
    sprite.state.memory.goals = {k: v for k, v in sprite.state.memory.goals.items() if not k.startswith(settings.RRT_PATH_PREFIX)}
    
    # 2. Inject new waypoints sequentially (Python dicts preserve insertion order -> FIFO)
    for i, wp in enumerate(waypoints):
        name = settings.SEPARATOR.join([settings.RRT_PATH_PREFIX, i])"
        sprite.state.memory.goals[name] = Goal(
            name=name,
            category=Goals.POSITION.value,
            position=wp,
            layer=sprite.state.layer
        )
        
    # 3. Re-append the final goal so it pops last
    sprite.state.memory.goals[final_goal.name] = final_goal

```

##### Tasks

**1. Task: RRT Algorithm Base Implementation**

*Objective*: Create the mathematical RRT planner in the logic utilities.

- [ ] Subtask: Create `app/game/logic/mechanics/modules/paths/plan.py`.
- [ ] Subtask: Implement `Planner` class with `plan()` method.
- [ ] Subtask: Implement dynamic search area bounding (Start to Target + 20% padding).
- [ ] Subtask: Bridge `Planner` collision checks to use `Asset.primitive()` against `board.weights()`.
- [ ] Subtask: Extend collision validation to iterate over `board.perimeters.get(layer, [])` to prevent pathing through static level geometry.

**2. Task: CognitionMechanics Ideation & Tracking**

*Objective*: Hook the RRT planner into the Sprite's sensory loop.

- [ ] Subtask: In `CognitionMechanics._track()`, implement a line-of-sight check to the current `Goal`.
- [ ] Subtask: If line-of-sight is blocked by an Asset with `mass >= 0` OR a `Boundary` from `board.perimeters`, invoke `Planner.plan()`.
- [ ] Subtask: Implement `inject_path()` logic to translate the returned `List[Position]` into `POSITION` goals and push them to `sprite.state.memory.goals`.
- [ ] Subtask: Set `sprite.state.goal = None` immediately after injection to force `_remember()` to pop the first waypoint on the next tick.

**3. Task: Path Recalculation & Invalidation**

*Objective*: Ensure Sprites react dynamically if the environment or target moves while they are traversing a path.

- [ ] Subtask: In `CognitionMechanics._track()`, track the distance delta of the ultimate target. If the target deviates by $> X$ pixels from its position when the RRT was generated, clear the `path-` keys from memory and recalculate.
- [ ] Subtask: If the Sprite is currently seeking a `path-` goal and the line-of-sight to that specific waypoint becomes blocked by a moving weight, clear memory and recalculate.