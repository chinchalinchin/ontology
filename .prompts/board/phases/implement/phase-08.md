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

##### Goal: Relational ISL Memory Predicates

Provide ISL runtime with the capacity to assert whether a remembered entity of a given category is currently near the Sprite's position.

##### Goal: Wander Transition Extensions

Add direct ISL transitions from `wander` to `find` (for `SUBJECT` and `OBJECT` memories) and `hunt` (for `TARGET` memories).

##### Goal: Memory Goal Reacquisition

Ensure `CognitionMechanics` reconciles active goals when an entity transitions from exploratory `wander` to targeted navigation.

##### Tasks: Part III

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
- [x] Subtask: In `CognitionMechanics._remember()`, expand recall eligibility beyond `IDLE` so that whenever `sprite.state.goal is None` and `sprite.state.intention in [Intentions.IDLE.value, Intentions.FIND.value, Intentions.HUNT.value]`, the relevant goal is popped from 

##### Final Boss: RRT Path Generation Bug

Up to this point, this line in the CognitionMechanics has been intentionally hiding a bug whose source yet to be pinpointed, in order to streamline and get the Goal-Intention logic working correctly around the pathfinding. Everything is currently working to spec. However, when this line is changed from,

```python
for asset in board.instances(AssetInstances.CRATES.value, layer):

# for asset in board.weights(layer):
```

To:

```python
# for asset in board.instances(AssetInstances.CRATES.value, layer):

for asset in board.weights(layer):
```

A bug enters into the application. To fully understand the bug, first set the scene.

**Properties**

```yaml
# ------------------------------------------------------------------
# ----------------------------------------------------------- CRAFTS
crafts:
  struts:
    # ----------------------------------------------------- FRAMES
    frame-adobe:
      dimensions:
        w: 96
        l: 160
      mass: 0
      hitboxes:
        - position: 
            x: 0
            y: 0
          dimensions:
            w: 96
            l: 160
      cost:
        - item: clay
          quantity: 10
    frame-brick:
      dimensions:
        w: 96
        l: 190
      mass: 0
      hitboxes:
        - position: 
            x: 10
            y: 20
          dimensions:
            w: 76
            l: 144
      cost:
        - item: stone
          quantity: 10
    # ----------------------------------------------------- FENCES
    fence-horizontal:
      dimensions:
        w: 72
        l: 73
      mass: 0
      hitboxes:
        - position: 
            x: 0
            y: 0
          dimensions:
            w: 72
            l: 73
      cost:
        - item: wood
          quantity: 10
    fence-vertical:
      dimensions:
        w: 8 
        l: 87
      mass: 0
      hitboxes:
        - position: 
            x: 0
            y: 0
          dimensions:
            w: 8
            l: 87
      cost:
        - item: wood
          quantity: 10
    # ----------------------------------------------------- FLOORS
    floor-wood:
      dimensions:
        w: 128
        l: 96
      mass: -1
      cost: 
        - item: wood
          quantity: 10
    # ----------------------------------------------------- WALLS
    wall-blue:
      dimensions:
        w: 128
        l: 96
      mass: 0
      cost: 
        - item: wood
          quantity: 10
      hitboxes:
        - position:
            x: 6
            y: 17
          dimensions:
            w: 116
            l: 54
    wall-castle:
      dimensions:
        w: 222
        l: 133
      mass: 0
      cost: 
        - item: stone
          quantity: 100
      hitboxes:
        - position:
            x: 178
            y: 102
          dimensions:
            w: 25
            l: 12
        - position: 
            x: 17
            y: 102
          dimensions:
            w: 25
            l: 12
        - position:
            x: 5
            y: 39
          dimensions:
            w: 203
            l: 63
objects:
  doors:
    door-castle-open:
      mass: -1
      dimensions:
        w: 64
        l: 64
    door-double:
      mass: -1
      dimensions:
        w: 64
        l: 64
    door-dungeon:
      mass: -1
      dimensions:
        w: 32
        l: 48
    door-mansion:
      mass: -1
      dimensions:
        w: 32
        l: 48
    door-house:
      mass: -1
      dimensions: 
        w: 32
        l: 48
    door-shadow:
      mass: -1
      dimensions:
        w: 32
        l: 48
    door-open:
      mass: -1
      dimensions:
        w: 32
        l: 57
    door-shack:
      mass: -1 
      dimensions:
        w: 32
        l: 48
```

