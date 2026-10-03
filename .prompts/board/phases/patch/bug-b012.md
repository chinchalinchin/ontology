
##### Bug B012: Composition Duplication

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

Reuse of a composition results in duplicate Assets being deployed onto the composed "pseudo" layer.

**Steps to Replicate** 

Composition:

```yaml
compositions:
  brick-house:
    root:
      strut: 
        id: frame-brick
        name: house
      components:
        objects:
          doors:
            - id: door-house
              name: entrance
              outlayer: brick-house-compose-layer
              depth: 1
              height: bind(parent.height) 
              position:
                x: 32
                y: 118
              out:
                x: 82
                y: 143
    branches:
      - strut: 
          id: wall-blue
          name: house-interior
          owner: bind(root.owner)
          layer: brick-house-compose-layer
          depth: 0 
          position:
            x: 0
            y: 0
        components:
          effects:
            passive:
              - id: grandfather-clock
                name: grandfather-clock-00 
                position:
                  x: -4
                  y: 30
                layer: brick-house-compose-layer                
                depth: 0
          objects:
            doors:
              - id: door-shadow
                name: house-doorframe
                layer: brick-house-compose-layer
                outlayer: bind(root.layer)
                depth: 0
                position:
                  x: 47
                  y: 142
                out:
                  x: 43
                  y: 163
            crates:
              - id: wood-bookshelf
                name: house-bookshelf
                layer: brick-house-compose-layer
                depth: 0
                position: 
                  x: 29
                  y: 44
          crafts: 
            struts:
              - id: floor-wood
                name: house-floor
                layer: brick-house-compose-layer
                owner: bind(root.owner)
                depth: 0
                height: -100 # FORCE TO BOTTOM: Always render behind the player
                position:
                  x: 0
                  y: 96
```

State:

```yaml
compositions:
  - id: brick-house
    name: suburbs-00
    layer: '0'
    owner: player
    position:
      x: 200
      y: 750
  - id: brick-house
    name: suburbs-01
    layer: '0'
    owner: archaxes
    position:
      x: 370
      y: 750
```

**Proposed Remeditation**

Decomposer needs to add a unique identifier to each "pseudo" layer in a composition.