# Ontology Docs: Architecture

## Specifications

### Specification: Initialization

The [Application](./00-overview.md#application) initialization can be traced through the following phases,

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
2. **Cython**: Initializes video, image, and typography subsystems.
3. **Registry**: Recursively parses the Asset directory, mapping file paths and generating crop-map indexes. *VRAM allocation is completely deferred.*
4. **Components**: Instantiates [Mechanics](./05-mechanics.md) and an empty [Board](./00-overview.md#component-board). 
5. **Ignition**: The [Engine Loop](#specification-engine-loop) begins. A [MenuEvent](./06-widgets.md#events) is injected into the [Engine Bus](./00-overview.md#component-engine) prior to ignition to immediately render the [Main Menu](./06-widgets.md#menu-data).

#### Phase 2: Hydration

When the User selects "*New Game*" or "*Load*" from the [Main Menu](./06-widgets.md#menu-data), an [Event](./06-widgets.md#concept-asychronicity) is thrown to the [Engine Bus](./00-overview.md#component-engine), signaling the onset of the [World Mechanic context](./05-mechanics.md#mechanics-world).

1. **Generation**: The [LoadController](./06-widgets.md#controllers) calls the Migrator each frame. The Migrator applies calls the [Factory](./00-overview.md#service-factory) to generate batches of Assets from the State file, injecting Frame, Animation, Hitbox, Properties, and State components, then yields execution back to the Engine.
2. **Prewarming**: Concurrently, the Registry parses a queue of keys, loading Asset files into memory.
3. **Allocation**: Once hydration is complete, the Migrator triggers the Screen to reallocate canvases for the Painter's Algorithm.
4. **Execution**: The LoadController emits a [TerminalEvent](./06-widgets.md#events), popping the loading screen, activating the Board, and unpausing the [World Mechanics](./05-mechanics.md#mechanics-world).

### Specification: Engine Loop

The Engine delegates behavior to [Mechanics](./05-mechanics.md). Rather than the [Engine](./00-overview.md#component-engine) passing arguments to a system, a Mechanic is responsible for querying the [Board](./00-overview.md#component=board) for the exact data it requires, processing the state, and optionally pushing Events to the Engine Bus.

Mechanics are segregated into `core` pipelines and `world` pipelines. The [Engine](./00-overview.md#component-engine) processes these pipelines conditionally:

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

* **Core Mechanics:** Systems that must execute every tick regardless of the Board State. This includes [MenuMechanics](./05-mechanics.md#core) (to process input and layout traversals), [AnimationMechanics](./05-mechanics.md#core) (to keep Assets animating), and RemoveMechanics (to optimize memory).
* **World Mechanics:** Systems that govern logic, physics, and behavior. This includes [MotionMechanics, CombatMechanics, and PlayerMechanics](./05-mechanics.md).

When an [Event](./06-widgets.md#events) fires and a Menu is pushed to the screen, the Board is paused. The Engine skips the World Mechanics loop entirely. The World freezes, but Core Mechanics continue ticking, allowing the User to navigate the Menu.

### Specification: Board Caches

#### Cache: Spatial Grid

The Board utilizes several spatial hash grids $(c_x, c_y)$:

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

The [Screen](./00-overview.md#component-screen) calculates rendering order using Elevations, Substrates, ground baseline, and a static priority:

$$
\text{sortkey}(A) = \Big(A.\text{elevation}, A.\text{substrate}, \text{ground}(A), A.\text{properties.priority}\Big)
$$

1. **Primary Key (`A.elevation` $\in \mathbb{Z}_{\ge 0}$)**: Discrete elevation (`0`, `1`, `2`, ...).
2. **Secondary Key (`A.substrate` $\in \mathbb{Z}_{\le 0}$)**: Rendering plane within a given elevation:
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

* `size: int`: Font size (defaults to `24`).
* `alignment: str`: Text alignment (`left`, `center`, `right`).
* `bold: bool`
* `italics: bool`
* `underline: bool`
* `strikethrough: bool`
* `margins: float`: Fractional padding applied to the target canvas bounds before wrapping (e.g., `0.05` for 5%).
* `color: Color`: 
    * `r: int` (0–255)
    * `g: int` (0–255)
    * `b: int` (0–255)
    * `a: int` (0–255)
* `outline`: (*Optional*) 
    * `width: int`: Perimeter thickness in pixels
    * `color: Color`:
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

* `x: int`
* `y: int`

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

**Model: Scale**:

* `pw: double`
* `pl: double`

##### Models: Rendering

* **`TexturePtr`**: Wraps a raw `SDL_Texture*` pointer alongside its integer dimensions (`w`, `l`).
* **`TTFFont`**: Wraps a raw `TTF_Font*` pointer alongside its pre-configured styling metadata.

#### Library: Math

* Address: `libs.core.math`

The mathematical foundation of the Engine operates over the two-dimensional Euclidean plane $\mathbb{R}^2$ and its discrete integer lattice $\mathbb{Z}^2$:

* *Coordinate Space*: Each Layer defines an independent Cartesian plane with origin $(0, 0)$ at the upper-left corner, $+x$ directed right, and $+y$ directed down.
*  *Bounding Primitives*: A rectangular region (Axis-Aligned Bounding Box, or AABB) is parameterized by its upper-left origin $(x, y)$ and non-negative dimensions $(w, l)$, spanning the half-open interval:

$$
R(x, y, w, l) = [x, x + w) \times [y, y + l)
$$

* *Composite Footprints*: An Asset at world position $(x_a, y_a)$ with relative Hitboxes $\{(x_i, y_i, w_i, l_i)\}$ occupies the union of translated bounding boxes:

$$
\mathcal{H}(A) = \bigcup_{i} \big[x_a + x_i, x_a + x_i + w_i\big) \times \big[y_a + y_i, y_a + y_i + l_i\big)
$$

##### Math: Geometry

* Address: `libs.core.math.geometry`

**Interfaces**

1. **`intersects`**: Calculates Axis-Aligned Bounding Box intersections.

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

2. **`onscreen`**: Evaluates if an Asset intersects with the Screen Camera.

For a Camera of dimensions $(w_s, l_s)$ centered on a focus at $(x_f, y_f)$ with dimensions $(w_f, l_f)$, the camera origin is:

$$
x_c = x_f + \left\lfloor \frac{w_f}{2} \right\rfloor - \left\lfloor \frac{w_s}{2} \right\rfloor
$$
$$y_c = y_f + \left\lfloor \frac{l_f}{2} \right\rfloor - \left\lfloor \frac{l_s}{2} \right\rfloor
$$

An Asset is visible on screen if its bounding box intersects $R(x_c, y_c, w_s, l_s)$.

3. **`cone`**: Field-of-view check validating whether a target coordinate falls within a parameterized directional vision cone.

    Given a source point $\mathbf{s} = (s_x, s_y)$ and a target point $\mathbf{t} = (t_x, t_y)$ with displacement $\mathbf{d} = \mathbf{t} - \mathbf{s} = (\Delta x, \Delta y)$:

    Given a cardinal unit heading vector $\hat{\mathbf{u}} \in \{(0, -1), (0, 1), (-1, 0), (1, 0)\}$ and angular cosine threshold $\cos\alpha$, $\mathbf{t}$ lies within the field of view of radius $r$ when $\|\mathbf{d}\|^2 \le r^2$ and:

    $$
    (\mathbf{d} = \mathbf{0})
    \lor
    (\frac{\mathbf{d} \cdot \hat{\mathbf{u}}}{\|\mathbf{d}\|} \ge \cos\alpha)
    $$

    4. **`nearby`**: Euclidean distance check.

    $\mathbf{t}$ lies within radius $r$ of $\mathbf{s}$ if and only if:

    $$
    \|\mathbf{d}\|^2 = \Delta x^2 + \Delta y^2 < r^2
    $$

5. **`punctures`**: Implementation of the Liang-Barsky line clipping algorithm. Evaluates whether a line segment $(x_1, y_1) \to (x_2, y_2)$ penetrates the interior of an AABB obstacle with non-degenerate penetration depth ($u_1 < u_2 - \epsilon$).

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

6. **`los`**: Raycasts a line-of-sight segment across a collection of primitive AABB tuples.

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

7. **`contours`**: Executes a two-pass Sweep-Line algorithm over primitive AABBs to generate map boundaries. Uses interval merging and XOR symmetric differences to isolate exposed contour edges, returning boundary segments.

    Given a family of axis-aligned rectangles $\{R_i = [x_{i,\min}, x_{i,\max}] \times [y_{i,\min}, y_{i,\max}]\}$, the exposed boundary contours of their union $\mathcal{U} = \bigcup_i R_i$ are derived via a two-pass orthogonal sweep:

    * *Vertical Sweep*: Sort all vertical edges by $x$-coordinate, pairing $x_{i,\min}$ with event $+1$ and $x_{i,\max}$ with event $-1$. At each event coordinate $x$, let $I_{\text{prev}}$ and $I_{\text{curr}}$ denote the merged 1D $y$-intervals of active rectangles before and after $x$. The asymmetric set differences isolate the exposed vertical contour segments at $x$:

    $$
    E_{\text{left}}(x) = I_{\text{curr}} \setminus I_{\text{prev}}
    $$
    $$
    E_{\text{right}}(x) = I_{\text{prev}} \setminus I_{\text{curr}}
    $$

    * *Horizontal Sweep*: Sort all horizontal edges by $y$-coordinate, pairing $y_{i,\min}$ with $+1$ and $y_{i,\max}$ with $-1$. Comparing the merged 1D $x$-intervals $J_{\text{prev}}$ and $J_{\text{curr}}$ isolates the exposed horizontal contour segments at $y$:

8. **`bounded`** Narrow-phase validation checking whether an Asset's offset hitboxes intersect a raw mathematical boundary constraint.

##### Math: Paths

* Address: `libs.core.math.paths`

Given a start coordinate $\mathbf{s} = (s_x, s_y)$, a target coordinate $\mathbf{t} = (t_x, t_y)$, a step size $\delta > 0$, an iteration limit $N_{\max}$, and a set of obstacle rectangles $\mathcal{O}$ (inflated in configuration space by the navigating Sprite's Hitbox half-dimensions and clearance radius), pathfinding constructs a collision-free trajectory from $\mathbf{s}$ to $\mathbf{t}$ via a Rapidly-exploring Random Tree (RRT).

**Interface**

1. **`rrt`**
    * *Search Window Partitioning*: Define a padded search domain enclosing $\mathbf{s}$ and $\mathbf{t}$ with margin $\mathbf{m} = (0.2|t_x - s_x| + 2\delta, 0.2|t_y - s_y| + 2\delta)$:

    $$
    [x_{\min}, x_{\max}] = [\min(s_x, t_x) - m_x, \max(s_x, t_x) + m_x]
    $$
    $$
    [y_{\min}, y_{\max}] = [\min(s_y, t_y) - m_y,\; \max(s_y, t_y) + m_y]
    $$

    If $x_{\min} < 0$ or $y_{\min} < 0$, the negative offset is added to the corresponding upper bound and the lower bound is clamped to $0$. The active obstacle set is restricted to $\mathcal{O}_{\text{local}} = \{R \in \mathcal{O} \mid R \cap ([x_{\min}, x_{\max}] \times [y_{\min}, y_{\max}]) \neq \emptyset\}$.

    * *Goal-Biased Tree Expansion*: Initialize a tree $\mathcal{T} = (V, E)$ rooted at $\mathbf{v}_0 = \mathbf{s}$. For up to $N_{\max}$ iterations:

    * *Sampling*: Draw $u, u_x, u_y \sim \mathcal{U}(0, 1)$ with goal bias $p_{\text{goal}} = 0.05$:

    $$
    \mathbf{q} = \begin{cases} \mathbf{t} & \text{if } u \le p_{\text{goal}} \\ \big(x_{\min} + u_x(x_{\max} - x_{\min}),\; y_{\min} + u_y(y_{\max} - y_{\min})\big) & \text{otherwise} \end{cases}
    $$

    * *Nearest Neighbor*: Select the tree vertex $\mathbf{v}_{\text{near}} \in V$ minimizing Euclidean distance to $\mathbf{q}$:

    $$
    \mathbf{v}_{\text{near}} = \arg\min_{\mathbf{v} \in V} \|\mathbf{v} - \mathbf{q}\|_2
    $$

    * *Clamped Steering*: Step from $\mathbf{v}_{\text{near}}$ toward $\mathbf{q}$ by distance $d = \min(\delta, \|\mathbf{q} - \mathbf{v}_{\text{near}}\|_2)$ along angle $\theta = \operatorname{atan2}(q_y - v_{\text{near},y},\; q_x - v_{\text{near},x})$:

    $$
    \mathbf{v}_{\text{new}} = \mathbf{v}_{\text{near}} + d\begin{pmatrix} \cos\theta \\ \sin\theta \end{pmatrix}
    $$

    * *Edge Validation & Termination*: If the segment $\overline{\mathbf{v}_{\text{near}}\mathbf{v}_{\text{new}}}$ is unobstructed across $\mathcal{O}_{\text{local}}$, add $\mathbf{v}_{\text{new}}$ to $V$ with parent $\mathbf{v}_{\text{near}}$. If $\mathbf{v}_{\text{new}} = \mathbf{t}$, or if $\|\mathbf{t} - \mathbf{v}_{\text{new}}\|_2 \le \delta$ and $\overline{\mathbf{v}_{\text{new}}\mathbf{t}}$ is unobstructed, append $\mathbf{t}$ to $\mathcal{T}$ and terminate exploration.

    * *Backtracing & String-Pulling Pruning**: Traverse parent links from $\mathbf{t}$ to $\mathbf{v}_0$ and reverse the sequence to form the unpruned chain $\mathbf{p}_0, \mathbf{p}_1, \dots, \mathbf{p}_k$ ($\mathbf{p}_0 = \mathbf{s}$, $\mathbf{p}_k = \mathbf{t}$). Redundant intermediate vertices are collapsed via greedy line-of-sight string-pulling:
        * From current anchor index $i$ (initialized to $0$), select the largest index $j \in (i, k]$ for which $\overline{\mathbf{p}_i\mathbf{p}_j}$ is unobstructed across $\mathcal{O}_{\text{local}}$ (defaulting to $j = i + 1$ if no further vertex has line of sight).
        * Emit $\mathbf{p}_j$, advance $i \leftarrow j$, and repeat until $i = k$.

##### Math: Space

* Address: `libs.core.math.space`

An Asset with Dimensions $[x, x + w] \times [y, y + l]$ covers the integer cell coordinates:

$$
c_x \in \left[\left\lfloor \frac{x}{C} \right\rfloor,\; \left\lfloor \frac{x + w}{C} \right\rfloor\right]
$$
$$c_y \in \left[\left\lfloor \frac{y}{C} \right\rfloor,\; \left\lfloor \frac{y + l}{C} \right\rfloor\right]
$$

**Interfaces**

1. **`insert`**: Maps coordinates to their flat hashed array.

    Each covered cell $(c_x, c_y)$ maps to a bucket index $h(c_x, c_y) \in \{0, \dots, M - 1\}$ via multiplicative prime hashing:

    $$
    h(c_x, c_y) = (c_x \cdot p_1 \oplus c_y \cdot p_2) \bmod M
    $$

    where $p_1, p_2$ are large coprime integers. The Asset identifier is inserted into each bucket its bounding box intersects.

2. **`query`**: Iterating through populated buckets yields unique unordered pairs $(i, j)$ with $i < j$ that share at least one bucket, forming the broad-phase candidate set for narrow-phase evaluation.

3. **`clear`**: Resets the grid for the current frame by zeroing out the allocated memory block.

##### Math: Physics

* Address: `libs.core.math.physics`

**Interfaces**

1. **`collisions`**

    * *Broad Phase*: Assets are hashed into the spatial grid by their bounding footprints to produce candidate pairs $(A_1, A_2)$.
    * *Narrow Phase*: Candidate pairs are evaluated for intersection across their offset hitboxes $\mathcal{H}(A_1) \cap \mathcal{H}(A_2) \neq \emptyset$.

2. **`collide`**

    * *Minimum Translation Vector & Inverse-Mass Separation*: For two intersecting hitboxes $H_1 = [x_1, x_1 + w_1] \times [y_1, y_1 + l_1]$ and $H_2 = [x_2, x_2 + w_2] \times [y_2, y_2 + l_2]$ with centers $\mathbf{c}_1, \mathbf{c}_2$, the axial overlap depths are:

    $$
    \delta_x = \frac{w_1 + w_2}{2} - |c_{1,x} - c_{2,x}|, \qquad \delta_y = \frac{l_1 + l_2}{2} - |c_{1,y} - c_{2,y}|
    $$

    Separation occurs along the axis of minimum penetration $\delta = \min(\delta_x, \delta_y)$ with unit normal $\hat{\mathbf{n}}$. Define each body's inverse mass $\mu_i$ such that static obstacles ($m_i = 0$) have $\mu_i = 0$ ($m_i \to \infty$) and dynamic bodies ($m_i > 0$) have $\mu_i = 1 / m_i$. For $\mu_{\text{total}} = \mu_1 + \mu_2 > 0$, each body is displaced in proportion to its inverse mass share:

    $$
    \Delta \mathbf{r}_1 = -\delta \left(\frac{\mu_1}{\mu_{\text{total}}}\right) \hat{\mathbf{n}}, \qquad \Delta \mathbf{r}_2 = +\delta \left(\frac{\mu_2}{\mu_{\text{total}}}\right) \hat{\mathbf{n}}
    $$

    * *One-Dimensional Elastic Momentum Transfer* Along the collision normal, post-separation velocities $(v_{1f}, v_{2f})$ follow conservation of momentum and kinetic energy:

    $$
    v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2 v_2}{m_1 + m_2}, \qquad v_{2f} = \frac{v_2(m_2 - m_1) + 2m_1 v_1}{m_1 + m_2}
    $$

    Against a static body ($m_2 = 0 \implies m_2 \to \infty$), the dynamic body's normal velocity inverts ($v_{1f} = -v_1$). Kinematic entities participate in inverse-mass spatial separation using their nominal mass $m_1 > 0$, but bypass velocity reassignment.

3. **`integrate`**: Executes Symplectic Euler Integration ($x_{n+1} = x_n + v_n \Delta t$). 

    Because positions $(x_n, y_n) \in \mathbb{Z}^2$ are discrete integers while velocities $(v_x, v_y) \in \mathbb{R}^2$ and timesteps $\Delta t \in \mathbb{R}_{>0}$ are continuous, fractional sub-pixel remainders $(r_x, r_y) \in (-1, 1)$ are accumulated across frames:

    $$
    \begin{aligned}
    \tilde{r}_x &= r_{x,n} + v_x \Delta t, & \Delta x &= \operatorname{trunc}(\tilde{r}_x), & x_{n+1} &= x_n + \Delta x, & r_{x,n+1} &= \tilde{r}_x - \Delta x \\
    \tilde{r}_y &= r_{y,n} + v_y \Delta t, & \Delta y &= \operatorname{trunc}(\tilde{r}_y), & y_{n+1} &= y_n + \Delta y, & r_{y,n+1} &= \tilde{r}_y - \Delta y
    \end{aligned}
    $$

4. **`friction`**: Decays the magnitude of a Velocity vector over time using an Environ Tile friction coefficient.

    For an entity with velocity $\mathbf{v}_n$ traversing a surface with friction coefficient $\mu_f \ge 0$ over timestep $\Delta t$, speed decays linearly to a lower bound of $0$:

    $$
    s_{n+1} = \max\big(0,\; \|\mathbf{v}_n\| - \mu_f \Delta t\big), \qquad \mathbf{v}_{n+1} = \begin{cases} \dfrac{s_{n+1}}{\|\mathbf{v}_n\|}\mathbf{v}_n & \text{if } \|\mathbf{v}_n\| > 0 \\ \mathbf{0} & \text{otherwise} \end{cases}
    $$

5.  **`kinematics`**: Handles direct velocity assignment. Snaps non-input axes to zero and normalizes the resulting vector.

    Given directional input vector $\mathbf{d}_{\text{input}}$ and speed $s$, non-active axes snap to $0$ and the velocity vector is normalized to magnitude $s$:

    $$
    \mathbf{v} = \begin{cases} s \dfrac{\mathbf{d}_{\text{input}}}{\|\mathbf{d}_{\text{input}}\|} & \text{if } \|\mathbf{d}_{\text{input}}\| > 0 \\ \mathbf{0} & \text{otherwise} \end{cases}
    $$

6.  **`dynamics`**: Calculates acceleration vectors towards a target coordinate. 

    Given position $\mathbf{r} = (x, y)$, target $\mathbf{t} = (t_x, t_y)$, impulse $a$, and maximum speed $s$, let $\mathbf{d} = \mathbf{t} - \mathbf{r}$ and $\hat{\mathbf{d}} = \mathbf{d} / \|\mathbf{d}\|$. Velocity accelerates along $\hat{\mathbf{d}}$ and is clamped to $s$:

    If $\|\mathbf{d}\|$ lies within the single-tick arrival threshold, velocity snaps to the remaining displacement to prevent oscillation.

7. **`boundaries`**: Evaluates broad-phase and narrow-phase candidate collisions between dynamic assets and static environmental boundary hulls.

    Environmental perimeters act as directed barriers with $\mu_{\text{bound}} = 0$. When an Asset's Hitbox penetrates a boundary segment, the Asset is displaced out of the overlap along the boundary normal by penetration depth $\delta$ and its normal velocity component is inverted.

8.  **`constrain`**: Resolves spatial overlap and inverts velocity vectors for assets colliding with infinitely massive boundary hulls.

#### Library: Graphics

* Address: `libs.core.graphics`

This Library is a Cythonized interface for SDL2 bindings. 

* **Context Initialization (`init`):** Sets up the SDL environment, including video, images, and typography.
* **Asset & Font Allocation (`_load_image`, `_load_font`):** Loads physical image (`.png`) and font (`.ttf`) Assets from the file system into Application memory, returning Cython wrappers. 
* **Typography (`measure`, `write`):** `measure` queries the pixel dimensions of a string without allocating a rendering surface. `write` calculates wrapping bounds and alignment, rendering characters as a blended surface that is stamped onto a target texture.
* **Background Compilation (`canvas` & `construct`):** `canvas` creates a blank texture in memory to match the full size of the Board. Flat lists of Environ Tile tuples are passed into `construct` to cache prerendered textures for the background of the Screen.
* **Buffer Management (`clear` & `present`):** `clear` wipes the current buffer while `present` finalizes and displays the current buffer.
* **World Rendering (`render`):** Copies the cropped background texture and then maps world-coordinates to camera-relative coordinates, stamping the active primitives onto the back buffer.
* **Overlays (`superimpose`):** Bypasses the camera offset logic, rendering textures via absolute screen coordinates directly on top of the Screen.