**Initial State**

```yaml
sheets:
  sprites: 
    - id: jasilynn
      name: evil-empress-jasilynn
      layer: brick-house-compose-layer
      depth: 0
      position:
        x: 175
        y: 200
      meters:
        health: 
          current: 50
          maximum: 100
        magic: 
          current: 100
          maximum: 100
      character:
        strength: 5
        defense: 5
        speed: 50
        impulse: 25
      mutators:
        parameters:
          fear:
            radius: 128
            limit: 0.50
            enemy: 5
          vision:
            radius: 128
          action:
            radius: 25
      psyche:
        dialogue: greeting
        expression: null
        motivation: conquest
        persona: empress-jasilynn
      intention: find
      goal:
        name: player
        category: subject
        layer: '0'
        position:
          x: 100
          y: 200
      memory:
        goals:
          player:
            name: player
            category: subject
            layer: '0'
            position:
              x: 100
              y: 200
        prices: null
        property: null
        relationships: 
          player: friend
        rumors: null
        sprites: 
          player:
            x: 100
            y: 200
      inventory: 
        loot: null
        equipment:
          armor: null
          tool: null
          utility: null
          weapon: shortsword
          shield: null
        wallet: 0
sheets:
  players: 
    - id: player
      name: player
      layer: '0'
      depth: 0
      position:
        x: 10
        y: 80
      meters:
        health: 
          current: 50
          maximum: 100
        magic: 
          current: 100
          maximum: 100
      character:
        strength: 5
        defense: 5
        speed: 100
        impulse: 25
      mutators:
        parameters:
          action:
            radius: 30
      inventory: 
        loot: null
        equipment:
          armor: null
          tool: null
          utility: null
          weapon: shortsword
          shield: buckler
        wallet: 0
```

**Obstacles Are Only Crates Logs (All is Well)**

