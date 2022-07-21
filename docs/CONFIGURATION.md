# Configuration

The configuration files listed below are ingested when the game engine initializes. They are read into memory and accessed through the course of the game, but are not modified in any way.

## Controls

- **Location**: _data/conf/controls.yaml_

This file defines the mapping between user input and player state. **Note**: The state name used in the mapping must be defined in the _sprites.yaml_ sheet for the `hero` sprite (the player character). The example below shows the general syntax, along with comments explaining the purpose of each variable,

```python
```

## Sprites

- **Location**: _data/conf/sprites.yaml_

This file defines the mapping between player state and spritesheet frames, along with other static information related to sprites. **Note**: the state names defined in this file must match the state maps in the _controls.yaml_.

```yaml
<group>:
  size:
      w: int
      h: int
  properties:
      hitbox:
          offset:
              x: int
              y: int
          size:
              w: int
              h: int
      walk: int
      run: int
      collide: int
  sheets:
      compose:
          - file: str
          - file: str
  blocking_states:
      - str
      - str
  states:
      - state:
          row: int
          frames: int
```

## Struts

- **Location**: _data/conf/struts.yaml_

```yaml
<group>:
  image:
    file: str
    position:
      x: int
      y: int
    size:
      width: int
      height: int
    properties:
      hitbox:
      offset:
        x:
        y:
      dimensions:
        w:
        h:
```

## Tiles

- **Location**: _data/conf/tiles.yaml_

```yaml
group:
  image:
    file: str
    position:
      x: int
      y: int
    size:
      w: int
      h: int
```

1. **image.file**: file name of the asset in _data/assets/tiles/_ used to construct tile frame.
2. **image.position.x**, **image.position.y**: Coordinates in the asset where the tile frame is located.
3. **image.size.w**, **image.size.h**: Dimensions of the tile frame in the asset file.

**NOTE**: `image.position` and `image.size` are used to crop the tiel frame from the asset file.