

##### Draft: Three-Tier Sheet State & Component Hierarchy

- **Page**: `docs/01-assets.md` & `docs/02-sprites.md`
- **Heading**: `###### Sheet: Pixies` (`01-assets.md`), `###### Sheet: Sprite` & `###### Sheet: Player` (`02-sprites.md`)

###### Drift

`docs/01-assets.md` leaves Pixie State as `TBD`, while `docs/02-sprites.md` describes `PlayerState` as an informal truncation of `SpriteState` without specifying the strict three-tier inheritance across States, Frames, and Animations. This ambiguity caused `Player`, `Sprite`, and `Pixie` deployments to share incompatible state and component strategies.

###### Update

```markdown
##### Sheet Hierarchy: States, Frames & Animations

Stateful Sheet Instances partition along a three-tier specialization hierarchy so each Instance carries strictly the data and rendering strategies required by its domain:

1. **Base Tier (`Pixies`)**:
   * **State (`SheetState`)**: Spatial and animation primitives (`position`, `velocity`, `animation`).
   * **Frame (`StateFrame`)**: Projects `(action, direction, frame)` onto the Sheet atlas.
   * **Animation (`StateAnimation`)**: Advances `(action, direction, frame)` according to Action count and delay.

2. **Character Tier (`Players`)**:
   * **State (`CharacterState` extends `SheetState`)**: Adds intentionality and physical agency (`intention`, `goal`, `character`, `slots`, `inventory`, `meters`).
   * **Frame (`CharacterFrame` extends `StateFrame`)**: Superimposes active Equipment frames in Z-order (`armor`, `utility`, `tool`, `weapon`, `shield`) over the base Sheet.
   * **Animation (`CharacterAnimation` extends `StateAnimation`)**: Gates body-frame advancement on `mutators.triggers.animated`, resetting idle animations to frame `0`.

3. **Autonomous Tier (`Sprites`)**:
   * **State (`SpriteState` extends `CharacterState`)**: Adds autonomous cognition and navigation (`psyche`, `memory`, `trajectory`).
   * **Frame (`SpriteFrame` extends `CharacterFrame`)**: Appends active Psyche Expression overlays at their configured spatial offset.
   * **Animation (`SpriteAnimation` extends `CharacterAnimation`)**: Advances body animations while decaying `psyche.expression.ttl` unconditionally on every tick, independent of body movement or `triggers.animated`.
```

---

##### Draft: Intention Transition Matrix Examples & Function Signature Drift

- **Page**: `docs/04-intentions.md`
- **Heading**: `###### Intention: Transition Matrix`

###### Drift

The prose example references `sprite.memory.goal.category == constants.Goals.TARGET.value` (whereas `memory.goals` is a mapping of Goal entries) and documents `any_goals(m: List[Goal], category: str)` when `memory.goals` is `Dict[str, Goal]`.

###### Update

```markdown
* `any_goals(goals: Dict[str, Goal], category: Optional[str])`: Determines whether any remembered Goal matches the requested Category (or whether Memory contains any Goals when `category` is omitted).
```

---

##### Draft: Three-Tier Sheet State Hierarchy & Mutator Parameters

* **Page**: `docs/01-assets.md`
* **Heading**: `Concept: Mutability` & `Sheet: Pixies`

###### Drift

`Model: Mutators` declares `parameters.action` and `parameters.vision` as booleans instead of spatial radii. `Sheet: Pixies` lists its State as `TBD`, diverging from the three-tier Sheet hierarchy (`Sheet` $\to$ `Character` $\to$ `Sprite`).

###### Update

**Model: Mutators**

* `parameters`: Numeric and categorical bounds modulating conditional calculations.
* `action: int`: Spatial radius of interaction.
* `vision: int`: Spatial radius of perception.


* `triggers`: Boolean flags.
* `animated: bool`: Flag governing animation progression.
* `dead: bool`: Flag indicating terminal state.
* `submerged: bool`: Flag governing aquatic frame modulation.