```bash
2026-09-11 20:32:45,208 - INFO - __main__ - Starting CLI with command: 'start' for board: 'world-01'
2026-09-11 20:32:45,209 - INFO - __main__ - Igniting engine for live execution...
2026-09-11 20:32:45,209 - INFO - app.services.orchestration.constructors - Loading YAML data for target state: world-01 ...
2026-09-11 20:32:45,209 - INFO - app.config.loader - Loading YAML property schemas...
2026-09-11 20:32:45,333 - INFO - app.config.loader - Loading YAML configurations...
2026-09-11 20:32:45,489 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-11 20:32:45,553 - INFO - app.services.orchestration.constructors - Initializing SDL and Cython rendering subsystems...
2026-09-11 20:32:45,773 - INFO - app.services.orchestration.constructors - Constructing Empty Board and Migrator subsystem...
2026-09-11 20:32:45,774 - INFO - app.game.board - Initializing Board with 0 incoming assets.
2026-09-11 20:32:45,775 - INFO - app.game.board - Board completely hydrated and initialized.
2026-09-11 20:32:45,776 - INFO - app.services.orchestration.constructors - Initializing Registry...
2026-09-11 20:32:45,792 - INFO - app.services.orchestration.constructors - Injecting Generators and Devices into Board...
2026-09-11 20:32:45,793 - INFO - app.services.orchestration.constructors - Building rendering pipelines, mechanics, and UI...
2026-09-11 20:32:45,794 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 480x480)
2026-09-11 20:32:45,809 - INFO - app.services.orchestration.constructors - Engine successfully assembled.
2026-09-11 20:32:45,809 - INFO - app.game.engine - Entering Game Loop...
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
2026-09-11 20:32:46,745 - INFO - app.services.orchestration.migrator - Migrator starting hydration for target state: world-01
2026-09-11 20:32:46,746 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-11 20:32:46,819 - INFO - app.services.generators.perimeter - Calculating dynamic perimeter boundaries for layer: 0
2026-09-11 20:32:46,820 - INFO - app.services.generators.perimeter - Derived simply-connected hull containing 4 edges.
2026-09-11 20:32:46,820 - INFO - app.services.generators.perimeter - Calculating dynamic perimeter boundaries for layer: brick-house-compose-layer
2026-09-11 20:32:46,820 - INFO - app.services.generators.perimeter - Derived simply-connected hull containing 8 edges.
2026-09-11 20:32:46,820 - INFO - app.game.menus.controllers.load - Hydration complete. Reallocating rendering canvases...
2026-09-11 20:32:46,821 - INFO - app.game.screen - Rebaking Screen canvases for new world state...
2026-09-11 20:32:46,887 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 480x480)
2026-09-11 20:32:46,889 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn tracked Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(197, 292))
2026-09-11 20:32:49,192 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> interact
2026-09-11 20:32:49,209 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn resolved Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(197, 292))
2026-09-11 20:32:49,209 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): interact -> idle
2026-09-11 20:32:49,226 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn remembered Goal(category=subject, name = player, layer = 0, position=(100, 200))
2026-09-11 20:32:49,226 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): idle -> find
2026-09-11 20:32:52,426 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> speak
2026-09-11 20:32:52,443 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): speak -> idle
2026-09-11 20:32:53,693 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): idle -> find
2026-09-11 20:32:56,744 - INFO - app.game.engine - [TELEMETRY] Avg FPS: 54.9 |Avg UPS (Ticks): 59.9
2026-09-11 20:33:01,429 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> speak
2026-09-11 20:33:01,446 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): speak -> idle
2026-09-11 20:33:02,146 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): idle -> find
2026-09-11 20:33:05,547 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn abandoned Goal(category=subject, name = player, layer = 0, position=(451, 459))
2026-09-11 20:33:05,548 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> idle
2026-09-11 20:33:05,564 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): idle -> wander
2026-09-11 20:33:05,580 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn randomized Goal(category=position, name = wander, layer = 0, position=(330, 553))
2026-09-11 20:33:06,752 - INFO - app.game.engine - [TELEMETRY] Avg FPS: 60.0 |Avg UPS (Ticks): 60.0
2026-09-11 20:33:08,770 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn resolved Goal(category=position, name = wander, layer = 0, position=(330, 553))
2026-09-11 20:33:08,770 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn randomized Goal(category=position, name = wander, layer = 0, position=(440, 524))
2026-09-11 20:33:10,754 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): wander -> find
2026-09-11 20:33:10,770 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn dropped Goal(category=position, name = wander, layer = 0, position=(440, 524))
2026-09-11 20:33:10,770 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn remembered Goal(category=subject, name = player, layer = 0, position=(412, 501))
2026-09-11 20:33:12,971 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> speak
2026-09-11 20:33:12,987 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): speak -> idle
^C2026-09-11 20:33:14,648 - INFO - __main__ - Game engine loop interrupted by user.
2026-09-11 20:33:14,649 - INFO - __main__ - Generating state dump...
2026-09-11 20:33:14,751 - INFO - __main__ - State dump successfully written to /home/grant/Projects/ontology/20260911_203314.state-dump.md
2026-09-11 20:33:14,898 - INFO - __main__ - CLI processes completed.
```

Note: Sprite correctly transitions through all Intentions, popping and pushing Goals accordingly.

**Obstacles Are Weight (Kaboom)**

