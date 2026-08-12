# Ontology: Mechanics

**General Mechanics**

These Mechanics handle general game logic.

- `PlayerMechanics`: Resolve Device input into Player (Intention, Goal)-state.
- `AnimationMechanics`: Translates current states into FrameKeys for the renderer.
- `CollisioMechanics`: (Cython) Adds velocity to position, resolves wall/crate collisions, etc.
- `RemoveMechanics`: General garbage collection for Assets whose lifespan has expired.
- `TransitionMechanics`: Applies the Intention Transition Matrix conditions to all Sprite Sheets.

**Objective Mechanics**

These Mechanics handle Object game logic.

- `SwitchMechanics`: Binds the Gate and Plate states together based on their `switch`.
- `ProjectileMechanics`: Increment projectile positions, checks intersections and resolves impacts.

**Intentional Mechanics**

These Mechanics handle the Sprite Intention logic.

- `MotionMechanics`: Translates Intentions (hunt, escape, etc.) into physical X/Y velocity vectors, etc.
- `CommerceMechanics`: Translate Intentions (barter, attract, etc.) into trades and price movements.
- `CombatMechanics`: (Cython) Resolves attack hitbox overlaps, decrements health, etc.
- `SpeechMechanics`: 

## TODO