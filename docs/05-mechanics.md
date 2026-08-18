# Ontology: Mechanics

A Mechanic is an implementation of an abstract interface that defines what information the engine will inject into the Mechanic's logic.  All Mechanics must implement an `update(board, delta)` method. The arguments of this interface are the [Board](./00-overview.md#board) and a game loop time delta.

## Overview

!!! note
    Mechanics are listed below using `key: class`, where `key` is the unique string identifier for the associated Mechanic implementation class.

### Core

These Mechanics handle the core engine logic.

- `animation AnimationMechanics`: Translates current states into FrameKeys for the renderer.
- `remove: RemoveMechanics`: General garbage collection for Assets whose lifespan has expired.
- `motion: MotionMechanics`: Translates Intentions (hunt, escape, etc.) into physical X/Y velocity vectors, etc.

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

TODO

### Intentional

These Mechanics handle the Sprite Intention logic.

- `player: PlayerMechanics`: Resolve Device input into Player (Intention, Goal)-state.
- `transition: TransitionMechanics`: Applies the Intention Transition Matrix conditions to all Sprite Sheets.
- `commerce: CommerceMechanics`: Translate Intentions (barter, attract, etc.) into trades and price movements.
- `speech: SpeechMechanics`: 

## Configuration

* Location: `/src/data/config/mechanics/main.yaml`

```yaml
mechanics:
    order:
        - <mechanic-key>
```