```bash
2026-09-11 20:34:58,950 - INFO - __main__ - Starting CLI with command: 'start' for board: 'world-01'
2026-09-11 20:34:58,950 - INFO - __main__ - Igniting engine for live execution...
2026-09-11 20:34:58,950 - INFO - app.services.orchestration.constructors - Loading YAML data for target state: world-01 ...
2026-09-11 20:34:58,950 - INFO - app.config.loader - Loading YAML property schemas...
2026-09-11 20:34:59,103 - INFO - app.config.loader - Loading YAML configurations...
2026-09-11 20:34:59,311 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-11 20:34:59,397 - INFO - app.services.orchestration.constructors - Initializing SDL and Cython rendering subsystems...
2026-09-11 20:34:59,631 - INFO - app.services.orchestration.constructors - Constructing Empty Board and Migrator subsystem...
2026-09-11 20:34:59,632 - INFO - app.game.board - Initializing Board with 0 incoming assets.
2026-09-11 20:34:59,632 - INFO - app.game.board - Board completely hydrated and initialized.
2026-09-11 20:34:59,632 - INFO - app.services.orchestration.constructors - Initializing Registry...
2026-09-11 20:34:59,647 - INFO - app.services.orchestration.constructors - Injecting Generators and Devices into Board...
2026-09-11 20:34:59,648 - INFO - app.services.orchestration.constructors - Building rendering pipelines, mechanics, and UI...
2026-09-11 20:34:59,648 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 480x480)
2026-09-11 20:34:59,665 - INFO - app.services.orchestration.constructors - Engine successfully assembled.
2026-09-11 20:34:59,666 - INFO - app.game.engine - Entering Game Loop...
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
2026-09-11 20:35:00,745 - INFO - app.services.orchestration.migrator - Migrator starting hydration for target state: world-01
2026-09-11 20:35:00,745 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-11 20:35:00,837 - INFO - app.services.generators.perimeter - Calculating dynamic perimeter boundaries for layer: 0
2026-09-11 20:35:00,837 - INFO - app.services.generators.perimeter - Derived simply-connected hull containing 4 edges.
2026-09-11 20:35:00,837 - INFO - app.services.generators.perimeter - Calculating dynamic perimeter boundaries for layer: brick-house-compose-layer
2026-09-11 20:35:00,838 - INFO - app.services.generators.perimeter - Derived simply-connected hull containing 8 edges.
2026-09-11 20:35:00,838 - INFO - app.game.menus.controllers.load - Hydration complete. Reallocating rendering canvases...
2026-09-11 20:35:00,838 - INFO - app.game.screen - Rebaking Screen canvases for new world state...
2026-09-11 20:35:00,916 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 480x480)
2026-09-11 20:35:00,918 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn tracked Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(197, 292))
2026-09-11 20:35:00,921 - INFO - app.game.logic.mechanics.intentional.cognition - Line-of-sight blocked for evil-empress-jasilynn. Triggering RRT.
2026-09-11 20:35:00,923 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn abandoned Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(197, 292))
2026-09-11 20:35:00,924 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> idle
2026-09-11 20:35:00,925 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn remembered Goal(category=subject, name = player, layer = 0, position=(100, 200))
2026-09-11 20:35:00,926 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn tracked Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(197, 292))
2026-09-11 20:35:00,926 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): idle -> find
2026-09-11 20:35:00,927 - INFO - app.game.logic.mechanics.intentional.cognition - Line-of-sight blocked for evil-empress-jasilynn. Triggering RRT.
2026-09-11 20:35:00,929 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn abandoned Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(197, 292))
2026-09-11 20:35:00,929 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> idle
2026-09-11 20:35:00,932 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn remembered Goal(category=subject, name = player, layer = 0, position=(
# ... infinite loop elided ...
2026-09-11 20:35:03,168 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): find -> idle
^C2026-09-11 20:35:03,175 - INFO - __main__ - Game engine loop interrupted by user.
2026-09-11 20:35:03,176 - INFO - __main__ - Generating state dump...
2026-09-11 20:35:03,330 - INFO - __main__ - State dump successfully written to /home/grant/Projects/ontology/20260911_203503.state-dump.md
2026-09-11 20:35:03,576 - INFO - __main__ - CLI processes completed.
```

**State Dump (Kaboom Case)**

```markdown
# Ontology State Dump

- **Board:** world-01
- **Timestamp:** 20260911_203503

---

## strut-house-1

- **Taxonomy:**
  - Category: `AssetCategories.CRAFTS`
  - Instance: `AssetInstances.STRUTS`
  - ID: `frame-brick`
- **Dimensions:**
  - Width: 96
  - Length: 190
- **Layer:** `0`
- **Depth:** 0
- **Position:** (150, 150)
- **Owner:** `player`

## door-strut-house-1-1

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-house`
- **Dimensions:**
  - Width: 32
  - Length: 48
- **Layer:** `0`
- **Depth:** 1
- **Height:** 340
- **Position:** (182, 268)
- **Door Out:**
  - Layer: `brick-house-compose-layer`
  - Position: (232, 293)

## strut-house-interior-1

- **Taxonomy:**
  - Category: `AssetCategories.CRAFTS`
  - Instance: `AssetInstances.STRUTS`
  - ID: `wall-blue`
- **Dimensions:**
  - Width: 128
  - Length: 96
