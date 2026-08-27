# Ontology: Plots

Due to the nature of the Ontology game engine, a Plot is not scripted, in the sense that Sprite Actions are hardcoded and pre-determined down to the pixels. Conditions are reached to change the World state, which causes a Player's `plot-key` attribute to update. This in turn affects what states can be reached by the gameplay loop. 

[Sprites](./02-sprites.md) retain Communications in their [Memory](./02-sprites.md#memory). These Communications are Lexicon keys to access content in the [Library](#library). They are used in conjunction with the Sprite's `persona` and the [Board's](./00-overview.md#board) plot key to unlock the appropriate content.

As a simple example, a Plot state might be defined to change conditional on the existence of Sprite (perhaps whether a character is alive or dead), call it `<plot>`.

A Sprite, whose `psyche.persona = <persona>` is defined through state files, when entering into a `speak` Intention with `psyche.expression = <lexicon>` (arrived at through [Intention transitions](./04-intentions.md) and [World Mechanics](./05-mechanics.md)), would then retrieve the `<plot>.<persona>.<lexicon>` Dialogue from the Library. 

## Library

* Location: `src/data/config/library/main.yaml`

The Library reads in the scripts stored in `src/data/config/library/main.yaml`, otherwise known as the *library directory*.

TODO

```yaml
library:
    <plot-key>
        <persona-key>:
            <lexicon-key>: <content>
```

- `plot-key`: Current state of the Plot. Determined by the Board.
- `persona-key`: Persona binding for Sprite or Signs. Determined by the Asset.
- `lexicon-key`: Dynamic key for ingame modulation. 

### Plot States


