#### Implement: Phase 08 - RRT Pathfinding

**Goals**: Implement RRT (Rapidly-exploring Random Tree) based pathfinding for the Sprites.

**Toy Implementation of RRT (Pure Python, No Cython)**

!!! note
    This is just a test example to explore the RRT algorithm. Actual implementation should be in Cython.

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
2. **Path Invalidation:** While a Sprite is following a waypoint (`path-i`), if a dynamic asset (like a pushed `Crate`) moves into the waypoint vector, the path is invalidated. The Sprite dumps its `memory.goals` and recalculates.
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
    # 5. Return List[Position] path segments.

```

##### Goal: Path Memory

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

##### Goal: Line of Sight & Raycasting

Implement the RRT planner. Use the new Cython `segment_intersects` to validate RRT branches against the `Space` grid to avoid false positives from diagonal bounding boxes.

```python
# Pseudo-code for Planner
def plan(start: Position, target: Position, board: Board) -> List[Position]:
    # 1. Define bounded search area (AABB of start/target + padding factor)
    # 2. Iterate RRT sampling.
    # 3. For collision checks, use Cython line-segment math against board.weights() and board.perimeters.
    # 4. Return List[Position] coordinates.
```

##### Tasks: Part I

**1. Task: Cython Geometry Primitives**

*Objective*: Implement `los` and `bisects` in the core math library.

* [x] Subtask: Add `bisects` to `libs/core/math/geometry.pyx` to accurately detect if an RRT branch cuts through an asset's hitbox.
* [x] Subtask: Add `los` (Line of Sight) to `geometry.pyx` utilizing Bresenham's line algorithm to query the `Space` grid natively.
* [x] Subtask: Recompile Cython extensions.

**2. Task: RRT Algorithm Implementation**

*Objective*: Build the planner utility.

* [x] Subtask: Create `app/game/logic/mechanics/modules/paths/plan.py`.
* [x] Subtask: Implement the `Planner` class with the `plan()` method.
* [x] Subtask: Bridge `Planner` collision checks to use the new `segment_intersects` primitive against `board.weights()` and `board.perimeters`.

**3. Task: CognitionMechanics Hook**

*Objective*: Integrate LOS and RRT into the Sprite's sensory loop.

* [!] Subtask: In `CognitionMechanics._track()`, use the Cython `los` primitive to check if the direct vector to the `TARGET`, `SUBJECT` or `OBJECT` is blocked.
* [!] Subtask: If `los` returns `False`, trigger `Planner.plan()`.
* [x] Subtask: Implement the `_path()` function to convert the path into `POSITION` goals, push them to `memory.goals`, push the original goal last, and clear the active `sprite.state.goal`. (This allows `_remember()` to naturally pop the first waypoint on the next tick).

**4. Task: Path Invalidation & Recalculation**

*Objective*: Handle dynamic environment changes during path traversal.

* [!] Subtask: In `_track()`, if the Sprite is currently tracking a `path-` goal, run a quick `los` check to that specific waypoint coordinate. If a dynamic weight (like a pushed Crate) has moved into the path, dump the `path-` goals from memory and recalculate.
* [!] Subtask: When `TransitionMechanics` shifts a Sprite into `ESCAPE` or `WANDER`, explicitly clear any lingering `path-` goals from `memory.goals` so they don't corrupt the new Intention loop.

##### Interlude: The Pathfinding Loop

To get RRT working without breaking the finite state automaton, we must rely on the existing loop. Here is how the engine will natively handle RRT pathing by chaining `CognitionMechanics` and `TransitionMechanics` together:

1. **Acquisition:** A Sprite is in `hunt` or `find`, tracking its `TARGET` / `SUBJECT`.
2. **Obstruction:** `CognitionMechanics._track` runs `geometry.los` and detects a blockage. It triggers `_plan`, pushes the `POSITION` waypoints to `memory.goals`, pushes the original goal last, and sets `current goal = None`.
3. **Standby:** `TransitionMechanics` evaluates the `hunt` ISL. It sees `not sprite.goal` and shifts the Intention to `idle`.
4. **Recall:** On the next tick, `CognitionMechanics._remember` fires (because `intention == IDLE`) and pops `path-0` (a `POSITION` goal) into the active goal.
5. **Traversal:** `TransitionMechanics` evaluates the `idle` ISL. It sees `goal.category == POSITION` and shifts Intention to `wander`. `MotionMechanics` pushes the Sprite to the waypoint.
6. **Resolution:** The Sprite reaches the waypoint. `CognitionMechanics._resolve` sets `goal = None`. `TransitionMechanics` shifts `wander` back to `idle`.
7. **Resumption:** The loop repeats until all waypoints are exhausted and the original `TARGET` is popped in `idle`.

**The Flaw in the Current Matrix:**

The loop is perfect, except for the very last step. When the final `TARGET` goal is popped from memory into the active goal during `idle`, the ISL Matrix currently has **no transition** from `idle` to `hunt`. The Sprite will pop its target and freeze in `idle` indefinitely.

##### Tasks: Part II

**Task 1: Update the Intention Matrix (`src/data/config/intentions/main.yaml`)**

- [x] Add the missing transition rule so the Sprite resumes hunting once the path is consumed and the `TARGET` pops out of memory.

```yaml
  idle:
    # ... existing transitions ...
    - next: hunt
      conditions:
        - sprite.goal
        - sprite.goal.category == constants.Goals.TARGET.value
        - sprite.layer == sprite.goal.layer