- **Layer:** `brick-house-compose-layer`
- **Depth:** 0
- **Position:** (150, 150)
- **Owner:** `player`

## door-strut-house-interior-1-1

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-shadow`
- **Dimensions:**
  - Width: 32
  - Length: 48
- **Layer:** `brick-house-compose-layer`
- **Depth:** 0
- **Position:** (197, 292)
- **Door Out:**
  - Layer: `0`
  - Position: (193, 313)

## strut-strut-house-interior-1-1

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `floor-wood`
- **Dimensions:**
  - Width: 128
  - Length: 96
- **Layer:** `brick-house-compose-layer`
- **Depth:** 0
- **Height:** -100
- **Position:** (150, 246)
- **Owner:** `player`

## strut-castle-wall-2

- **Taxonomy:**
  - Category: `AssetCategories.CRAFTS`
  - Instance: `AssetInstances.STRUTS`
  - ID: `wall-castle`
- **Dimensions:**
  - Width: 222
  - Length: 133
- **Layer:** `0`
- **Depth:** 0
- **Position:** (250, 250)
- **Owner:** `the-government`

## door-strut-castle-wall-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-castle-open`
- **Dimensions:**
  - Width: 64
  - Length: 64
- **Layer:** `0`
- **Depth:** 0
- **Height:** 383
- **Position:** (331, 299)
- **Door Out:**
  - Layer: `castle-compose-layer`

## door-strut-castle-wall-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-castle-open`
- **Dimensions:**
  - Width: 64
  - Length: 64
- **Layer:** `0`
- **Depth:** 0
- **Height:** 383
- **Position:** (331, 299)
- **Door Out:**
  - Layer: `castle-compose-layer`

## gate-strut-castle-wall-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `gates`
  - ID: `gate-castle`
- **Dimensions:**
  - Width: 64
  - Length: 64
- **Layer:** `0`
- **Depth:** 1
- **Height:** 383
- **Position:** (331, 299)
- **Animation:**
  - Action: `walk`
  - Direction: `down`
  - Frame: 0
  - Tick: 1
- **Switch:** False
- **Link:** `castle-gate-link`

## gate-strut-castle-wall-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `gates`
  - ID: `gate-castle`
- **Dimensions:**
  - Width: 64
  - Length: 64
- **Layer:** `0`
- **Depth:** 1
- **Height:** 383
- **Position:** (331, 299)
- **Animation:**
  - Action: `walk`
  - Direction: `down`
  - Frame: 0
  - Tick: 1
- **Switch:** False
- **Link:** `castle-gate-link`

## plate-strut-castle-wall-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `plates`
  - ID: `plate-stone`
- **Dimensions:**
  - Width: 15
  - Length: 14
- **Layer:** `0`
- **Depth:** 1
- **Height:** 383
- **Position:** (274, 395)
- **Animation:**
  - Action: `walk`
  - Direction: `down`
  - Frame: 0
  - Tick: 1
- **Switch:** False
- **Link:** `castle-gate-link`

## plate-strut-castle-wall-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `plates`
  - ID: `plate-stone`
- **Dimensions:**
  - Width: 15
  - Length: 14
- **Layer:** `0`
- **Depth:** 1
- **Height:** 383
- **Position:** (274, 395)
- **Animation:**
  - Action: `walk`
  - Direction: `down`
  - Frame: 0
  - Tick: 1
- **Switch:** False
- **Link:** `castle-gate-link`

## the-steppe

- **Taxonomy:**
  - Category: `tiles`
  - Instance: `back`
  - ID: `grass`
- **Dimensions:**
  - Width: 32
  - Length: 32
- **Layer:** `0`
- **Depth:** 0
- **Position:** (0, 0)
- **Multiple:**
  - nx: 100
  - ny: 100

## castle-dawn-barrel-00

- **Taxonomy:**
  - Category: `objects`
  - Instance: `crates`
  - ID: `crate-barrel`
- **Dimensions:**
  - Width: 28
  - Length: 38
- **Layer:** `0`
- **Depth:** 0
- **Position:** (100, 250)
- **Velocity:** (, )

## castle-dawn-sign-board-00

- **Taxonomy:**
  - Category: `objects`
  - Instance: `signs`
  - ID: `wood-bulletin`
