
##### Bug B012: Composition Duplication

**STATUS**: CLOSED
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

State Dump (`python src/cli.py --dump-state start`):

(...Irrelevant sections elided...)

```markdown
# Perimeters

## strut-house-1

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `frame-brick`
  - Name: `strut-house-1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 96
    - Length: 190
- Mass: 0
- Cost:
- `stone`: 10
- Hitboxes:
- Position: (10, 20) | Dimensions: w: 76, l: 144
- **State:**
- Layer: `0`
- Depth: 0
- Position: (200, 750)
- Owner: `player`
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## door-strut-house-1-1

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-house`
  - Name: `door-strut-house-1-1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 32
    - Length: 48
- Mass: -1
- Count: 1
- **State:**
- Layer: `0`
- Depth: 1
- Height: 940
- Position: (232, 868)
- Door Out:
- Layer: `brick-house-compose-layer`
- Position: (82, 143)
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## strut-house-interior-1

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `wall-blue`
  - Name: `strut-house-interior-1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 128
    - Length: 96
- Mass: 0
- Cost:
- `wood`: 10
- Hitboxes:
- Position: (6, 17) | Dimensions: w: 116, l: 54
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (0, 0)
- Owner: `player`
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## crate-strut-house-interior-1-1

- **Taxonomy:**
  - Category: `objects`
  - Instance: `crates`
  - ID: `wood-bookshelf`
  - Name: `crate-strut-house-interior-1-1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 54
    - Length: 64
- Mass: 100
- Count: 1
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (2, 71)
- Velocity: (0.0, 0.0)
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## door-strut-house-interior-1-1

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-shadow`
  - Name: `door-strut-house-interior-1-1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 32
    - Length: 48
- Mass: -1
- Count: 1
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (47, 142)
- Door Out:
- Layer: `0`
- Position: (243, 913)
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## strut-strut-house-interior-1-1

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `floor-wood`
  - Name: `strut-strut-house-interior-1-1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 128
    - Length: 96
- Mass: -1
- Cost:
- `wood`: 10
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Height: -100
- Position: (0, 96)
- Owner: `player`
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## passive-strut-house-interior-1-1

- **Taxonomy:**
  - Category: `effects`
  - Instance: `passive`
  - ID: `grandfather-clock`
  - Name: `passive-strut-house-interior-1-1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.IterableFrame'>`
- **Properties:**
- Dimensions:
    - Width: 32
    - Length: 96
- Mass: 0
- Lifecycle:
- Type: `continuous`
- Delay: 60
- Frequency: 0
- Cooldown: 60
- Persist: False
- Count: 12
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (-4, 30)
- Active: True
- Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 3
    - Tick: 7
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## strut-house-2

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `frame-brick`
  - Name: `strut-house-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 96
    - Length: 190
- Mass: 0
- Cost:
- `stone`: 10
- Hitboxes:
- Position: (10, 20) | Dimensions: w: 76, l: 144
- **State:**
- Layer: `0`
- Depth: 0
- Position: (370, 750)
- Owner: `archaxes`
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## door-strut-house-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-house`
  - Name: `door-strut-house-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 32
    - Length: 48
- Mass: -1
- Count: 1
- **State:**
- Layer: `0`
- Depth: 1
- Height: 940
- Position: (402, 868)
- Door Out:
- Layer: `brick-house-compose-layer`
- Position: (82, 143)
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## strut-house-interior-2

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `wall-blue`
  - Name: `strut-house-interior-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 128
    - Length: 96
- Mass: 0
- Cost:
- `wood`: 10
- Hitboxes:
- Position: (6, 17) | Dimensions: w: 116, l: 54
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (0, 0)
- Owner: `archaxes`
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## crate-strut-house-interior-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `crates`
  - ID: `wood-bookshelf`
  - Name: `crate-strut-house-interior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 54
    - Length: 64
- Mass: 100
- Count: 1
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (56, 71)
- Velocity: (0.0, 0.0)
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## door-strut-house-interior-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-shadow`
  - Name: `door-strut-house-interior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 32
    - Length: 48
- Mass: -1
- Count: 1
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (47, 142)
- Door Out:
- Layer: `0`
- Position: (413, 913)
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## strut-strut-house-interior-2-2

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `floor-wood`
  - Name: `strut-strut-house-interior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
- Dimensions:
    - Width: 128
    - Length: 96
- Mass: -1
- Cost:
- `wood`: 10
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Height: -100
- Position: (0, 96)
- Owner: `archaxes`
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## passive-strut-house-interior-2-2

- **Taxonomy:**
  - Category: `effects`
  - Instance: `passive`
  - ID: `grandfather-clock`
  - Name: `passive-strut-house-interior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.IterableFrame'>`
- **Properties:**
- Dimensions:
    - Width: 32
    - Length: 96
- Mass: 0
- Lifecycle:
- Type: `continuous`
- Delay: 60
- Frequency: 0
- Cooldown: 60
- Persist: False
- Count: 12
- **State:**
- Layer: `brick-house-compose-layer`
- Depth: 0
- Position: (-4, 30)
- Active: True
- Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 3
    - Tick: 7
- Mutators:
- Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

## Layer: brick-house-compose-layer

* Position: (0, 0) | Dimensions: w: 1, l: 192
* Position: (128, 0) | Dimensions: w: 1, l: 192
* Position: (0, 0) | Dimensions: w: 128, l: 1
* Position: (0, 192) | Dimensions: w: 128, l: 1

```

**Proposed Remeditation**

Decomposer needs to add a unique identifier to each "pseudo" layer in a composition.