```

**Task 2: Implement Planning & Invalidation (`CognitionMechanics._track`)**

Add two specific LOS evaluations in `_track`:

1. [x] **Triggering:** If `goal.category` is an entity (`TARGET`, `SUBJECT`, `OBJECT`), check LOS. If blocked, call `self._plan` (which sets `goal = None`).
2. [x] **Invalidation:** If `goal` is an active waypoint (`name.startswith(RRT_PATH_PREFIX)`), check LOS to the waypoint. If a dynamic asset (like a pushed Crate) obstructs it, clear `path-*` from memory and set `goal = None`. The engine will naturally loop to `idle`, pop the original goal, and replan.

**Task 3: Handle Memory Scrubbing (`CognitionMechanics._resolve`)**

- [!] If a Goal terminates prematurely (e.g., a `TARGET` dies while the Sprite is navigating a path toward them, or the Sprite gives up), `_resolve` sets `goal = None`. Add one line to strip any residual `path-*` strings from `memory.goals` to ensure ghost-paths don't corrupt the next Intention loop.

##### Bug B009: Infinite Wander Loop via Subverted ISL Transitions

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

The Sprite becomes permanently trapped in the `wander` Intention because `CognitionMechanics._project()` undermines `TransitionMechanics`. 

In the game loop, `CognitionMechanics` executes before `TransitionMechanics`. When a Sprite reaches its wander destination, `_resolve()` correctly sets `goal = None`. However, at the end of the same tick, `_project()` evaluates `elif intention == Intentions.WANDER.value:` and immediately randomizes a *new* goal because `not sprite.state.goal` evaluates to True. 

By the time `TransitionMechanics` evaluates the ISL condition for exiting `wander` (`not sprite.goal`), the goal has already been repopulated. The condition fails, and the Sprite loops in `wander` forever.

**Steps to Replicate** 

1. Allow a Sprite to enter the `wander` intention.
2. Wait for the Sprite to reach its randomized `POSITION` goal.
3. Observe the CLI logs: it clears the goal and immediately generates a new one in the same tick, bypassing the transition to `idle`.

**Proposed Remediation**

Remove the `WANDER` goal regeneration from `_project()`. Instead, shift the randomization logic into `_ideate()` during the `IDLE` intention, or simply allow `_project` to pass if the goal was just cleared, letting the engine naturally transition to `idle` on the next tick.

**Notes** 

Not sure I agree with your analysis. While I don't generally like the idea of `_project()` since it is distributing responsibility for Goal creation across the whole class, I am still not inclined to agree with you. Why would a Sprite that needs to stay in `wander` transition into idle? No, the generation of a new `wander` goal is not the issue. The issue is there is no transition from `wander` into `find`. The point of `wander` is to generate a search area when the sprite loses track of a goal. If the goal comes back into sight, it needs to transition into an intention where it can start tracking again. However, the problem here: The ISL Environ conjuncts currently lack the ability to form propositions about particular memories. It only allows categorical claims. The ISL conjuncts need to be able to say: the `cat` such that: `memory_exists(cat) and is_near(memory[indexof(cat)] .position, sprite position) and cat in [TARGET, SUBJECT, OBJECT]`. Obviously not that exact syntax as it needs to evaluate to a true/false, but the general idea is: if memory exists, and the location of the memory is near and the memory is a certain category, then transition from wander into find. 

**Additional Anaylsis**

The initial remediation incorrectly treated `wander` as an ephemeral state that should immediately yield back to `idle`. As noted in your design requirements, `wander` functions as an active, exploratory search loop: when a Sprite loses track of an entity, it should continue generating search waypoints.

The architectural problem stems from two system gaps:

1. **ISL Relational Limitation**: The ISL environment only supports coarse existential checks on memory (e.g., `check_goals(sprite.memory.goals, category)`), lacking the relational capability to evaluate whether a remembered entity's position is within perceptual proximity.
2. **Missing Outbound Transitions in `wander**`: In `src/data/config/intentions/main.yaml`, `wander` only defines exits back to `idle`. There are no transition rules allowing `wander` to shift directly to `find` or `hunt` when a target re-enters perceptual range.
3. **Goal Reacquisition Contract**: When `TransitionMechanics` changes the intention from `wander` to `find` or `hunt`, the active `goal` is still the synthetic `wander` waypoint. In accordance with the engine contract (*CognitionMechanics mutates Goals, TransitionMechanics mutates Intentions*), `CognitionMechanics` must detect the transition out of `wander` and pop the matching goal from `memory.goals`.

#### Tasks: Part III

**Overview** 

Implements relational ISL predicates for remembered entity proximity, adds direct transitions from `wander` to `find`/`hunt`, and wires Goal reacquisition in `CognitionMechanics`.

##### Goal: Relational ISL Memory Predicates

Provide ISL runtime with the capacity to assert whether a remembered entity of a given category is currently near the Sprite's position.

##### Goal: Wander Transition Extensions

Add direct ISL transitions from `wander` to `find` (for `SUBJECT` and `OBJECT` memories) and `hunt` (for `TARGET` memories).

##### Goal: Memory Goal Reacquisition

Ensure `CognitionMechanics` reconciles active goals when an entity transitions from exploratory `wander` to targeted navigation.

##### Tasks

**1. Task: Implement `any_memories_visible` in ISL Environ**

*Objective*: Add a spatial memory query function to `app/services/translators/environ.py`.

- [x] Subtask: Implement `any_memories_visible(sprite, sprites, categories)` in `environ.py`. If the remembered entity is present in `sprites`, validate layer matching and evaluate Euclidean distance against the current character coordinate; otherwise fall back to `goal.position`.
- [x] Subtask: Expose `any_memories_visible` in `Environ.functions`.

**2. Task: Extend Wander Intention Matrix**

*Objective*: Configure outbound transitions in `src/data/config/intentions/main.yaml`.

- [x] Subtask: Add `wander -> hunt` transition conditioned on `functions.any_memories_visible(sprite, sprites, [ constants.Goals.TARGET.value ])`.
- [x] Subtask: Add `wander -> find` transition conditioned on `functions.any_memories_visible(sprite, sprites, [ constants.Goals.SUBJECT.value, constants.Goals.OBJECT.value ])`.

**3. Task: Cognition Goal Reconciliation**

*Objective*: Restore real goals upon intention transitions in `app/game/logic/mechanics/intentional/cognition.py`.

- [x] Subtask: In `CognitionMechanics._resolve()`, if `sprite.state.intention in [Intentions.FIND.value, Intentions.HUNT.value]` and `sprite.state.goal.name == "wander"`, clear `sprite.state.goal = None`.
- [ ] Subtask: In `CognitionMechanics._remember()`, expand recall eligibility beyond `IDLE` so that whenever `sprite.state.goal is None` and `sprite.state.intention in [Intentions.IDLE.value, Intentions.FIND.value, Intentions.HUNT.value]`, the relevant goal is popped from 


##### Bug B012: Unchecked NoneType Dereference in Cognition Tracking on Path Invalidation

**STATUS**: OPEN

**SEVERITY**: CRITICAL

**Description**

In `CognitionMechanics._track()` (`src/app/game/logic/mechanics/intentional/cognition.py`), when a Sprite is following an active waypoint (`is_path = True`), `self._scrap(sprite, board)` is executed to test line of sight against intervening dynamic obstacles. If occluded, `_scrap()` nullifies the active goal via `sprite.state.goal = None`.

However, `_track()` does not check if `sprite.state.goal` was cleared following `self._scrap()`. Execution falls through into the category checks:

```python
        elif goal.category in [
            Goals.POSITION.value,
            Goals.OBJECT.value, 
            Goals.PROPERTY.value
        ]:
            sprite.state.mutators.triggers.vision = True
            self._plan(sprite, board)
            goal = sprite.state.goal
            return

