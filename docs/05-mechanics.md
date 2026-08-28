# Ontology: Mechanics

A Mechanic is an implementation of an abstract interface the engine calls during the game loop; All Mechanics must implement an `update(board: Board, delta: float)` method. The arguments of this interface are the [Board](./00-overview.md#board) and a game loop time delta. These arguments are injected from above by the [Enegine](./00-overview.md#engine)

## Overview

!!! note
    Mechanics are listed below using `key: class`, where `key` is the unique string identifier for the associated Mechanic implementation class. This `key` is used in the [Mechanics Configuration](#configuration) to specify the order of execution.

### Core

These Mechanics handle the core engine logic.

- `animation AnimationMechanics`: Translates current states into FrameKeys for the renderer.
- `remove: RemoveMechanics`: General garbage collection for Assets whose lifespan has expired.
- `motion: MotionMechanics`: Translates Intentions (hunt, escape, etc.) into physical X/Y velocity vectors, etc.
- `menu: MenuMechanics`: Handles Menu and Widget interactions.

**MotionMechanics**

- Kinematic Assets: Players
- Motive Assets: Sprites
- Inert Assets: Projectiles
- Frictive Assets: Crates

Assets with Mass are divided into Kinenamtic, Motive, Inert and Frictive Assets. Kinematic and Motive Assets have Velocity states with (Speed, Impulse) properties that control their rate of change of Velocity; Frictive and Inert Assets have a Velocity state, but have their Velocities controlled through external forces, i.e. Friction and garbage collection. 

Kinematic Assets snap to velocity vectors and do not change vectorally. This is used for the Player. When the Player presses right, the Player Sprite immediately changes *Velocity* (not Position) to right, snapping to the inputted direction without getting sent into circular motion. In other words, velocities orthogonal to the Player's inputted direction are nulled out by the game loop; Velocity is used to control Player position updates through Symplectic Euler updates, but only applies changes in one direction at once.

Motive Assets generate their own motion through their internal state by applying an Impulse every game tick, a directional acceleration vector that is applied until the magnitude of the resultant Velocity vector is equal to Speed. Motive Assets experience friction to prevent the conservation of momentum sending them into "orbit" around their Goal.

Frictive Assets have motion imparted to them via collisions. Afterwards, the force of friction is applied to the resultant Velocity every game tick until that Velocity has been brought to zero. The force of friction is proportional to the currently occupied Tile's  `properties.friction`.

Inert Assets are exluded from these considerations. They are spawned with a Velocity vector and an initial position; They follow the trajectory determined by these parameters until the distance between their initial and current position exceeds the garbage collection limit.

The general flow of MotionMechanics is given by,

* **Kinematic Motion** Check `device.poll()`. If directional input is present, calculate accelerate velocity to direction and null out orthogonal velocity. If no input is present, hardcode `velocity = (0,0)`.
* **Motive Motion** Calculate the unit vector pointing from `current_position` to `goal_position`. Multiply by `character.impulse` and $\Delta t$. Add to `velocity`. Clamp magnitude to `character.speed`.
* **Frictive Motion** Query `Board.tile()` at asset's center. Calculate $\Delta v = \text{friction} \cdot \Delta t$. Apply $\Delta v$ in the direction opposite to the current `velocity`. If $\Delta v > \vert{}\text{velocity}\vert{}$, set `velocity = (0,0)`.
* **Inert Motion** Exclude Inert from the above steps. For all assets, apply $v \cdot \Delta t$ to the sub-pixel accumulators `rx/ry`. When `rx/ry` exceed $1.0$ or $-1.0$, cast to `int`, shift the physical `Position`, and decrement the accumulator.

The mathematical bounds for Friction are $[0, \infty)$.

* **Lower Bound ($0$):** A value of exactly $0$ yields $\Delta v = 0$, meaning the asset will glide indefinitely without losing momentum until it strikes a static body. A value $< 0$ violates thermodynamic priors; it would yield a negative $\Delta v$, causing the asset to accelerate infinitely opposite to its current trajectory.
* **Upper Bound ($\infty$):** There is no programmatic upper bound. Any value satisfying the condition $\text{friction} \cdot \Delta t \ge \vert v \vert$ instantly halts the asset in a single frame.

The `friction` property defines the rate of linear velocity decay, measured in pixels per second squared ($px/s^2$).

The engine updates the velocity magnitude $v$ via Symplectic Euler Integration:

$$v_{n+1} = \max(0, v_n - \text{friction} \cdot \Delta t)$$

* **Low Friction (e.g., $0.01$):** The deceleration scalar is minute. The asset bleeds momentum extremely slowly, simulating a frictionless surface like ice.
* **High Friction (e.g., $100.0$):** The asset sheds velocity rapidly and comes to rest in a short distance, simulating dense surfaces like mud or deep grass.

**MenuMechanics**

To keep MenuMechanics clean, the Engine uses the **Strategy Pattern** and delegates to MenuController classes. 

MenuMechanics is responsible for *Universal Menu Physics* (e.g. traversal, opening, closing). The MenuController is responsible for *Bespoke Menu Logic* (e.g. equipping, buying, selling).`MenuMechanics only ever interacts with `board.menus[-1]` (the top of the stack).

With the controllers handling the semantic meaning of button presses, MenuMechanics becomes a simple router. Its `update()` loop looks like this:

1. **Check Stack:** If `len(board.menus) == 0`, exit early.
2. **Get Top Menu:** `active_menu = board.menus[-1]`
3. **Poll Input:**
    * If `NORTH/SOUTH/WEST/EAST`: Look at `menu.state.focus`. Look up the key in `active_menu.state.graph`. If a neighbor exists, change `focus` and update the `TraversalAnimation` status of the respective Button Assets.
    * If `SELECT`: Call `active_menu.controller.select(menu.state.focus, menu, board)`.
    * If `CANCEL`: Pop the menu off the stack. (Unpause the board if the stack is now empty).
4. **Tick:** Call `active_menu.controller.update()` so continuous menus (like the HUD) can update their meters.

AnimationMechanics strictly governs "World Time". MenuMechanics governs "Menu Time". The `animate()` interface for Widgets is called inside `MenuMechanics.update()`, iterating over `board.overlays` (always) and `board.menus[-1]` (if active).

### Spatial

These Mechanics handle spatial interactions and collisions between Assets.

- `switch: SwitchMechanics`: (Cython) Binds the Gate and Plate states together based on their `switch`.
- `projectile: ProjectileMechanics`: (Cython) Increment projectile positions, checks intersections and resolves impacts.
- `collision: CollisioMechanics`: Resolves collisions.
- `combat: CombatMechanics`: (Cython) Resolves attack hitbox overlaps, decrements health, etc.
- `interaction: InteractionMechanics`: (Cython) Resolves Asset interactions.

**InteractionMechanics**

!!! note
    `|` is used as a quantifier in the following.

- Source: `source = sprite | sprite.state.intention = 'interact'`
- Target: `target = asset | intersects(sprite, asset)`
- Logic:
    - `if source.instance == 'sprites'`:
        - `if target.instance == 'chests': TODO`
        - `if target.instance == 'doors': source.state.layer = door.state.outlayer` 
    - `if source.instance == 'players':`
        - `if target.instance == 'chests': bus.append(MenuEvent('inventory', player.state)` 
        - `if target.instance == 'doors': source.state.layer = door.state.outlayer` 

**CollisionMechanics**

When Assets collide, overlap resolution uses inverse mass ratios to correct spatial positioning, ensuring immutable Assets with no Mass (`m = 0`) remain completely immobile while dynamic Assets with Mass (`m > 0`) absorb 100% of the displacement shift. Post-separation, Velocities are updated via 1D elastic collision formulas, conserving momentum cleanly across all participating masses,

$$
v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2v_2}{m_1 + m_2}
$$

The [Player](./03-player.md) does not observe momentum transfers. Instead, the Player follows the procedures outlined below,

* **Property Level:** The Player retains a normal, dynamic mass (e.g., $m = 10$).
* **Phase 1 - Spatial Resolution:**
    * **Player vs. Wall ($m=0$):** `inv_total` is $> 0$. The Wall absorbs 0% of the overlap shift, and the Player absorbs 100%. The Player correctly halts at the wall boundary.
    * **Player vs. Crate ($m=5$):** Both absorb the spatial shift proportional to their inverse mass. The Player effectively pushes the Crate out of the way.
* **Phase 2 - Momentum Transfer:** Bypass the 1D elastic collision calculation *only* for the Player.


### Intentional

These Mechanics handle the Sprite Intention logic.

- `player: PlayerMechanics`: Resolve Device input into Player (Intention, Goal)-state.
- `transition: TransitionMechanics`: Applies the Intention Transition Matrix conditions to all Sprite Sheets.
- `commerce: CommerceMechanics`: Translate Intentions (barter, attract, etc.) into trades and price movements.
- `speech: SpeechMechanics`: TODO

## Configuration

* Location: `/src/data/config/mechanics/main.yaml`

Mechanics Configuration defines what Mechanic classes are instantiated by the game engine. The order in which they are specified in the schema becomes the order of execution in the game engine.

```yaml
mechanics:
    order:
        - <mechanic-key>
```