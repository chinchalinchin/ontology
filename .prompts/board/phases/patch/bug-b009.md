##### Bug B009: Irregular Composition Behavior
!!! note
    State dumps are snapshots of the game state at the *end* of the session.

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

Irregular camera behavior when Composition state is altered.

**Steps to Replicate** 

1. Composition is configured:

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
            crate:
              - id: bookshelf
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

2. Composition starts in this state:

```yaml
compositions:
  - id: brick-house
    name: door-test
    layer: '0'
    owner: player
    position:
      x: 150
      y: 150
```

Player enters `brick-house` door. 

3. Game is manually cancelled and state is dumped,

```markdown
# Ontology: State Dump

- **Board:** world-01
- **Timestamp:** 20260921_110304


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
  - Position: (150, 150)
  - Owner: `player`

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
  - Height: 340
  - Position: (182, 268)
  - Door Out:
    - Layer: `brick-house-compose-layer`
    - Position: (232, 293)

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
  - Position: (150, 150)
  - Owner: `player`

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
  - Position: (197, 292)
  - Door Out:
    - Layer: `0`
    - Position: (193, 313)

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
  - Position: (150, 246)
  - Owner: `player`

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
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 12
- **State:**
  - Layer: `brick-house-compose-layer`
  - Depth: 0
  - Position: (151, 180)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 7
    - Tick: 5

... irrelevant assets elided ...

## the-steppe

- **Taxonomy:**
  - Category: `tiles`
  - Instance: `back`
  - ID: `grass`
  - Name: `the-steppe`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Friction: 100.0
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (0, 0)
  - Multiple:
    - nx: 100
    - ny: 100

... irelevant assets elided ...

## player

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `players`
  - ID: `player`
  - Name: `player`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.SpriteAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SpriteFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 64
    - Length: 64
  - Mass: 7
  - Stack:
    - `human-male-ivory`
    - `feet-boots-black`
    - `legs-robe-black`
    - `torso-shirt-male-black`
    - `toros-cape-black`
    - `head-glasses`
    - `head-beard-white`
    - `hair-curls-white`
    - `head-wizard-hat-moon`
  - Hitboxes:
    - Position: (23, 34) | Dimensions: w: 18, l: 15
  - Actions:
    - `cast`:
      - Count: 7
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 0
        - `Directions.LEFT`: row 1
        - `Directions.DOWN`: row 2
        - `Directions.RIGHT`: row 3
    - `thrust`:
      - Count: 8
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 4
        - `Directions.LEFT`: row 5
        - `Directions.DOWN`: row 6
        - `Directions.RIGHT`: row 7
    - `walk`:
      - Count: 9
      - Delay: 3
      - Directions:
        - `Directions.UP`: row 8
        - `Directions.LEFT`: row 9
        - `Directions.DOWN`: row 10
        - `Directions.RIGHT`: row 11
    - `slash`:
      - Count: 6
      - Delay: 5
      - Directions:
        - `Directions.UP`: row 12
        - `Directions.LEFT`: row 13
        - `Directions.DOWN`: row 14
        - `Directions.RIGHT`: row 15
    - `shoot`:
      - Count: 13
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 16
        - `Directions.LEFT`: row 17
        - `Directions.DOWN`: row 18
        - `Directions.RIGHT`: row 19
    - `die`:
      - Count: 6
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 20
- **State:**
  - Layer: `brick-house-compose-layer`
  - Depth: 0
  - Position: (162, 245)
  - Velocity: (0.0, 0.0)
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 0
  - Character:
    - Strength: 5
    - Defense: 5
    - Speed: 100
    - Impulse: 25
  - Meters:
    - Health: 50 / 100
    - Magic: 100 / 100
  - Inventory:
    - Wallet: 0
    - Equipment:
      - Weapon: `shortsword`
      - Shield: `buckler`
  - Goal:
    - Position: (162, 245)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
    - Parameters:
      - Fear:
        - Radius: 30
        - Limit: 0.5
        - Enemy: 5
      - Vision:
        - Radius: 30
      - Action:
        - Radius: 30
  - Intention: `idle`

---

# Perimeters

## Layer: 0

* Position: (0, 0) | Dimensions: w: 1, l: 3200
* Position: (3200, 0) | Dimensions: w: 1, l: 3200
* Position: (0, 0) | Dimensions: w: 3200, l: 1
* Position: (0, 3200) | Dimensions: w: 3200, l: 1

## Layer: brick-house-compose-layer

* Position: (150, 150) | Dimensions: w: 1, l: 192
* Position: (250, 342) | Dimensions: w: 1, l: 41
* Position: (278, 150) | Dimensions: w: 1, l: 100
* Position: (472, 250) | Dimensions: w: 1, l: 133
* Position: (150, 150) | Dimensions: w: 128, l: 1
* Position: (278, 250) | Dimensions: w: 194, l: 1
* Position: (150, 342) | Dimensions: w: 100, l: 1
* Position: (250, 383) | Dimensions: w: 222, l: 1
```