```

`self._plan()` is invoked immediately, executing `sprite.state.goal.position.x`, which raises an unhandled `AttributeError: 'NoneType' object has no attribute 'position'` and halts the engine loop.

**Steps to Replicate**

1. Assign a Sprite an RRT path with generated waypoints (`path-0`, `path-1`, ...).
2. Move a dynamic Crate across the current waypoint vector to invalidate line of sight.
3. Observe crash in `_plan()` called from `_track()`.

**Proposed Remediation**

In `CognitionMechanics._track()`, immediately inspect `sprite.state.goal` after `self._scrap()`:

```python
        if is_path:
            self._scrap(sprite, board)
            if not sprite.state.goal:
                return

```

---

##### Bug B013: Cross-Layer Leak and Unfiltered Obstacle Extraction in CognitionMechanics

**STATUS**: OPEN

**SEVERITY**: HIGH

**Description**

In `CognitionMechanics.obstacles()` (`src/app/game/logic/mechanics/intentional/cognition.py`), dynamic bodies are retrieved via:

```python
for asset in board.instances(AssetInstances.CRATES.value):

```

1. `board.instances()` is called without specifying the `layer` argument. It queries `_all_instances`, returning all Crates across every board layer. Crates positioned on subterranean or elevated layers are mistakenly injected as collision rectangles into the current layer's RRT planner.
2. Obstacle retrieval queries only `AssetInstances.CRATES.value`, bypassing other impassable entities with mass $m \ge 0$ (such as closed `GATES`, `STRUTS`, or other sheet entities). The active line was commented out (`# for asset in board.weights(layer):`).

