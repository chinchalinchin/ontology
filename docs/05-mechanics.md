# Ontology: Mechanics

**General Mechanics**

These Mechanics handle general game logic.

- `player: PlayerMechanics`: Resolve Device input into Player (Intention, Goal)-state.
- `animation AnimationMechanics`: Translates current states into FrameKeys for the renderer.
- `collision: CollisioMechanics`: (Cython) Adds velocity to position, resolves wall/crate collisions, etc.
- `remove: RemoveMechanics`: General garbage collection for Assets whose lifespan has expired.

**Object Mechanics**

These Mechanics handle Object game logic.

- `SwitchMechanics`: Binds the Gate and Plate states together based on their `switch`.
- `ProjectileMechanics`: Increment projectile positions, checks intersections and resolves impacts.

**Sprite Mechanics**

These Mechanics handle the Sprite Intention logic.

- `transition: TransitionMechanics`: Applies the Intention Transition Matrix conditions to all Sprite Sheets.
- `motion: MotionMechanics`: Translates Intentions (hunt, escape, etc.) into physical X/Y velocity vectors, etc.
- `commerce: CommerceMechanics`: Translate Intentions (barter, attract, etc.) into trades and price movements.
- `combat: CombatMechanics`: (Cython) Resolves attack hitbox overlaps, decrements health, etc.
- `speech: SpeechMechanics`: 

## Configuratoin

* Location: `/src/data/mechanics/main.yaml`

```yaml
mechanics:
    order:
        - <mechanic-key>
```