Everything behaves as expected; The `brick-house-compose-layer` is rendered on screen. Camera is (apparently) centered on the composition layer. Player is able to move around, collide with layer hitboxes appropriately, etc.

4. Composition state is changed to,

```yaml
compositions:
  - id: brick-house
    name: door-test
    layer: '0'
    owner: player
    position:
      x: 150
      y: 750
```

5. Game is started. Player enters door to `brick-house-compose-layers`; Screen is completely black, except for the HUD. Player is not visible on screen.

6. Game is manually exited and state is dumped,

```markdown
# Ontology: State Dump

- **Board:** world-01
- **Timestamp:** 20260921_110441


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
  - Position: (150, 750)
  - Owner: `player`

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
  - Position: (182, 868)
  - Door Out:
    - Layer: `brick-house-compose-layer`
    - Position: (232, 893)

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
  - Position: (150, 750)
  - Owner: `player`

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
  - Position: (197, 892)
  - Door Out:
    - Layer: `0`
    - Position: (193, 913)

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
  - Position: (150, 846)
  - Owner: `player`

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
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 12
- **State:**
  - Layer: `brick-house-compose-layer`
  - Depth: 0
  - Position: (151, 780)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 8
    - Tick: 39

... irrelevant assets elided


## player

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `players`
  - ID: `player`
  - Name: `player`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.SpriteAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SpriteFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 64
    - Length: 64
  - Mass: 7
  - Stack:
    - `human-male-ivory`
    - `feet-boots-black`
    - `legs-robe-black`
    - `torso-shirt-male-black`
    - `toros-cape-black`
    - `head-glasses`
    - `head-beard-white`
    - `hair-curls-white`
    - `head-wizard-hat-moon`
  - Hitboxes:
    - Position: (23, 34) | Dimensions: w: 18, l: 15
  - Actions:
    - `cast`:
      - Count: 7
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 0
        - `Directions.LEFT`: row 1
        - `Directions.DOWN`: row 2
        - `Directions.RIGHT`: row 3
    - `thrust`:
      - Count: 8
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 4
        - `Directions.LEFT`: row 5
        - `Directions.DOWN`: row 6
        - `Directions.RIGHT`: row 7
    - `walk`:
      - Count: 9
      - Delay: 3
      - Directions:
        - `Directions.UP`: row 8
        - `Directions.LEFT`: row 9
        - `Directions.DOWN`: row 10
        - `Directions.RIGHT`: row 11
    - `slash`:
      - Count: 6
      - Delay: 5
      - Directions:
        - `Directions.UP`: row 12
        - `Directions.LEFT`: row 13
        - `Directions.DOWN`: row 14
        - `Directions.RIGHT`: row 15
    - `shoot`:
      - Count: 13
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 16
        - `Directions.LEFT`: row 17
        - `Directions.DOWN`: row 18
        - `Directions.RIGHT`: row 19
    - `die`:
      - Count: 6
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 20
- **State:**
  - Layer: `brick-house-compose-layer`
  - Depth: 0
  - Position: (232, 893)
  - Velocity: (0.0, 0.0)
  - Animation:
    - Action: `walk`
    - Direction: `up`
    - Frame: 0
    - Tick: 0
  - Character:
    - Strength: 5
    - Defense: 5
    - Speed: 100
    - Impulse: 25
  - Meters:
    - Health: 50 / 100
    - Magic: 100 / 100
  - Inventory:
    - Wallet: 0
    - Equipment:
      - Weapon: `shortsword`
      - Shield: `buckler`
  - Goal:
    - Position: (232, 893)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
    - Parameters:
      - Fear:
        - Radius: 30
        - Limit: 0.5
        - Enemy: 5
      - Vision:
        - Radius: 30
      - Action:
        - Radius: 30
  - Intention: `idle`

---

# Perimeters

## Layer: 0

* Position: (0, 0) | Dimensions: w: 1, l: 3200
* Position: (3200, 0) | Dimensions: w: 1, l: 3200
* Position: (0, 0) | Dimensions: w: 3200, l: 1
* Position: (0, 3200) | Dimensions: w: 3200, l: 1

## Layer: brick-house-compose-layer

* Position: (150, 750) | Dimensions: w: 1, l: 192
* Position: (250, 250) | Dimensions: w: 1, l: 133
* Position: (278, 750) | Dimensions: w: 1, l: 192
* Position: (472, 250) | Dimensions: w: 1, l: 133
* Position: (250, 250) | Dimensions: w: 222, l: 1
* Position: (250, 383) | Dimensions: w: 222, l: 1
* Position: (150, 750) | Dimensions: w: 128, l: 1
* Position: (150, 942) | Dimensions: w: 128, l: 1

```


**Hypothesis**

The compose layer does not have any background tiles to allow the camera to be centered. 

**Proposed Remeditation**

{{ remediation }}

{% endfor %}