**Steps to Replicate**

1. Place a Crate on `layer_2` at coordinate $(100, 100)$.
2. Run RRT pathfinding for a Sprite on `layer_1` traversing coordinate $(100, 100)$.
3. The planner fails or routes around $(100, 100)$ despite `layer_1` being completely clear.

**Proposed Remediation**

In `CognitionMechanics.obstacles()`, restore `board.weights(layer)` to filter obstacles strictly by the Sprite's active layer:

```python
        for asset in board.weights(layer):
            if asset.name in exclude:
                continue
            obstacles.append((
                asset.state.position.x,
                asset.state.position.y,
                asset.dimensions.w,
                asset.dimensions.l
            ))

```

---

### Suggested Documentation Updates

#### 1. `docs/04-intentions.md` (Intentions & Transitions)

* Update the **Intentional Scripting Language (ISL)** section to document the `functions.check_memory_near` predicate. Clarify that while the Intention Transition Matrix evaluates transitions via finite automata rules, memory predicates bridge dynamic world perceptions to remembered goals.
* Document the **Exploratory State Pattern**: Clarify that navigational states such as `wander` are persistent search modes that do not cycle through `idle` upon waypoint arrival; instead, they continue sampling local coordinates until perceptual predicates trigger edge-triggered shifts into directed tracking (`find` / `hunt`).

#### 2. `docs/05-mechanics.md` (Spatial & Mathematical Primitives)

* In the **Geometry (`libs/core/math/geometry.pyx`)** section, document the Liang-Barsky $\epsilon$-penetration rule. Note that segments sharing a boundary or vertex contact where $t_{exit} \le t_{enter} + \epsilon$ are defined as non-occluding.
* Explicitly state that line of sight evaluations model ray propagation through volume rather than surface contact, preventing $t=0$ boundary self-occlusions during navigation tracking.