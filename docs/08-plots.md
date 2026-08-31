# Ontology: Plots

Due to the nature of the Ontology game engine, a Plot is not scripted, in the sense that Sprite Actions are hardcoded and pre-determined down to the pixel. Conditions are reached to change the World state, which causes the [Board's](./00-overview.md#board) `plot` attribute to update. This in turn affects what dialogue keys can be reached by the gameplay loop. 

[Sprites](./02-sprites.md) retain a Expression in their [Psyche](./02-sprites.md#psyche). This Expression is a Lexicon key to access content in the [Library](#library). It is used in conjunction with the Sprite's `persona` and the [Board's](./00-overview.md#board) `plot` key to unlock the appropriate content.

As a simple example, a Plot state might be defined to change conditional on the existence of Sprite (perhaps whether a character is alive or dead), call it `<plot>`.

A Sprite, whose `psyche.persona = <persona>` is defined through state files, when entering into a `speak` Intention with `psyche.expression = <lexicon>` (arrived at through [Intention transitions](./04-intentions.md) and [World Mechanics](./05-mechanics.md)), would then retrieve the `<plot>.<persona>.<lexicon>` dialogue from the Library. 

## Library

* Location: `src/data/config/library/main.yaml`

The Library reads in the dialogue scripts stored in `src/data/config/library/main.yaml`, otherwise known as the *library directory*.

TODO

```yaml
library:
    <plot-key>:
        <persona-key>:
            <lexicon-key>: <content>
```

- `plot-key`: Current state of the Plot. Determined by the Board.
- `persona-key`: Persona binding for Sprite or Signs. Determined by the Asset.
- `lexicon-key`: Dynamic key for ingame modulation. 

## Plot States

The Plot is an Asset-less State. It is instantiated during [initialization](./09-architecture.md#initialization) and injected into the Board. 

TODO

## Plot Mechanics

PlotMechanics are a [World Mechanic](./05-mechanics.md) that manages the Plot State. It does so through the medium of the *Plot Transition Matrix*.

### Transition Matrix

Similar to [Intentions](./04-intentions.md), the Plot utilizes a Transition Matrix to determine where the current node of the Plot State resides, and whether or not conditions have been met to transition to the next node.

The general schema for a row of Plot Transitions is given directly below,

```yaml
plots:
    <plot-state>:
        - next: <plot-state>
          conditions:
            - <condition>
```

For example, the following Plot Transition Matrix demonstrates how a Plot tree can be embedded into the game by specifying nodes and the conditions that must be met to transition out of a given node, 

```yaml
plots:
    town-locked:
        - next: town-unlocked
          conditions:
            - player.state.inventory.loot['town-key'] >= 1
        - next: town-unlocked
          conditions:
            - sprites['town-guard'].mutators.triggers.dead
        - next: town-unlocked
          conditions:
            - sprites['mayor'].state.memory.relationships['player'] == Relationships.FRIEND
    town-unlocked:
        - next: town-hostile
          conditions:
            - sprites['mayor'].state.memory.relationships['player'] == Relationships.FOE
    town-hostile:
        - next: town-unlocked
          conditions:
            - sprites['mayor'].state.memory.relationships['player'] != Relationships.FOE
```

TODO