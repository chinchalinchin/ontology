# Configuration

The configuration files listed below are ingested when the game engine initializes. They are read into memory and accessed through the course of the game, but are not modified in any way.

## Controls

- **Location**: _data/conf/controls.yaml_

This file defines the mapping between user input and player state. **Note**: The state name used in the mapping must be defined in the _sprites.yaml_ sheet for the `hero` sprite (the player character). The example below shows the general syntax, along with comments explaining the purpose of each variable,

```python
```

## Sprites

- **Location**: _data/conf/sprites.yaml_

This file defines the mapping between player state and spritesheet frames. **Note**: the state names defined in this file 
```python
```
## Struts

- **Location**: _data/conf/struts.yaml_

## Tiles

_data/conf/tiles.yaml_