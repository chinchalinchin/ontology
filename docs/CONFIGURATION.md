# Configuration

The configuration files listed below are ingested when the game engine initializes. They are read into memory and accessed through the course of the game, but are not modified in any way.

## Controls

- **Location**: _data/conf/controls.yaml_

This file defines the mapping between user input and player state. **Note**: The state name used in the mapping must be defined in the _sprites.yaml_ sheet for the `hero` sprite (the player character). The example below shows the general syntax, along with comments explaining the purpose of each variable,

```python
```

## Tiles

- **Location**: _data/conf/tiles.yaml_

```yaml
group:
  image:
    file: 
      path: str
      position:
        x: int
        y: int
    size:
      w: int
      h: int
    channels:
      r: int
      g: int
      b: int
      a: int
```

- `group`: name of the group being defined
- `image.file.path`: file name of the asset in _data/assets/tiles/_ used to construct tile frame.
- `image.file.position.x`, `image.file.position.y`: Coordinates in the asset where the tile frame is located.
- `image.size.w`, `image.size.h`: Dimensions of the tile frame in the asset file.`
- `image.channels.r`, `image.channels.g`, `image.channels.b`, `image.channels.a`: (R,G,B,A) definition, instead of a cropped image frame, for a tileset.

**NOTE**: `image.file` and `image.channels` are mutually exclusive. If one is specified, the other cannot be specified. 

**NOTE**: Specifically for _Tiles_: You may specify whatever size you want for the tileset, but only the block defined by the tile dimensions in the settings will be rendered, i.e. only the first 92px by 32px block will be rendered from that tileset.

## Struts

- **Location**: _data/conf/struts.yaml_

This file defines the mapping between struts and their corresponding strutsheet. In particular, it tells the game engine how to crop a group strut from a strutset, by specifying the (_x_, _y_) coordinates of the upper left corner and its dimension (_w_, _h_). In addition, it configures the _Strut_'s hitbox relative to its upper left corner.

As mentioned in previous section, each in-game element builds up complexity on top of the simpler pieces. A _Strut_ contains the same configuration as a _Tile_, plus properties Because of this, the explanation for keys appearing in the previous configurations are excluded. Only new configuration keys are explained.

```yaml
group:
  image:
    file: 
      path: str
      position:
        x: int
        y: int
    size:
      w: int
      h: int
    channels:
      r: int
      g: int
      b: int
      a: int
  properties:
    hitbox:
      offset:
        x:
        y:
      size:
        w:
        h:
```

- `properties.hitbox.offset.x`, `properties.hitbox.offset.y`: How far into the image frame, relative to its top left corner, to start the _Strut_'s hitbox
- `properties.hitbox.size.w`, `properties.hitbox.size.h`: Dimensions of the _Strut_'s hitbox, relative to its `offset`.

## Plates 

- **Location**: _data/conf/plates.yaml_

This file defines the m

As mentioned in previous section, each in-game element builds up complexity on top of the simpler pieces. A _Plate_ contains the same configuration and properties as a _Strut_, plus some additional properties. Because of this, the explanation for keys appearing in the previous configurations are excluded. Only new configuration keys are explained.

```yaml
group:
  image:
    file: 
      path: str
      position:
        x: int
        y: int
    size:
      w: int
      h: int
    channels:
      r: int
      g: int
      b: int
      a: int
  properties:
    hitbox:
      offset:
        x:
        y:
      size:
        w:
        h:
    door: bool
```
- `properties.door`: Signals this particular plateset should be treated as a door.

**Note**: If a plate is configured as a `door`, then when you define its state in _data/state/static.yml_, you must provide an outlet for the door. See [State](./STATE.md) for more information on state definitions.


## Sprites

- **Location**: _data/conf/sprites.yaml_

This file defines the mapping between player state and spritesheet frames through a group named `hero`. Besides the required `hero` configuration, this file will also configure the state mappings between any defined sprites and their spritesheet frames.  **Note**: the state names defined in this file must match the state maps in the _controls.yaml_.

As mentioned in previous section, each in-game element builds up complexity on top of the simpler pieces. A _Sprite_ contains many of the same properties as a _Tile_, _Strut_ and _Plate_, so those definitions are omitted.

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
      aware: int
      poll: int
      paths:
        path_one:
          x: int
          y: int
        path_two:
          x: int
          y: int
  sheets:
    - str
    - str
  blocking_states:
      - str
      - str
  states:
      - state:
          row: int
          frames: int
        
```

**Notes**: Sprites are the most complex object in the game.