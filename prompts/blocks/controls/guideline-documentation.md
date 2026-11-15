**Guideline: Documentation**

* **Flexibility** Treat code as ground truth, but recognize the application is in development and this ground truth will evolve over time. Documentation is an ideal that may not yet be implemented in the code (or it may have been modified to accomodate the realities of code execution); it serves as a design document. It should be respected and consulted for the general direction of the project, but not always enforced. Because the application is currently in development, the documentation may touch on areas that have not yet been implemented or it may assert things of the code that are no longer true. Documentation is in flux while design occurs, so it is open for debate if something is inconsistent or contradictory. Assist in elaborating the nebulous or vague concepts in the documentation.
* **Generality** Documentation should **not** be *hyper-specific*. Do **not** document each and every function call, or `dict` lookup. Do **not** litter the Documentation with string literals, i.e. `tickmarks`. The point of Documentation is to create a metalogical framework for understanding the Application, not for replicating the codebase into pseudocode. Do **not** reference specific function calls like `malloc()` or `cosf()`. The Documentation should **not** contain any reference to implementation-specific libraries beyond the Application libraries themselves. 
* **Concisness** Do **not** change documentation to insert pointless filler words like "*precisely*", "*exactly*", "*pure*", etc. 

**Example: Poor Documentation**

Example of **Extremely Poor** Documentation:

    This module implements the Rapidly-exploring Random Tree (RRT) pathfinding algorithm in pure C memory.

    - **Broad-Phase Culling & Memory Management**: Computes an AABB search window around `(sx, sy)` and `(tx, ty)` padded by `20% + 2 * step_size` (with origin fallback clamping), packing only intersecting obstacles into a contiguous `RRTObstacle*` buffer via `malloc()`. Allocates `RRTNode*` and integer index buffers (`path_buf`, `forward_buf`, `pruned_buf`) sized to `max_iter + 2`, freeing all buffers synchronously in a `try...finally` block.
    - **Tree Representation**: Nodes are represented as flat `RRTNode` structs containing coordinate values and an integer `parent_idx`, eliminating object pointer chasing and heap fragmentation.
    - **Inner Loop (`nogil`)**: Releases the Python GIL during tree exploration. Executes 5% goal-biased continuous coordinate sampling, $O(N)$ nearest-neighbor distance minimization, distance-clamped trigonometric steering (`fminf(step_size, hypotf(dx, dy))`) via `atan2f()`, `cosf()`, and `sinf()`, and line-of-sight segment verification via `c_punctures`.
    - **String-Pulling & Path Reconstruction**: Backtraces the `parent_idx` chain from `target_idx` to the root node, reverses the index chain into `forward_buf`, and executes a `nogil` greedy raycast string-pulling pass (`_prune_path`) to collapse redundant intermediate vertices before re-acquiring the GIL to instantiate Python `Position` models. 

Why this **Extremely Poor** Documentation:

* It *inverts* the order of understanding. Since it does not actually reflect the underlying logic of the Rapidly-exploring Random Tree in anyway, and is more aptly described as a "taxonomy of jargon", a reader cannot understand this block without first reading the Codebase, defeating the entire purpose of Documentation. It actively obscures the algorithm through meaningless jargon. 
* It is littered with specific references to lines in the Codebase. This is a *Dependency* between the Documentation and the Codebase. Anytime the Codebase changes, this section of the Documentation has to be updated to reflect the underlying change. This is not how Documentation should work; Documentation specifies, the Codebase implements. If Documentation needs updated to accomodate the specifics of an implementation, then something is wrong. The Documentation should be *completely* decoupled from the Codebase; all such *Dependencies* should be eliminated when they are detected.
* It references a static idea from a snapshot of the project, e.g. "*eliminating object pointer chasing and heap fragmentation*". If the code actually eliminates this, then it is pointless and counter-productive reintroducing this clause as an idea into future **Contexts**. This is a *Vestige* of the current **Context**, and all such *Vestiges* should be removed from the Documentation.

**Example: Good Documentation**

Example of **Extremely Good** Documentation:

    Let world space be parameterized by $(X, Y, Z)$, where $(X, Y)$ spans the horizontal ground plane ($E = 0$) and $Z \ge 0$ is the vertical elevation axis perpendicular to the ground plane:

    1. **Assumption (Orthographic Parallelism)**: Camera rays are parallel and intersect the horizontal ground plane $(X, Y)$ at a constant inclination angle $\theta = 60^\circ$.
    2. **Assumption (Right Triangle Formation)**: For a point at discrete elevation $E$ dropping by $\Delta E = 1$ to $E - 1$, the vertical elevation change ($\Delta z$), the horizontal ground change ($\Delta y$), and the camera line-of-sight ray ($L_{\text{LOS}}$) form a right triangle $\triangle$ with right angle at the base of the vertical leg and acute angle $\theta = 60^\circ$ at the ground intercept:

    $$
    \tan(\theta) = \frac{\Delta z}{\Delta y}, \qquad \sin(\theta) = \frac{\Delta z}{L_{\text{LOS}}}, \qquad \cos(\theta) = \frac{\Delta y}{L_{\text{LOS}}}
    $$

    **Unit Elevation Drop ($\Delta y_{\text{elevation}}$):**

    Taking the horizontal ground run of one unit Tile as the adjacent leg ($\Delta y = U = 32\text{ px}$), the vertical leg opposite $\theta = 60^\circ$ (the Screen-space $+y$ displacement of one unit elevation) is:

    $$
    \Delta y_{\text{elevation}} = \lfloor U \cdot \tan(60^\circ) \rfloor = \lfloor 32\sqrt{3} \rfloor = 55\text{ px}
    $$

    Equivalently, taking the line-of-sight hypotenuse across a two-tile Sprite frame ($L_{\text{LOS}} = 2U = 64\text{ px}$) yields the same opposite vertical leg:

    $$
    \Delta y_{\text{elevation}} = \lfloor L_{\text{LOS}} \cdot \sin(60^\circ) \rfloor = \left\lfloor 64 \cdot \frac{\sqrt{3}}{2} \right\rfloor = 55\text{ px}
    $$

    Under this formulation, Gravity is purely a property of the topological elevation planes $E \in \mathbb{Z}_{\ge 0}$: every $\Delta y_{\text{elevation}} = \text{TIER_DROP_DISTANCE} = 55\text{ px}$ of vertical freefall transitions an unsupported entity down one discrete elevation plane ($E \to E - 1$), where substrate support is re-evaluated immediately.

Why this **Extremely Good** Documentation:

* The reader requires no knowledge of the Codebase to understand what is going. The Documentation is no less specific or exact for the lack of highly specific and bespoke jargon.
* The Documentation has *no Dependencies* on the Codebase whatsoever. No classes names are referenced, no functions names are enumerated, no specific lines from the Codebase are referenced at all; It is a pure deduction from explicit and well-defined premises.

**Markup: Documentation**

* `@TODO(phase: Optional[str])`: Markup by the **User** to denote key areas that need re-evaluated. If present, review the note and consider using a [Backlog Template `with(not grooming)`](#template-backlog) to open an item in the Backlog, or a [Bug Report](#template-bug-report) to isolate a logical error.
    * `phase`: If `phase` has not been started on the [Task Board](#ontology-task-board), ignore this markup. If `phase = None`, review the note unconditionally.

