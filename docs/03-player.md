# Ontology: Player

A Player is a special type of Sprite Sheet Asset. Like all other Assets, its state is maintained in `/src/data/<board>/**.yaml`.

## Overview

The Player Sprite Sheet is configured through the `player` Sheet [Persona Stack](./02-sprites.md#personas).

!!! note
    The value of the Player ID is irrelevant, but  

**Taxonomy**

- `category: sheet`
- `instance: sprite`

**Properties**

- `actions:` 
    - `count: int`
    - `directions:`
        - `row: int`
        - `attackboxes: List[Attackbox]` 
* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]` 

**State**

- `position: Position`
- `layer: str`
- `meters:`
    - `health:` 
        - `current: int`
        - `maximum: int`
    - `magic: int`
        - `current: int`
        - `maximum: int`
- `character:`
    - `strength: int`
    - `defense: int`
    - `speed: int`
- `animation:`
    - `action: str`
    - `direction: str`
    - `frame: int`
- `intention:` 
    - `extension: str`
    - `disposition: str`
    - `motivation: str`
    - `expression: str`
- `inventory:`
    - `loot: Dict[str, int]`
    - `equipment:`
        `armor: str`
        `weapon: str`
        `tool: str`
        `utility: str`
    - `wallet: int`

## Devices

The Player Asset contains a Device, which polls for user input. The main responsiblity of the Player is to translate the data received into Intentions. This is achieved through an input mapping.

### Mapping

Devices have their input mapped to *Intentions* and *Goals*. The mapping configuration file provides a dictionary lookup for what input state corresponds to what game state.

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