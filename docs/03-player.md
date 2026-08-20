# Ontology: Player

A Player is a special type of Sprite Sheet Asset. 

## Overview

The Player Sprite Sheet is configured through the `player` Sprite Sheet. 

!!! important
    The `player` Sprite *must* be defined in `/src/assets/sheets/main.yml#sprites`.

**Taxonomy**

- `category: sheets`
- `instance: players`

**Properties: SheetProperties**

- `actions:` 
    - `count: int`
    - `directions:`
        - `row: int`
* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]` 
* `stack: List[str]`

**State: PlayerState**

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
- `goal: Goal`
- `intention: str` 
- `inventory:`
    - `loot: Dict[str, int]`
    - `equipment:`
        `armor: str`
        `weapon: str`
        `tool: str`
        `utility: str`
    - `wallet: int`

## Devices

The [Board](./00-overview.md#board) contains a Device, which polls for user input. The PlayerMechanic uses a Mapping to translate the polling data into a [(Intention, Goal)](./04-intentions.md)-tuple. The [Mapping Configuration](#mapping-configuration) file provides a translation key between input state and game state.

### Keyboard

The input state of the Keyboard is polled through SDL. Keyboard mappings correspond to SDL scancodes. See [SDL documentation](https://wiki.libsdl.org/SDL2/SDL_Scancode) for more information.