- **Dimensions:**
  - Width: 30
  - Length: 32
- **Layer:** `0`
- **Depth:** 0
- **Position:** (430, 370)
- **Persona:** `castle-dawn-sign`
- **Lexicon:** `spring`

## evil-empress-jasilynn

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `sprites`
  - ID: `jasilynn`
- **Dimensions:**
  - Width: 64
  - Length: 64
- **Layer:** `brick-house-compose-layer`
- **Depth:** 0
- **Position:** (175, 200)
- **Velocity:** (, )
- **Animation:**
  - Action: `walk`
  - Direction: `down`
  - Frame: 5
  - Tick: 1
- **Character:**
  - Strength: 5
  - Defense: 5
  - Speed: 50
  - Impulse: 25
- **Meters:**
  - Health: 50 / 100
  - Magic: 100 / 100
- **Inventory:**
  - Wallet: 0
  - Equipment:
    - Armor: `None`
    - Weapon: `shortsword`
    - Tool: `None`
    - Utility: `None`
    - Shield: `None`
- **Mutators:**
  - Triggers:
    - Animated: True
    - Frightened: False
    - Dead: False
    - Vision: True
  - Parameters:
    - Fear:
      - Radius: 128
      - Limit: 0.5
      - Enemy: 5
    - Vision:
      - Radius: 128
    - Action:
      - Radius: 25
- **Memory:**
  - Goals:
    - `player`:
      - Name: `player`
      - Category: `subject`
      - Layer: `0`
      - Position: (100, 200)
  - Sprites:
    - `player`: (100, 200)
  - Relationships:
    - `player`: `Relationships.FRIEND`
- **Psyche:**
  - Persona: `empress-jasilynn`
  - Motivation: `conquest`
  - Dialogue: `greeting`
- **Intention:** `Intentions.FIND`

## player

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `players`
  - ID: `player`
- **Dimensions:**
  - Width: 64
  - Length: 64
- **Layer:** `0`
- **Depth:** 0
- **Position:** (10, 135)
- **Velocity:** (, )
- **Animation:**
  - Action: `walk`
  - Direction: `down`
  - Frame: 0
  - Tick: 0
- **Character:**
  - Strength: 5
  - Defense: 5
  - Speed: 100
  - Impulse: 25
- **Meters:**
  - Health: 50 / 100
  - Magic: 100 / 100
- **Inventory:**
  - Wallet: 0
  - Equipment:
    - Armor: `None`
    - Weapon: `shortsword`
    - Tool: `None`
    - Utility: `None`
    - Shield: `buckler`
- **Goal:**
  - Name: `None`
  - Category: `None`
  - Layer: `None`
  - Position: (10, 135)
- **Mutators:**
  - Triggers:
    - Animated: False
    - Frightened: False
    - Dead: False
    - Vision: False
  - Parameters:
    - Fear:
      - Radius: 30
      - Limit: 0.5
      - Enemy: 5
    - Vision:
      - Radius: 30
    - Action:
      - Radius: 30
- **Intention:** `Intentions.IDLE`

---

# Perimeters

## Layer: 0

- Position: (0, 0) | Dimensions: w: 1, l: 3200
- Position: (3200, 0) | Dimensions: w: 1, l: 3200
- Position: (0, 0) | Dimensions: w: 3200, l: 1
- Position: (0, 3200) | Dimensions: w: 3200, l: 1

## Layer: brick-house-compose-layer

- Position: (150, 150) | Dimensions: w: 1, l: 192
- Position: (250, 342) | Dimensions: w: 1, l: 41
- Position: (278, 150) | Dimensions: w: 1, l: 100
- Position: (472, 250) | Dimensions: w: 1, l: 133
- Position: (150, 150) | Dimensions: w: 128, l: 1
- Position: (278, 250) | Dimensions: w: 194, l: 1
- Position: (150, 342) | Dimensions: w: 100, l: 1
- Position: (250, 383) | Dimensions: w: 222, l: 1
```

**Root-Cause Analysis: The "Final Boss" Loop**

The failure observed when transitioning from `board.instances(AssetInstances.CRATES.value, layer)` to `board.weights(layer)` is caused by an architectural mismatch between **visual bounding geometry** and **physical collision geometry**, compounded by evaluating raycasting from the sprite's **texture canvas origin** rather than its **physical sensory anchor**.

When `board.weights(layer)` is activated, `strut-house-interior-1` (`wall-blue`) at `(150, 150)` is included in the obstacle query because its mass is `0`. Three cascading defects cause the engine to freeze in an infinite two-tick loop:

1. Visual Geometry vs. Hitbox Footprint in Obstacle Extraction

In `CognitionMechanics.obstacles()`, the obstacle list is populated as:

```python
obstacles.append((
    asset.state.position.x,
    asset.state.position.y,
    asset.dimensions.w,
    asset.dimensions.l,
))