**Sheet: Pixies**

Pixies are kinematic Sheets excluded from equipment slotting, inventory management, and intentional goal loops. Their State inherits the minimal kinematic base (`Position`, `Velocity`, `AnimationState`) shared by all Sheets, while Characters extend this base with equipment, inventory, meters, intention, and goal, and Sprites further extend Characters with episodic memory, psyche, and trajectory.

---

##### Draft: Direction Mapping Sign Convention & Intentional Propositions

* **Page**: `docs/04-intentions.md`
* **Heading**: `Intention: Transition Matrix` & `Mapping: Directions`

###### Drift

1. Under `Direction Mapping: Sprite`, displacement is defined as $\text{position} - \text{target}$ while mapping $\Delta y > 0$ to `down`. Under the top-left origin coordinate system ($+y$ downward), a target below the Sprite satisfies $\text{target}.y > \text{position}.y$, so $\text{position}.y - \text{target}.y < 0$; the sign convention is inverted (and the formula contains malformed math delimiters).
2. Under `Concept: Intentional Propositions`, examples reference nonexistent singular `sprite.memory.goal.category` and `sprite.memory.communications`.

###### Update

**Direction Mapping: Sprite**

Let $\mathbf{p} = (p_x, p_y)$ be the Sprite position and $\mathbf{t} = (t_x, t_y)$ be the active target coordinate (the next trajectory waypoint if present, otherwise the goal position). Define displacement toward the target as:

$$\Delta x = t_x - p_x, \qquad \Delta y = t_y - p_y$$

Partitioning the plane along the diagonals $|\Delta y| = |\Delta x|$ maps displacement onto cardinal headings:

$$\begin{aligned}
(\Delta y > \Delta x \;\land\; \Delta y > -\Delta x) &\implies \text{down} \\
(\Delta y < \Delta x \;\land\; \Delta y > -\Delta x) &\implies \text{right} \\
(\Delta y < \Delta x \;\land\; \Delta y < -\Delta x) &\implies \text{up} \\
(\Delta y > \Delta x \;\land\; \Delta y < -\Delta x) &\implies \text{left}
\end{aligned}$$

---

##### Draft: Formal Intention Loops, Commitment Stack & Epistemic Perception

* **Page**: `docs/04-intentions.md`
* **Heading**: `Concept: Intention Loops` & `Workflow Component: Cognition`

###### Drift

The current documentation conflates unordered episodic goal memory with suspended subgoal commitments (such as cross-layer portal traversal) and does not state the epistemic boundary of perception or the invariant-monitoring contract between Goal resolution and Intention transitions.

###### Update

**Concept: Intention Loops**

Each Intention Loop rooted at `idle` forms a temporally extended option $\langle I, \pi, \beta \rangle$:

1. **Initiation ($I$):** The Entrypoint transition $\text{idle} : i_1$ together with any required equipment admissibility constraint.
2. **Execution ($\pi$):** Interpoint transitions $i_j : i_{j+1}$ ($i_j, i_{j+1} \neq \text{idle}$) paired with spatial and navigational mechanics.
3. **Termination ($\beta$):** Goal resolution (`complete` or `lost`) or a context-invariant violation (the active Goal category no longer matches the active Intention), routing the Sprite back to `idle` via an Exitpoint $i_{n-1} : \text{idle}$.

**Workflow Component: Cognition**

Cognition distinguishes three cognitive stores:

* **Perception (Beliefs):** Same-Layer sensory updates bounded by vision radius. Unseen entities freeze at their last observed Layer and coordinates until re-observed.
* **Commitment Stack (Intentions):** An ordered LIFO stack of parent Goals suspended by prerequisite subgoals (such as a Layer-transit Door). Completing a prerequisite immediately resumes the top suspended parent Goal.
* **Episodic Memory (Desires):** An unordered store of abandoned or remembered Goals evaluated only when the Commitment Stack is empty, filtered by Intention compatibility and live-visibility dormancy.