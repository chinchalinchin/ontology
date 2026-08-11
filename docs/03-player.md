# Ontology: Player

A Player is a special type of Sprite Sheet Asset. Like all other Assets, its state is maintained in `/src/data/<board>/**.yaml`. 

## Overview

The Player Sprite Sheet is configured through the `player` Sheet [Persona Stack](./02-sprites.md#personas).

**Taxonomy**

- ID: `player`
- Name: `player`
- Category: `sheet`
- Instance: `player`

**Properties: SheetProperties**

- Actions: 
    - Count: `int`
    - Directions:
        - Row: `int`
        - Attackboxes: `List[Attackbox]` 
* Dimensions: `Tuple[int, int]
* Hitboxes: `List[Tuple[int, int, int, int]]` 

**State: PlayerState**

- Name: `str`
- Position: `Tuple[int, int]`
- Layer: `str`
- Meters
    - Health: 
        - Current: `int`
        - Maximum: `int`
    - Magic: `int`
        - Current: `int`
        - Maximum: `int`
- Character
    - Strength: `int`
    - Defense: `int`
    - Speed: `int`
- Animation:
    - Action: `str`
    - Direction: `str`
    - Frame: `int`
- Intention: 
    - Extension: `str`
    - Disposition: `str`
    - Motivation: `str`
    - Expression: `str`
- Inventory:
    - Loot: `Dict[str, int]`
    - Equipment:
        Armor: `str`
        Weapon: `str`
        Tool: `str`
        Utility: `str`
    - Wallet: `int`

### Intentions

Player Intentions do not include the dimensions of Motivation and Communication,

    (Disposition, Expression, Extension)

See [Intentions documentation](./04-intentions.md) for more information.

## Devices

The Player Asset contains a Device, which polls for user input. The main responsiblity of the Player is to translate the data received into Intentions. This is achieved through an input mapping.

### Mapping

Devices have their input mapped to *Intentions*. The mapping configuration file provides a dictionary lookup for what input state corresponds to what game state.

**Keyboard Mappings**

The input state of the Keyboard is polled through SDL. Keyboard mappings correspond to SDL scancodes. See [SDL documentation](https://wiki.libsdl.org/SDL2/SDL_Scancode) for more information.

**Defaults**

The default mappings bundled with the game are provided below,

```yaml
--8<-- "docs/.static/yaml/examples/default-mapping-matrix.yaml"
```

## Schemas

### Device Mappings

* Location: `src/data/player/mappings.yaml`

```yaml
--8<-- "docs/.static/yaml/data-mappings.yaml"
```