```

`asset.dimensions` represents the full graphical texture bounds. For `wall-blue`, dimensions are $w=128, l=96$, establishing an obstacle box spanning:

$$X \in [150, 278], \quad Y \in [150, 246]$$

However, the actual physical collision barrier defined in `crafts.yaml` is its hitbox:

```yaml
hitboxes:
  - position: { x: 6, y: 17 }
    dimensions: { w: 116, l: 54 }

```

The true impassable collision barrier spans only:

$$X \in [156, 272], \quad Y \in [167, 221]$$

The bottom 25 pixels ($Y \in [221, 246]$) represent the visual baseboard and walkable floor trim in front of the wall where sprites can stand. By using `asset.dimensions`, `CognitionMechanics.obstacles()` inflates the obstacle by 25 pixels downward into the room's walkable space.

2. Texture Origin vs. Physical Footprint Anchor

`evil-empress-jasilynn` is spawned at `(175, 200)`. In LPC sprite sheets (64x64), `(x, y)` is the top-left coordinate of the rendering canvas. The sprite's physical collision hitbox is offset at `(21, 23)` with dimensions `(22, 21)`:

$$X_{\text{hitbox}} \in [196, 218], \quad Y_{\text{hitbox}} \in [223, 244]$$

Because $223 > 221$, Jasilynn's physical collision body does **not** overlap the wall's hitbox. `CollisionMechanics` detects no overlap, so physics permits her to exist and move freely.

However, `CognitionMechanics._plan()` and `_track()` query line of sight using the top-left canvas origin `sprite.state.position`:

$$\text{Start} = (175, 200)$$

Because $150 \le 175 \le 278$ and $150 \le 200 \le 246$, $(175, 200)$ is inside the inflated bounding box of `wall-blue`. In `geometry.bisects()`, when a ray origin is inside an obstacle box, the entry fraction is $u_1 = 0.0$ and exit fraction $u_2 > 0.0$. Thus, $u_1 < u_2$ evaluates to `True`, flagging line of sight as blocked.

3. RRT Root Node Invalidity & Tree Stalling

Because LOS is blocked, `_plan()` constructs `Planner(start=sprite.state.position, target=sprite.state.goal.position)`.

* The root node `self.start` is set to $(175, 200)$.
* For every sampled point $\text{rnd}$, `_steer()` creates a vector from `self.start`.
* `_check_collision(self.start, new_node)` calls `geometry.los()`.
* Because `self.start` is inside the obstacle, **every outgoing branch from the root node registers a collision**.
* No node is ever added to `node_list`. The tree stalls for 300 iterations and returns `[]`.

4. The Two-Tick Intention Oscillation

When `Planner.plan()` returns `[]`:

1. `_plan()` logs `abandoned` and sets `sprite.state.goal = None`.
2. In `TransitionMechanics`, the sprite is in `find`. The condition `not sprite.goal` triggers `find -> idle`.
3. In `idle`, `CognitionMechanics._remember()` runs on the next tick. It pops `player` from `memory.goals`.
4. In `_track()`, the cross-layer logic detects the player is on layer `0`, subsumes `player` back into `memory.goals`, and re-assigns the door (`door-strut-house-interior-1-1`) as an `OBJECT` goal.
5. In `TransitionMechanics`, the ISL condition for `idle -> find` evaluates to `True`.
6. In `find`, `_track()` calls `_plan()` on the door again. LOS is blocked, RRT fails, `sprite.state.goal = None`, and the sprite drops back to `idle`.
7. This cycle repeats every two frames, permanently locking the NPC.

#### Refactor: Phase 08.01 - Obstacle Geometry

**Overview**

Refactor the spatial queries and sensory representations connecting `CognitionMechanics` to the Cython geometry and RRT pathfinding subsystems. Ensure path generation accurately reflects physical hitboxes rather than texture canvas bounds, and stabilize the automaton when targets are temporarily or permanently unreachable.

##### Goal: Physical Obstacle Projection

Extract obstacle bounding boxes strictly from asset collision hitboxes rather than top-level rendering dimensions.

```python
def obstacles(layer: str, board: Board, exclude: list) -> list:
    rects = []
    for asset in board.weights(layer):
        if asset.name in exclude:
            continue
        for hb in asset.hitboxes:
            rects.append((
                asset.state.position.x + hb.position.x,
                asset.state.position.y + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l,
            ))
    for bound in board.perimeters.get(layer, []):
        rects.append((
            bound.position.x,
            bound.position.y,
            bound.dimensions.w,
            bound.dimensions.l,
        ))
    return rects

