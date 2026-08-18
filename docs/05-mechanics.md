# Ontology: Mechanics

A Mechanic is an implementation of an abstract interface that defines what information the engine will inject into the Mechanic's logic; All Mechanics must implement an `update(board, delta)` method. The arguments of this interface are the [Board](./00-overview.md#board) and a game loop time delta.

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

- Motive Assets: Players, Projectiles, Sprites
- Frictive Assets: Crates

Assets with Mass are divided into Motive and Frictive Assets. Motive Assets have (Velocity) states with (Speed, Impulse) properties; Frictive Assets have a (Velocity) state. 

Motive Assets generate their own motion through their internal state by applying an Impulse every game tick, a directional acceleration vector that is applied until the magnitude of the resultant Velocity vector is equal to it is Speed.

Frictive Assets have motion imparted to them via collisions and then the force of friction is applied to the resultant velocity every game tick until their velocity has been brought to zero, where the force of friction is proportional to the currently occupied Tile's  `properties.friction`.

Projectiles are exluded from these considerations. They are spawned with a Velocity vector and an initial position; They follow the trajectory determined by these parameters until the distance between their initial and current position exceeds the garbage collection limit.

The general flow of MotionMechanics is given by,

* **Player Motion** Check `device.poll()`. If directional input is present, calculate impulse vector, apply to `velocity`, and clamp magnitude to `character.speed`. If no input is present, hardcode `velocity = (0,0)`.
* **Sprite Motion** Calculate the unit vector pointing from `current_position` to `goal_position`. Multiply by `character.impulse` and $\Delta t$. Add to `velocity`. Clamp magnitude to `character.speed`.
* **Frictive Asset Motion** Query `Board.tile()` at asset's center. Calculate $\Delta v = \text{friction} \cdot \Delta t$. Apply $\Delta v$ in the direction opposite to the current `velocity`. If $\Delta v > \vert{}\text{velocity}\vert{}$, set `velocity = (0,0)`.
* **Projectile Motion** Exclude Projectiles from the above steps. For all assets, apply $v \cdot \Delta t$ to the sub-pixel accumulators `rx/ry`. When `rx/ry` exceed $1.0$ or $-1.0$, cast to `int`, shift the physical `Position`, and decrement the accumulator.

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
        - `if target.instance == 'chests':`
        - `if target.instance == 'doors': source.state.layer = door.state.outlayer` 
    - `if source.instance == 'players':`
        - `if target.instance == 'chests': bus.append(MenuEvent('inventory', player.state)` 
        - `if target.instance == 'doors': source.state.layer = door.state.outlayer` 

**CollisionMechanics**

When Assets collide, overlap resolution uses inverse mass ratios to correct spatial positioning, ensuring immutable Assets with no Mass (`m = 0`) remain completely immobile while dynamic Assets with Mass (`m > 0`) absorb 100% of the displacement shift. Post-separation, Velocities are updated via 1D elastic collision formulas, conserving momentum cleanly across all participating masses,

$$
v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2v_2}{m_1 + m_2}
$$

### Intentional

These Mechanics handle the Sprite Intention logic.

- `player: PlayerMechanics`: Resolve Device input into Player (Intention, Goal)-state.
- `transition: TransitionMechanics`: Applies the Intention Transition Matrix conditions to all Sprite Sheets.
- `commerce: CommerceMechanics`: Translate Intentions (barter, attract, etc.) into trades and price movements.
- `speech: SpeechMechanics`: 

## Configuration

* Location: `/src/data/config/mechanics/main.yaml`

Mechanics Configuration defines what Mechanic classes are instantiated by the game engine. The order in which they are specified in the schema becomes the order of execution in the game engine.

```yaml
mechanics:
    order:
        - <mechanic-key>
```