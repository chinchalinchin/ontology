# Ontology Docs: Architecture

This section contains an in-depth presentation of the [Application's](./00-overview.md#application) architecture.

## Specifications

### Specification: Initialization

The engine utilizes a decoupled boot-and-hydrate lifecycle to achieve instantaneous menu rendering and non-blocking transitions. The general flow is shwon in the following diagram and detailed further in the following sections,

```mermaid
flowchart LR
    A[Orchestrator] --> B[Registry]
    B --> C[Engine]
    C --> D[MainMenu]
    D --> E[StateEvent]
    E --> F[Migrator]
    F --> G[LoadController]
    G --> H[Engine]
```

!!! important "Hardware Rendering Context Pre-requisites"
    When running in live (non-headless) mode, the hardware window context **must** be instantiated strictly *after* the rendering subsystem is intialized but *before* Registry initialization. The Registry caches textures directly into GPU memory via Cython. If the window context does not exist when the Registry attempts to index and load `.png` files, the textures will silently resolve as empty `0x0` null pointers. This results in a "ghost game" where the entire Screen is invisible, but the Board database and Mechanic systems continue to operate normally.

#### Phase 1: Boot

1. **Bootstrapping**: Loads Configuration files via Pydantic TypeAdaptor, instantiates Service singletons, compiles [Executors](./05-mechanics.md#dependency-executors) and [Relations](./05-mechanics.md#dependency-relations)
2. **Cython**: Initializes SDL2 video, image, and typography subsystems.
3. **Registry**: Recursively parses the Asset directory, mapping file paths and generating crop-map indexes. *VRAM allocation is completely deferred.*
4. **Components**: Instantiates [Mechanics](./05-mechanics.md) and an empty [Board database](./00-overview.md#component-board). 
5. **Ignition**: The fixed-timestep loop begins. A [MenuEvent('main')](./06-widgets.md#events) is injected into the Engine bus prior to ignition to immediately render the [Main Menu](./06-widgets.md#menus).

#### Phase 2: Hydration

Triggered by a StateEvent (e.g., selecting "*New Game*" or "*Load*"), the Engine transitions into world generation without blocking the Python GIL.

1. **Generation**: The [LoadController](./06-widgets.md#controllers) calls the Migrator each frame. The Migrator applies calls the [Factory](./00-overview.md#service-factory) to generate batches of Assets from the State file, injecting Frame, Animation, Hitbox, Properties, and State components, then yields execution back to the Engine.
   *The StateSchema distinguishes between Physical Asset State (Assets requiring State, Frames, etc.) and World State. During hydration, the Migrator parses World State and assigns it to the Board.
2. **Prewarming**: Concurrently, the Registry parses a queue of keys, loading Asset files into memory within a time budget.
3. **Allocation**: Once hydration is complete, the Migrator triggers  all Screens to recalculate max dimensions and reallocate canvases for the Painter's Algorithm.
4. **Execution**: The LoadController emits a [TerminalEvent](./06-widgets.md#events), popping the loading screen, activating the Board, and unpausing the [World Mechanics](./05-mechanics.md#mechanics-world).

### Specification: Engine Loop

The Engine delegates behavior to [Mechanics](./05-mechanics.md). Rather than the [Engine](./00-overview.md#component-engine) passing arguments to a system, a Mechanic is responsible for querying the [Board](./00-overview.md#component=board) for the exact data it requires, processing the state, and optionally pushing Events to the Engine's Bus.

Mechanics are strictly segregated into `core` pipelines and `world` pipelines. The [Engine](./00-overview.md#component-engine) method processes these pipelines conditionally:

```python
def _play(self, delta) -> None:
    """
    Apply Mechanics.
    """
    for mechanic in self.core:
        mechanic.update(self.board, delta, self.bus)

    if not self.board.paused:
        for mechanic in self.world:
            mechanic.update(self.board, delta, self.bus)
```

* **Core Mechanics:** Systems that must execute every frame regardless of game state. This includes [MenuMechanics](./05-mechanics.md#core) (to process input and layout traversals), [AnimationMechanics](./05-mechanics.md#core) (to keep Assets animating), and RemoveMechanics (garbage collection).
* **World Mechanics:** Systems that govern gameplay logic, physics, and NPC behavior. This includes [MotionMechanics, CombatMechanics, and PlayerMechanics](./05-mechanics.md).

When an [Event](./06-widgets.md#events) fires and a Menu is pushed to the screen, the Board is paused. The Engine skips the World Mechanics loop entirely. The World freezes, but Core Mechanics continue ticking, allowing the User to navigate the Menu.

### Specification: Board Caches

#### Cache: Spatial Grid

The Board utilizes two discrete ($O(1)$) spatial hash grids $(c_x, c_y)$:

1. **Tile Grid**: Partitions Tiles into buckets nested by Layer and Instance

$$
\text{tilemap}[\text{layer}][\text{instance}][(c_x, c_y)] \to \text{Asset}
$$

2. **Fluid Grid**: Paritions Fluid streams and their Pools into buckets. Each bucket stores references to overlapping Fluids:

$$
\text{fluidmap}[\text{layer}][(c_x, c_y)] \to \text{List}[\text{Asset}]
$$

### Specification: Graphics

#### Rendering: Sort

World rendering evaluates spatial geometry using discrete elevations, intra-elevation substrate planes, ground perspective, and coplanar priority:

$$
\text{sortkey}(A) = \Big(A.\text{elevation}, A.\text{substrate}, \text{ground}(A), A.\text{properties.priority}\Big)
$$

1. **Primary Key (`A.elevation` $\in \mathbb{Z}_{\ge 0}$)**: Discrete elevation (`0`, `1`, `2`, ...).
2. **Secondary Key (`A.substrate` $\in \mathbb{Z}_{\le 0}$)**: Intra-elevation rendering plane within $E$:
    * `-4`: [Environ Tiles](./01-assets.md#tile-environ)
    * `-3`: [Fluids](./01-assets.md#effect-fluids)
    * `-2`: [Struts](./03-compositions.md#craft-struts), [Geography](./09-ecology.md#category-geography).
    * `-1`: [Bridges](./01-assets.md#craft-bridges), [Stairs](01-assets.md#craft-stairs).
    * `0`: Standard Substrate.
3. **Tertiary Key ($\text{ground} \in \mathbb{Z}$)**: Geometric perspective offset by Anchor: $\text{ground} = \text{int}(A.\text{state.position.y} + A.\text{dimensions.l} + A.\text{state.anchor})$.
4. **Quaternary Key ($\text{priority} \in \mathbb{Z}$)**: Coplanar tie-breaker for Assets sharing an identical `(elevation, substrate, ground)` baseline.

#### Rendering: Typography

A Font configuration pairs a `.ttf` file with styling rules. During bootstrap, the Registry ingests each Font declared in `/src/assets/fonts/**/*.yaml`, storing them as styled Cython wrappers. 

In [Menu Configurations](./06-widgets.md#configuration-menus), Font are scoped at the [Pane](./06-widgets.md#widget-panes) level: any Fany declared on a parent Pane cascades down to all child Widgets unless explicitly overridden by a nested pane.

See [Library: Graphics](#library-graphics) for more implementation details.

**Properties: FontProperties**

* `size: int`: Point size used during glyph rasterization (defaults to `24`).
* `alignment: str`: Text alignment within the bounding box (`left`, `center`, `right`).
* `bold: bool`: Toggles `TTF_STYLE_BOLD`.
* `italics: bool`: Toggles `TTF_STYLE_ITALIC`.
* `underline: bool`: Toggles `TTF_STYLE_UNDERLINE`.
* `strikethrough: bool`: Toggles `TTF_STYLE_STRIKETHROUGH`.
* `margins: float`: Fractional padding applied to the target canvas bounds before wrapping (e.g., `0.05` for 5%).
* `color`: Primary glyph fill color.
    * `r: int` (0–255)
    * `g: int` (0–255)
    * `b: int` (0–255)
    * `a: int` (0–255)
* `outline`: (*Optional*) Border styling configuration.
    * `width: int`: Perimeter thickness in pixels (`outline > 0` enables two-pass rendering).
    * `color`:
        * `r: int` (0–255)
        * `g: int` (0–255)
        * `b: int` (0–255)
        * `a: int` (0–255)

**Required: Fonts**

* `dialogue`: Font used to render text.
* `menu`: Font used for Buttons.
* `title`: Font used for headings.

### Specification: Cython Libraries

While Python objects are fast enough for general logic, calculating collisions and processing rendering instructions for thousands of entities requires maximum performance. The engine uses Cython to bridge this gap, adhering to a **"Zero Heap Allocation in the Inner Loop"** philosophy to prevent frame stutters caused by the Python Garbage Collector.

!!! important "Zero Heap Allocation Flexibility"
    Zero Heap Allocation is more of an ideal/driving principle than an enforced constraint. 

#### Library: Models

* Address `libs.core.models`

**Model: Position**

- `x: int`
- `y: int`

**Model: Dimensions**

* `w: int`
* `l: int`

**Model: Multiple**

* `nx: int`
* `ny: int`

**Model: Velocity**

* `vx: int`
* `vy: int`

**Model: Hitbox**

* `position: Position`
* `dimension Dimensions`

**ScreenPosition**:

* `px: double`
* `py: double`

#### Library: Math

* Address: `libs.core.math`

The mathematical foundation of the Engine operates over the two-dimensional Euclidean plane $\mathbb{R}^2$ and its discrete integer lattice $\mathbb{Z}^2$:

1. **Coordinate Space**: Each Layer defines an independent Cartesian plane with origin $(0, 0)$ at the upper-left corner, $+x$ directed right, and $+y$ directed down.
2. **Bounding Primitives**: A rectangular region (Axis-Aligned Bounding Box, or AABB) is parameterized by its upper-left origin $(x, y)$ and non-negative dimensions $(w, l)$, spanning the half-open interval:

$$
R(x, y, w, l) = [x, x + w) \times [y, y + l)
$$

3. **Composite Footprints**: An entity at world position $(x_a, y_a)$ with relative hitboxes $\{(x_i, y_i, w_i, l_i)\}$ occupies the union of translated bounding boxes:

$$
\mathcal{H}(A) = \bigcup_{i} \big[x_a + x_i,\; x_a + x_i + w_i\big) \times \big[y_a + y_i,\; y_a + y_i + l_i\big)
$$

##### Math: Geometry

* Address: `libs.core.math.geometry`

1. **intersects** Calculates Axis-Aligned Bounding Box intersections.

Two axis-aligned bounding boxes $R_1 = (x_1, y_1, w_1, l_1)$ and $R_2 = (x_2, y_2, w_2, l_2)$ intersect if and only if their projections overlap on both principal axes:

$$
(x_1 < x_2 + w_2)
$$
$$
(x_1 + w_1 > x_2)
$$
$$
(y_1 < y_2 + l_2)
$$
$$
(y_1 + l_1 > y_2)
$$

A point $(p_x, p_y)$ lies inside $R(x, y, w, l)$ when $x \le p_x < x + w$ and $y \le p_y < y + l$.

2. **onscreen** Evaluates if an Asset intersects with the Screen Camera.

For a Camera of dimensions $(w_s, l_s)$ centered on a focus at $(x_f, y_f)$ with dimensions $(w_f, l_f)$, the camera origin is:

$$
x_c = x_f + \left\lfloor \frac{w_f}{2} \right\rfloor - \left\lfloor \frac{w_s}{2} \right\rfloor
$$
$$y_c = y_f + \left\lfloor \frac{l_f}{2} \right\rfloor - \left\lfloor \frac{l_s}{2} \right\rfloor
$$

An Asset is visible on screen if its bounding box intersects $R(x_c, y_c, w_s, l_s)$.

3. **cone** Field-of-view check validating whether a target coordinate falls within a parameterized directional vision cone.

Given a source point $\mathbf{s} = (s_x, s_y)$ and a target point $\mathbf{t} = (t_x, t_y)$ with displacement $\mathbf{d} = \mathbf{t} - \mathbf{s} = (\Delta x, \Delta y)$:

Given a cardinal unit heading vector $\hat{\mathbf{u}} \in \{(0, -1), (0, 1), (-1, 0), (1, 0)\}$ and angular cosine threshold $\cos\alpha$, $\mathbf{t}$ lies within the field of view of radius $r$ when $\|\mathbf{d}\|^2 \le r^2$ and:

$$
(\mathbf{d} = \mathbf{0})
\lor
(\frac{\mathbf{d} \cdot \hat{\mathbf{u}}}{\|\mathbf{d}\|} \ge \cos\alpha)
$$

4. **nearby**: Euclidean distance check.

$\mathbf{t}$ lies within radius $r$ of $\mathbf{s}$ if and only if:

$$
\|\mathbf{d}\|^2 = \Delta x^2 + \Delta y^2 < r^2
$$

5. **punctures** Implementation of the Liang-Barsky line clipping algorithm. Evaluates whether a line segment $(x_1, y_1) \to (x_2, y_2)$ penetrates the interior of an AABB obstacle with non-degenerate penetration depth ($u_1 < u_2 - \epsilon$).

A directed line segment from $\mathbf{p}_1 = (x_1, y_1)$ to $\mathbf{p}_2 = (x_2, y_2)$ is parameterized over $u \in [0, 1]$ by:

$$
\mathbf{p}(u) = \mathbf{p}_1 + u(\mathbf{p}_2 - \mathbf{p}_1) = (x_1 + u\Delta x,\; y_1 + u\Delta y)
$$

Intersection with an obstacle rectangle $R = [r_x, r_x + r_w] \times [r_y, r_y + r_l]$ satisfies the system of four linear inequalities $ p_k \le q_k$ for $k \in \{0, 1, 2, 3\}$:

$$
p_0 = -\Delta x, \quad q_0 = x_1 - r_x
$$
$$
p_1 = +\Delta x, \quad q_1 = (r_x + r_w) - x_1
$$
$$
p_2 = -\Delta y,  \quad q_2 = y_1 - r_y
$$
$$
p_3 = +\Delta y, \quad q_3 = (r_y + r_l) - y_1
$$

Let $u_1$ and $u_2$ denote the clipped entry and exit parameters:

$$
u_1 = \max\Big(\{0\} \cup \{\frac{q_k}{p_k} \mid p_k < 0 \}\Big)
$$
$$
u_2 = \min\Big(\{1\} \cup \{\frac{q_k}{p_k} \mid p_k > 0 \}\Big)
$$

The segment punctures the interior of $R$ if no parallel boundary is violated ($p_k = 0 \implies q_k > \epsilon$) and $u_1 < u_2 - \epsilon$ for tolerance $\epsilon > 0$. Line of sight holds between $\mathbf{p}_1$ and $\mathbf{p}_2$ over an obstacle set $\mathcal{O}$ if the segment punctures no rectangle in $\mathcal{O}$.

6. **los** Raycasts a line-of-sight segment across a collection of primitive AABB tuples.

For a corridor of cross-section $(s_w, s_l)$ originating at $(s_x, s_y)$ and propagating along a cardinal direction up to distance $D_{\max}$, the distance to the nearest obstructing rectangle $(o_x, o_y, o_w, o_l) \in \mathcal{O}$ is evaluated over obstacles whose transverse projection overlaps the corridor:

* *Vertical Propagation* ($o_x < s_x + s_w$ and $o_x + o_w > s_x$):

$$
d_{\text{down}} = \min\Big(\{D_{\max}\} \cup \{ o_y - s_y \mid o_y > s_y \}\Big)
$$
$$
d_{\text{up}} = \min\Big(\{D_{\max}\} \cup \{s_y - (o_y + o_l) \mid o_y + o_l < s_y\}\Big)
$$

* *Horizontal Propagation* ($o_y < s_y + s_l \land o_y + o_l > s_y$):

$$
d_{\text{right}} = \min\Big(\{D_{\max}\} \cup \{o_x - s_x \mid o_x > s_x\}\Big)
$$
$$
d_{\text{left}} = \min\Big(\{D_{\max}\} \cup \{s_x - (o_x + o_w) \mid o_x + o_w < s_x\}\Big)
$$

7. **contours**

Executes a two-pass Sweep-Line algorithm over primitive AABBs to generate map boundaries. Uses interval merging and XOR symmetric differences to isolate exposed contour edges, returning boundary segments.

Given a family of axis-aligned rectangles $\{R_i = [x_{i,\min}, x_{i,\max}] \times [y_{i,\min}, y_{i,\max}]\}$, the exposed boundary contours of their union $\mathcal{U} = \bigcup_i R_i$ are derived via a two-pass orthogonal sweep:

* *Vertical Sweep*: Sort all vertical edges by $x$-coordinate, pairing $x_{i,\min}$ with event $+1$ and $x_{i,\max}$ with event $-1$. At each event coordinate $x$, let $I_{\text{prev}}$ and $I_{\text{curr}}$ denote the merged 1D $y$-intervals of active rectangles before and after $x$. The asymmetric set differences isolate the exposed vertical contour segments at $x$:

$$
E_{\text{left}}(x) = I_{\text{curr}} \setminus I_{\text{prev}}
$$
$$
E_{\text{right}}(x) = I_{\text{prev}} \setminus I_{\text{curr}}
$$

* *Horizontal Sweep*: Sort all horizontal edges by $y$-coordinate, pairing $y_{i,\min}$ with $+1$ and $y_{i,\max}$ with $-1$. Comparing the merged 1D $x$-intervals $J_{\text{prev}}$ and $J_{\text{curr}}$ isolates the exposed horizontal contour segments at $y$:

8. **bounded**

Narrow-phase validation checking whether an Asset's offset hitboxes intersect a raw mathematical boundary constraint.

##### Math: Paths

* Address: `libs.core.math.paths`


Given a start coordinate $\mathbf{s} = (s_x, s_y)$, a target coordinate $\mathbf{t} = (t_x, t_y)$, a step size $\delta > 0$, an iteration limit $N_{\max}$, and a set of obstacle rectangles $\mathcal{O}$ (inflated in configuration space by the navigating Sprite's Hitbox half-dimensions and clearance radius), pathfinding constructs a collision-free trajectory from $\mathbf{s}$ to $\mathbf{t}$ via a Rapidly-exploring Random Tree (RRT):

1. **Search Window Partitioning**: Define a padded search domain enclosing $\mathbf{s}$ and $\mathbf{t}$ with margin $\mathbf{m} = (0.2|t_x - s_x| + 2\delta, 0.2|t_y - s_y| + 2\delta)$:

$$
[x_{\min}, x_{\max}] = [\min(s_x, t_x) - m_x, \max(s_x, t_x) + m_x]
$$
$$
[y_{\min}, y_{\max}] = [\min(s_y, t_y) - m_y,\; \max(s_y, t_y) + m_y]
$$

If $x_{\min} < 0$ or $y_{\min} < 0$, the negative offset is added to the corresponding upper bound and the lower bound is clamped to $0$. The active obstacle set is restricted to $\mathcal{O}_{\text{local}} = \{R \in \mathcal{O} \mid R \cap ([x_{\min}, x_{\max}] \times [y_{\min}, y_{\max}]) \neq \emptyset\}$.

2. **Goal-Biased Tree Expansion**: Initialize a tree $\mathcal{T} = (V, E)$ rooted at $\mathbf{v}_0 = \mathbf{s}$. For up to $N_{\max}$ iterations:

* **Sampling**: Draw $u, u_x, u_y \sim \mathcal{U}(0, 1)$ with goal bias $p_{\text{goal}} = 0.05$:

$$
\mathbf{q} = \begin{cases} \mathbf{t} & \text{if } u \le p_{\text{goal}} \\ \big(x_{\min} + u_x(x_{\max} - x_{\min}),\; y_{\min} + u_y(y_{\max} - y_{\min})\big) & \text{otherwise} \end{cases}
$$

* **Nearest Neighbor**: Select the tree vertex $\mathbf{v}_{\text{near}} \in V$ minimizing Euclidean distance to $\mathbf{q}$:

$$
\mathbf{v}_{\text{near}} = \arg\min_{\mathbf{v} \in V} \|\mathbf{v} - \mathbf{q}\|_2
$$

* **Clamped Steering**: Step from $\mathbf{v}_{\text{near}}$ toward $\mathbf{q}$ by distance $d = \min(\delta, \|\mathbf{q} - \mathbf{v}_{\text{near}}\|_2)$ along angle $\theta = \operatorname{atan2}(q_y - v_{\text{near},y},\; q_x - v_{\text{near},x})$:

$$
\mathbf{v}_{\text{new}} = \mathbf{v}_{\text{near}} + d\begin{pmatrix} \cos\theta \\ \sin\theta \end{pmatrix}
$$

* **Edge Validation & Termination**: If the segment $\overline{\mathbf{v}_{\text{near}}\mathbf{v}_{\text{new}}}$ is unobstructed across $\mathcal{O}_{\text{local}}$, add $\mathbf{v}_{\text{new}}$ to $V$ with parent $\mathbf{v}_{\text{near}}$. If $\mathbf{v}_{\text{new}} = \mathbf{t}$, or if $\|\mathbf{t} - \mathbf{v}_{\text{new}}\|_2 \le \delta$ and $\overline{\mathbf{v}_{\text{new}}\mathbf{t}}$ is unobstructed, append $\mathbf{t}$ to $\mathcal{T}$ and terminate exploration.

3. **Backtracing & String-Pulling Pruning**: Traverse parent links from $\mathbf{t}$ to $\mathbf{v}_0$ and reverse the sequence to form the unpruned chain $\mathbf{p}_0, \mathbf{p}_1, \dots, \mathbf{p}_k$ ($\mathbf{p}_0 = \mathbf{s}$, $\mathbf{p}_k = \mathbf{t}$). Redundant intermediate vertices are collapsed via greedy line-of-sight string-pulling:

* From current anchor index $i$ (initialized to $0$), select the largest index $j \in (i, k]$ for which $\overline{\mathbf{p}_i\mathbf{p}_j}$ is unobstructed across $\mathcal{O}_{\text{local}}$ (defaulting to $j = i + 1$ if no further vertex has line of sight).
* Emit $\mathbf{p}_j$, advance $i \leftarrow j$, and repeat until $i = k$.

##### Math: Space

* Address: `libs.core.math.space`

This module manages the broad-phase spatial partitioning grid.

* **Memory Management (`__init__`, `__dealloc__`)**: Manually allocates continuous blocks of system memory (`malloc`) for its `bucket_counts` and `bucket_data` arrays. Enforces safe teardown via `__dealloc__` calling `free()`, preventing memory leaks.
* **`clear`**: Resets the grid for the current frame by zeroing out the allocated memory block using C's `memset()`.
* **`insert` & `_hash**`: Maps 2D spatial coordinates to a 1D flat array. Assets intersecting cell boundaries are hashed into multiple buckets dynamically.
* **`query`**: Iterates through populated buckets and yields a list of unique `(id1, id2)` integer tuples, generating candidate pairs for narrow-phase evaluation.

##### Math: Physics

* Address: `libs.core.math.physics`

This module orchestrates the physical simulation, bridging the broad-phase grid with narrow-phase resolution, computing forces, and applying velocities to engine states.

* **`collisions`**: The collision pipeline. Ingests a flat list of primitive integer tuples to avoid Python object overhead:
    1. **Hash**: Inserts dynamic assets into the `Space` grid using physical dimensions.
    2. **Query**: Retrieves the reduced list of candidate pairs occupying the same spatial buckets.
    3. **Narrow Phase**: Pre-allocates dummy `Position` and `Dimensions` objects on the C-stack, unpacks candidate primitives, and evaluates overlaps via `geometry.intersects`. Returns verified colliding pairs.
* **`collide`**: Resolves confirmed physical overlaps, accounting for local `Hitbox` offsets:
    1. **Spatial Resolution**: Shifts overlapping entities apart based on inverse mass ratios (e.g., an $m=0$ wall absorbs 0% of the shift, forcing dynamic bodies out).
    2. **Momentum Transfer**: Evaluates 1D elastic collision formulas, updating the `.vx` and `.vy` attributes of participating `Velocity` objects. Kinematic assets bypass momentum transfer to retain immediate vector control.
* **`integrate`**: Executes Symplectic Euler Integration ($x_{n+1} = x_n + v_n \Delta t$). Maintains sub-pixel accumulators (`rx`, `ry`) to update discrete integer positions without drift.
* **`friction`**: Decays the magnitude of a `Velocity` vector over time using an environmental friction coefficient, clamping to $0.0$ to prevent negative overshoot.
* **`kinematics`**: Handles direct velocity assignment. Snaps non-input axes to zero and normalizes the resulting vector to the specified `speed`.
* **`dynamics`**: Calculates acceleration vectors towards a target coordinate (`tx`, `ty`) based on a given `impulse`. Clamps the resulting velocity to `speed` and snaps directly to the target velocity if within the arrival threshold to prevent oscillation.
* **`boundaries`**: Evaluates broad-phase and narrow-phase candidate collisions between dynamic assets and static environmental boundary hulls.
* **`constrain`**: Resolves spatial overlap and inverts velocity vectors for assets colliding with infinitely massive boundary hulls.

#### Library: Graphics

* Address: `libs.core.graphics`

This Library is a Cythonized interface for SDL2 bindings. 

* **Context Initialization (`init`):** Sets up the SDL environment, including video, images, and typography.
* **Asset & Font Allocation (`_load_image`, `_load_font`):** Loads physical image (`.png`) and font (`.ttf`) Assets from the file system into Application memory, returning Cython wrappers. Fonts are pre-styled during ingestion using Configurations.
* **Typography (`measure`, `write`):** `measure` queries the pixel dimensions of a string without allocating a rendering surface. `write` calculates wrapping bounds and alignment, rendering characters as a blended surface that is stamped onto a target texture.
* **Background Compilation (`canvas` & `construct`):** A blank texture is created in memory to match the full size of the Board. 
* **Buffer Management (`clear` & `present`):** `clear` wipes the current buffer while `present` finalizes and displays the current buffer.
* **World Rendering (`render`):** Copies the cropped background texture and then maps world-coordinates to camera-relative coordinates, stamping the active primitives onto the back buffer.
* **Overlays (`superimpose`):** Bypasses the camera offset logic, rendering textures via absolute screen coordinates directly on top of the Screen.

**Memory Management**

* **`TexturePtr`**: Wraps a raw `SDL_Texture*` pointer alongside its integer dimensions (`w`, `l`).
* **`TTFFont`**: Wraps a raw `TTF_Font*` pointer alongside its pre-configured styling metadata.