```

##### Goal: Footprint Sensory Anchoring

Anchor line-of-sight raycasts and RRT start/end coordinates to the entity's physical footprint center rather than the top-left canvas coordinate.

```python
def anchor(asset: Asset) -> Position:
    hbs = asset.hitboxes
    if not hbs:
        return Position(
            x=asset.state.position.x + asset.dimensions.w // 2,
            y=asset.state.position.y + asset.dimensions.l // 2,
        )
    hb = hbs[0]
    return Position(
        x=asset.state.position.x + hb.position.x + hb.dimensions.w // 2,
        y=asset.state.position.y + hb.position.y + hb.dimensions.l // 2,
    )

```

##### Goal: Pathfinding Failure Recovery

Prevent the two-tick thrashing loop between `find` and `idle` when RRT cannot find a path.

```python
# If RRT fails to connect:
CognitionMechanics.log_goal(sprite, verb="unreachable")
sprite.state.memory.unreachable[goal.name] = (
    current_tick + settings.PATH_RETRY_INTERVAL
)
sprite.state.goal = None

```

##### Tasks

**1. Task: Hitbox-Accurate Obstacle Extraction**

*Objective*: Ensure pathfinding obstacle lists accurately represent physical collision boundaries.

* [x] Subtask: Refactor `CognitionMechanics.obstacles()` to iterate over `asset.hitboxes` for all entities returned by `board.weights(layer)`.
* [x] Subtask: Verify `obstacles()` computes absolute world coordinates by summing `asset.state.position` and `hitbox.position`.
* [x] Subtask: Add unit tests in `tests/unit/test_app_game_logic_mechanics_intentional_cognition.py` verifying multi-hitbox and offset-hitbox assets produce multiple discrete obstacle tuples.

**2. Task: Sensory Anchor Utilities**

*Objective*: Eliminate perspective bias in spatial raycasts.

* [x] Subtask: Add an `anchor()` helper in `app/game/logic/mechanics/modules/paths/` (or `CognitionMechanics`) to compute the physical footprint center of any Asset.
* [x] Subtask: Update `CognitionMechanics._plan()` to pass footprint anchors as `start` and `target` to `geometry.los()` and `Planner`.
* [x] Subtask: In `CognitionMechanics.path()`, offset generated RRT waypoints by the sprite's anchor displacement so `sprite.state.position` is steered such that the hitbox follows the path.

**3. Task: Categorical Dispatch Optimization in `_track**`

*Objective*: Prevent spurious per-tick re-planning on existing paths and static objects.

* [x] Subtask: In `CognitionMechanics._track()`, ensure active waypoints (`name.startswith(settings.RRT_PATH_PREFIX)`) only run invalidation checks (`_scrap()`) and bypass `_plan()`.
* [x] Subtask: Gate `_plan()` for `OBJECT` and `POSITION` goals behind an initial acquisition check or active obstruction detection.

**4. Task: Unreachable Target Backoff**

*Objective*: Stabilize the automaton when a target is obstructed.

* [!] Subtask: Add an unreachable/dormant tracking mechanism in `SpriteState.memory` to prevent `_remember()` from immediately popping goals that failed RRT.
* [!] Subtask: Ensure that upon path failure, control falls through to `idle -> wander` until sensory conditions change or the retry timeout expires.