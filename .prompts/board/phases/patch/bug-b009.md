##### Bug B009: Irregular Composition Behavior
!!! note
    State dumps are snapshots of the game state at the *end* of the session.

**STATUS**: CLOSED
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

##### Root Cause Analysis

The black screen occurs because `Board.size()` computes layer dimensions strictly from `AssetCategories.TILES.value`. Because `brick-house-compose-layer` contains no tiles (its floor and walls are instantiated under `AssetCategories.CRAFTS.value`), `Board.size()` evaluates to `(w=0, l=0)`. `Screen` clamps `self.boardsize` to `self.screensize`, forcing `max_x = 0` and `max_y = 0` inside `Screen.camera()`. This pins the camera to `(0, 0)` regardless of player position.

When the composition was deployed at `y=150`, the interior assets happened to lie within the camera viewport $[0, \text{screensize.l}]$, creating the illusion that the camera was centered. Shifting the composition to `y=750` placed all interior assets at $y \ge 750$. Because the camera remained clamped to `(0, 0)`, every asset failed the camera culling check in `Screen.draw()` ($dy \le \text{pov.y} + \text{screensize.l}$ evaluated to $750 \le 600 \to \text{False}$), rendering an empty black screen behind the HUD.

*Hypothesis Under Evaluation:*

> *"The compose layer does not have any background tiles to allow the camera to be centered."*

The hypothesis accurately identifies that `Board.size()` depends on tiles, but the proposed remediation—introducing background tiles to the composition layer—is **ineffectual and architecturally flawed**:

1. **Brittle and Incomplete Bounds:** If a minimal patch of tiles matching the floor dimensions ($128 \times 96$) is added to the composition pseudo-state, `Decomposer` offsets them to $(150, 750)$, yielding a maximum extent of $y = 750 + 96 = 846$. In an $800 \times 600$ viewport, `max_y` becomes $846 - 600 = 246$. The camera clamp still cannot exceed $y = 246$, meaning the viewport spans $[246, 846]$. The player spawn at $(232, 893)$ and the door at $(197, 892)$ fall past $846$ and remain culled.
2. **Violates Architectural Separation:** Compositions are abstract macro containers. Architectural framing and flooring are designed to be modeled as `crafts.struts` (`wall-blue`, `floor-wood`). Requiring every composition layer to configure dummy tiles to satisfy board dimensions breaks domain boundaries and pollutes the configuration schema with defensive workarounds.
3. **Fails on Arbitrary Tileless Layers:** Any layer designed without tiles (e.g., floating platforms, interior rooms rendered via decals, subterranean voids) would reproduce this exact bug.

Implementing the hypothesis via data-level tile additions will not resolve the defect.

**1. Spatial Superposition in `Decomposer`**

In `app.services.generators.game.decomposer`:

```python
pseudo_pos = kwargs.get('position')
if pseudo_pos:
    kwargs['position'] = Position(
        x=parent_context['position'].x + pseudo_pos.x,
        y=parent_context['position'].y + pseudo_pos.y
    )

```

`Decomposer` calculates absolute coordinates as $\text{Parent Absolute Position} + \text{Child Pseudo Position}$.

* At root `(150, 150)`: `strut-house-interior-1` sits at $(150, 150)$, `floor-wood` at $(150, 246)$, the exit door at $(197, 292)$, and the player spawns at $(232, 293)$.
* At root `(150, 750)`: `strut-house-interior-1` sits at $(150, 750)$, `floor-wood` at $(150, 846)$, the exit door at $(197, 892)$, and the player spawns at $(232, 893)$.

This relative placement is compliant with the Composition specification in `03-compositions.md` to prevent multiple composition instances from overlapping on shared layers.

**2. Dimension Collapse in `Board.size()`**

In `app.game.board`:

```python
def size(self, layer=None) -> List[Dimensions]:
    layers = [ layer ] if layer is not None else self.layers()
    layer_sizes = []

    for layer in layers:
        tiles = self.categories(AssetCategories.TILES.value, layer)
        w = max([ tile.state.position.x + tile.state.multiple.nx * tile.properties.dimensions.w 
                for tile in tiles ], default = 0)
        l = max([tile.state.position.y + tile.state.multiple.ny * tile.properties.dimensions.l
                for tile in tiles], default = 0)
        layer_sizes.append(Dimensions(w=w, l=l))
    return layer_sizes

```

Because `self.categories(AssetCategories.TILES.value, 'brick-house-compose-layer')` returns `[]`, `Board.size()` defaults to `Dimensions(w=0, l=0)`.

**3. Viewport Clamping and Camera Locking in `Screen`**

In `app.game.screen`:

```python
self.boardsize = Dimensions(
    w=max(boardsize.w, screensize.w),
    l=max(boardsize.l, screensize.l)
)
```

When `boardsize` is `(0, 0)`, `self.boardsize` equals `self.screensize`. In `camera()`:

```python
max_x = max(0, self.boardsize.w - self.screensize.w)  # 0
max_y = max(0, self.boardsize.l - self.screensize.l)  # 0

cam_x = max(0, min(cam_x, max_x))  # Clamped to 0
cam_y = max(0, min(cam_y, max_y))  # Clamped to 0
```

The camera cannot translate, remaining frozen at `(0, 0)`.

**4. Frustum Culling**

In `Screen.draw()`:

```python
if (dx + dw >= pov.x and dx <= pov.x + self.screensize.w and
    dy + dl >= pov.y and dy <= pov.y + self.screensize.l):
    active_assets.append((tex, sx, sy, sw, sl, dx, dy, dw, dl))
```

With `pov.y = 0` and standard viewport heights (e.g., 600px):

* In Step 2 (`y=150`): Maximum asset bounds were $y = 340 \le 600$, allowing all items to pass culling.
* In Step 4 (`y=750`): Minimum asset bounds start at $y = 750 > 600$. All assets fail $dy \le \text{pov.y} + \text{screensize.l}$ and are culled. Because `is_opaque = len(tiles) == 0` evaluates to `True`, the engine renders the cleared black background canvas with HUD overlays.

##### Remediation

**1. Update `Board.size()`**

Modify `Board.size()` in `src/app/game/board.py` to calculate layer boundaries across all physical assets on the layer (`tiles` scaled by `multiple`, alongside any entity declaring `dimensions`):

```python
    def size(self, layer=None) -> List[Dimensions]:
        """
        Calculates the spatial extent of the Board by layer. 
        Evaluates tiles, objects, crafts, and sheets to support tileless composition layers.
        """
        layers = [layer] if layer is not None else self.layers()
        layer_sizes = []

        for l in layers:
            layer_assets = self.assets(l)
            max_w = 0
            max_l = 0

            for asset in layer_assets:
                if asset.category == AssetCategories.TILES.value:
                    ext_w = int(asset.state.position.x) + (asset.state.multiple.nx * asset.properties.dimensions.w)
                    ext_l = int(asset.state.position.y) + (asset.state.multiple.ny * asset.properties.dimensions.l)
                elif asset.dimensions:
                    ext_w = int(asset.state.position.x) + asset.dimensions.w
                    ext_l = int(asset.state.position.y) + asset.dimensions.l
                else:
                    continue

                if ext_w > max_w:
                    max_w = ext_w
                if ext_l > max_l:
                    max_l = ext_l

            layer_sizes.append(Dimensions(w=max_w, l=max_l))

        return layer_sizes

```

**2. Correct Craft Scope in `Perimeter.extract()`**

In `src/app/services/generators/game/perimeter.py`, `crafts` queries all board crafts instead of filtering by layer, injecting extraneous boundaries from Layer 0 into composition layers:

```python
        # 2. Map Game Space
        objects = board.categories(AssetCategories.OBJECTS.value, layer)
        crafts = board.categories(AssetCategories.CRAFTS.value, layer)
        space = objects + crafts
        for obj in space:
            x1 = int(obj.state.position.x)
            y1 = int(obj.state.position.y)
            rects.append((x1, y1, x1 + obj.dimensions.w, y1 + obj.dimensions.l))
```

##### Verification

With changes Composition is visible on screen at updated position (150, 750). However, it is not centered on the screen, instead rendered below the HUD. Ideally, what should occur for Compositions is when they turn out to be smaller than the screen dimensions (480 x 480 = screen dimensions, in this case), they should be appear centered on the screen. Determine the changes that would be required to ensure Compositions behave this way.

**Followup**

It seems that Sprite positions in the state have to be specified in absolute coordinates when the  Sprite is in another layer, e.g.,

```yaml
sheets:
  sprites: 
    - id: jasilynn
      name: evil-empress-jasilynn
      layer: brick-house-compose-layer
      depth: 0
      position:
        x: 175
        y: 200
      meters:
        health: 
          current: 50
          maximum: 100
        magic: 
          current: 100
          maximum: 100
      character:
        strength: 5
        defense: 5
        speed: 50
        impulse: 25
      mutators:
        parameters:
          fear:
            radius: 100
            limit: 0.50
            enemy: 5
          vision:
            radius: 150
          action:
            radius: 25
          squeeze: 
            radius: 10
      psyche:
        dialogue: greeting
        expression: null
        motivation: conquest
        persona: empress-jasilynn
      intention: find
      goal:
        name: player
        category: subject
        layer: '0'
        position:
          x: 100
          y: 200
      memory:
        goals:
          player:
            name: player
            category: subject
            layer: '0'
            position:
              x: 100
              y: 200
        prices: null
        property: null
        relationships: 
          player: friend
        rumors: null
        sprites: 
          player:
            x: 100
            y: 200
      inventory: 
        pouch: null
        pack: null
        equipment:
          armor: null
          tool: null
          utility: null
          weapon: shortsword
          shield: null
        wallet: 0
```

The sprite is not visible. But if position is updated to (175, 775), the sprite can be seen. This is not a dealbreaker, although it would be preferrable for coordinates to map to origin of the layer in which they are specified. The current system could become confusing if there are multiple layers, i.e. a debugging nightmare.

**State Dump**

```markdown
# Ontology: State Dump

- **Board:** world-01
- **Timestamp:** 20260921_121100

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
    - Frame: 6
    - Tick: 31

... irrelevant assets elided ...

## evil-empress-jasilynn

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `sprites`
  - ID: `jasilynn`
  - Name: `evil-empress-jasilynn`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.SpriteAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SpriteFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 64
    - Length: 64
  - Mass: 25
  - Stack:
    - `human-female-ivory`
    - `torso-dress-red`
    - `hair-long-black`
    - `head-crown-gold`
    - `feet-boots-black`
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
  - Layer: `0`
  - Depth: 0
  - Position: (28, 887)
  - Velocity: (0.0, 0.0)
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 0
  - Character:
    - Strength: 5
    - Defense: 5
    - Speed: 50
    - Impulse: 25
  - Meters:
    - Health: 50 / 100
    - Magic: 100 / 100
  - Inventory:
    - Wallet: 0
    - Equipment:
      - Weapon: `shortsword`
  - Goal:
    - Name: `player`
    - Category: `subject`
    - Layer: `0`
    - Position: (21, 911)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: True
    - Parameters:
      - Fear:
        - Radius: 100
        - Limit: 0.5
        - Enemy: 5
      - Vision:
        - Radius: 150
      - Action:
        - Radius: 25
  - Memory:
    - Sprites:
      - `player`: (21, 911)
    - Doors:
      - `door-strut-house-interior-1-1`: `0`
    - Relationships:
      - `player`: `friend`
  - Psyche:
    - Persona: `empress-jasilynn`
    - Motivation: `conquest`
    - Dialogue: `greeting`
    - Expression:
      - Icon: `loquacity`
      - TTL: 26
      - Offset: (32, -14)
  - Intention: `idle`

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
  - Layer: `0`
  - Depth: 0
  - Position: (21, 911)
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
    - Position: (21, 911)
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
* Position: (278, 750) | Dimensions: w: 1, l: 192
* Position: (150, 750) | Dimensions: w: 128, l: 1
* Position: (150, 942) | Dimensions: w: 128, l: 1
```

##### Root Cause Analysis

The two issuesobserved are interconnected symptoms stemming from the same architectural assumption: `Decomposer` currently propagates the root strut's Layer 0 position across layer boundaries, and `Screen` clamps viewport camera coordinates to $[0, \text{boardsize} - \text{screensize}]$.

**1. Why Sprites Required Absolute Layer 0 Coordinates (Part 2)**

In `app.services.generators.game.decomposer`:

```python
pseudo_pos = kwargs.get('position')
if pseudo_pos:
    kwargs['position'] = Position(
        x=parent_context['position'].x + pseudo_pos.x,
        y=parent_context['position'].y + pseudo_pos.y
    )

```

When unpacking `comp_config.branches`, `parent_context` is `root_context` (Layer 0, position `(150, 750)`). Even though `branch.strut` explicitly declares `layer: brick-house-compose-layer` and `position: (0, 0)`, `_hydrate_state()` blindly adds `parent_context['position']` to `pseudo_pos`.

Consequently:

* `strut-house-interior-1` is deployed at `(150, 750)` on `brick-house-compose-layer`.
* All interior child assets (flooring, furniture, doors) are offset relative to `(150, 750)`.
* The entrance door on Layer 0 computes its `out` coordinate as `root_context['position'] + pseudo_out = (150, 750) + (82, 143) = (232, 893)`.
* When Jasilynn is declared in `state.yaml` on `brick-house-compose-layer` at `(175, 200)`, she is placed at literal coordinate `(175, 200)`. Because the house interior begins at $y = 750$, she sits $550\text{ px}$ above the room in the void and remains outside the camera's culling frustum. Shifting her to $(175, 775)$ placed her at $(175, 750 + 25)$, which falls inside the shifted house.

**2. Why the Composition Rendered Off-Center Below the HUD (Part 1)**

Two systems prevent the composition from centering:

1. **Inflated Layer Extents:** Because the interior was shifted to $(150, 750)$, `Board.size('brick-house-compose-layer')` evaluates to $w = 278, l = 942$ instead of $w = 128, l = 192$. Because $l = 942 > 480$, the engine treats the layer as taller than the screen, locking `cam_y` to the bottom clamp:

$$
\text{max\_y} = 942 - 480 = 462
$$

The player at $y = 893$ is drawn at $dy = 893 - 462 = 431$ (near the bottom edge).

2. **Camera Zero-Clamping:** In `Screen.camera()`:
```python
max_x = max(0, self.boardsize.w - self.screensize.w)
max_y = max(0, self.boardsize.l - self.screensize.l)

cam_x = max(0, min(cam_x, max_x))
cam_y = max(0, min(cam_y, max_y))
```

When an axis dimension is smaller than the screen ($w < \text{screensize.w}$), `max_x` evaluates to `0`, clamping `cam_x` strictly to `0`. An asset at $x = 0$ is drawn at $dx - \text{cam\_x} = 0 - 0 = 0$ (the top-left corner under the HUD) rather than receiving a negative camera offset to center it within the viewport.

3. **Global Extent Leak in Builder:** In `src/app/services/orchestration/builder.py`:

```python
max_width = max((self.board.size(layer)[0].w for layer in self.board.layers()), default=0)
max_length = max((self.board.size(layer)[0].l for layer in self.board.layers()), default=0)
```

The generator expression shadows the outer loop variable `layer`, assigning the dimensions of the largest board layer (Layer 0, $3200 \times 3200$) to every screen instance.

##### Remediation

**Step 1: Decouple Layer Coordinates in `Decomposer`**

Update `src/app/services/generators/game/decomposer.py` so that assets transitioning to a new layer use local coordinates relative to $(0, 0)$. Teleport destinations (`out`) check destination layer parity against `root_context['layer']`:

```python
    def _hydrate_state(self, 
        state_obj: AssetState, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        inst_key: str, 
        is_strut: bool = False
    ) -> AssetState:
        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name, None)
            kwargs[f.name] = self._resolve_bind(val, root_context, parent_context)
        
        if 'layer' in kwargs and not kwargs['layer']:
            kwargs['layer'] = parent_context['layer']
        if 'owner' in kwargs and not kwargs['owner']:
            kwargs['owner'] = parent_context['owner']

        # Layer Transition Boundary: If moving to an independent layer, reset local origin
        is_cross_layer = kwargs.get('layer') != parent_context.get('layer')
        base_pos = Position(0, 0) if is_cross_layer else parent_context['position']

        pseudo_pos = kwargs.get('position')
        if pseudo_pos:
            kwargs['position'] = Position(
                x=base_pos.x + pseudo_pos.x,
                y=base_pos.y + pseudo_pos.y
            )
        else:
            kwargs['position'] = Position(base_pos.x, base_pos.y)

        # Teleport destination coordinate mapping
        pseudo_out = kwargs.get('out')
        if pseudo_out:
            outlayer = kwargs.get('outlayer')
            # If returning to root layer, offset by deployed root position
            if outlayer == root_context.get('layer'):
                kwargs['out'] = Position(
                    x=root_context['position'].x + pseudo_out.x,
                    y=root_context['position'].y + pseudo_out.y
                )
            else:
                # Target is an interior layer; coordinates are local to that layer
                kwargs['out'] = Position(pseudo_out.x, pseudo_out.y)

        base_inst = inst_key[:-1] if inst_key.endswith('s') else inst_key
        
        if is_strut:
            b_name = kwargs.get('name') or root_context['name']
            kwargs['name'] = '-'.join([base_inst, b_name, str(inc)])
        else:
            kwargs['name'] = '-'.join([base_inst, parent_context['name'], str(inc)])
        
        return type(state_obj)(**kwargs)

```
With this change, `strut-house-interior-1` sits at $(0, 0)$, `floor-wood` sits at $(0, 96)$, and the entire composition layer spans $(0, 0) \to (128, 192)$. Jasilynn can now be specified at $(60, 100)$ directly inside the room.

**Step 2: Layer-Specific Sizing in `Builder`**

Fix the generator variable shadowing in `src/app/services/orchestration/builder.py` so each layer receives its own dimensions:

```python
        else:
            self.screens = {}
            for layer in self.board.layers():
                layer_size = self.board.size(layer)[0]
                self.screens[layer] = Screen(
                    self.context.screensize, 
                    Dimensions(layer_size.w, layer_size.l),
                    self.board.categories(AssetCategories.TILES.value, layer),
                    self.registry
                )

```

**Step 3: Screen Centering for Sub-Viewport Layers**

Modify `src/app/game/screen.py` to preserve the true board dimensions on `self.boardsize`, using the hardware clamp only for GPU canvas allocations. In `camera()`, apply negative coordinate shifts when layer bounds are smaller than viewport bounds:

```python
class Screen:
    screensize: Dimensions
    boardsize: Dimensions
    bg_canvas: TexturePtr
    fg_canvas: TexturePtr
    registry: Registry

    def __init__(self, 
        screensize: Dimensions,
        boardsize: Dimensions,
        tiles: List[Asset],
        registry: Registry
    ):
        self.screensize = screensize
        self.boardsize = boardsize
        self.registry = registry

        # Hardware Target Minimum: Texture size must not drop below viewport bounds
        canvas_w = max(boardsize.w, screensize.w)
        canvas_l = max(boardsize.l, screensize.l)

        is_opaque = len(tiles) == 0

        self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
        self.fg_canvas = render.canvas(canvas_w, canvas_l)
        
        back_tiles, fore_tiles = self._prerender(tiles)
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)

    def camera(self, 
        focus: Position, 
        dim: Dimensions
    ) -> Position:
        """
        Calculates camera viewport coordinates. 
        Centers layers smaller than viewport dimensions via negative offsets.
        """
        if self.boardsize.w < self.screensize.w:
            cam_x = -((self.screensize.w - self.boardsize.w) // 2)
        else:
            cam_x = focus.x + (dim.w // 2) - (self.screensize.w // 2)
            max_x = self.boardsize.w - self.screensize.w
            cam_x = max(0, min(cam_x, max_x))

        if self.boardsize.l < self.screensize.l:
            cam_y = -((self.screensize.l - self.boardsize.l) // 2)
        else:
            cam_y = focus.y + (dim.l // 2) - (self.screensize.l // 2)
            max_y = self.boardsize.l - self.screensize.l
            cam_y = max(0, min(cam_y, max_y))

        return Position(x=cam_x, y=cam_y)

    def rebake(self, 
        tiles: List[Asset], 
        boardsize: Dimensions,
        screensize: Dimensions = None
    ) -> None:
        if self.bg_canvas:
            render.destroy(self.bg_canvas)
        if self.fg_canvas:
            render.destroy(self.fg_canvas)

        if screensize:
            self.screensize = screensize

        self.boardsize = boardsize
        canvas_w = max(boardsize.w, self.screensize.w)
        canvas_l = max(boardsize.l, self.screensize.l)

        is_opaque = len(tiles) == 0

        self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
        self.fg_canvas = render.canvas(canvas_w, canvas_l)

        back_tiles, fore_tiles = self._prerender(tiles)
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)

```

**Step 4: Guard SDL Against Negative Source Rectangles**

When `cam_x < 0` or `cam_y < 0`, passing negative coordinates to `SDL_RenderCopy` for the background canvas causes SDL2 to return an invalid source rectangle error.

Update `render()` in `src/libs/graphics/render.pyx` to offset destination coordinates and clamp source rectangles:

```cython
def render(
    TexturePtr background, 
    TexturePtr foreground, 
    list assets, 
    int cam_x, 
    int cam_y, 
    int screen_w, 
    int screen_l, 
    TexturePtr target=None
):
    if target is not None:
        SDL_SetRenderTarget(_renderer, target.ptr)

    cdef SDL_Rect c_src, c_dst, bg_src, bg_dst
    cdef TexturePtr tex_wrapper
    cdef int sx, sy, sw, sl, dx, dy, dw, dl

    if background is not None:
        bg_src.x = cam_x if cam_x >= 0 else 0
        bg_src.y = cam_y if cam_y >= 0 else 0
        bg_dst.x = 0 if cam_x >= 0 else -cam_x
        bg_dst.y = 0 if cam_y >= 0 else -cam_y
        bg_src.w = min(screen_w - bg_dst.x, background.w - bg_src.x)
        bg_src.h = min(screen_l - bg_dst.y, background.l - bg_src.y)
        bg_dst.w = bg_src.w
        bg_dst.h = bg_src.h

        SDL_RenderCopy(_renderer, background.ptr, &bg_src, &bg_dst)

    for asset in assets:
        tex_wrapper, sx, sy, sw, sl, dx, dy, dw, dl = asset
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sl
        c_dst.x = dx - cam_x
        c_dst.y = dy - cam_y
        c_dst.w = dw
        c_dst.h = dl
        SDL_RenderCopy(_renderer, tex_wrapper.ptr, &c_src, &c_dst)

    if foreground is not None:
        bg_src.x = cam_x if cam_x >= 0 else 0
        bg_src.y = cam_y if cam_y >= 0 else 0
        bg_dst.x = 0 if cam_x >= 0 else -cam_x
        bg_dst.y = 0 if cam_y >= 0 else -cam_y
        bg_src.w = min(screen_w - bg_dst.x, foreground.w - bg_src.x)
        bg_src.h = min(screen_l - bg_dst.y, foreground.l - bg_src.y)
        bg_dst.w = bg_src.w
        bg_dst.h = bg_src.h

        SDL_RenderCopy(_renderer, foreground.ptr, &bg_src, &bg_dst)

    if target is not None:
        SDL_SetRenderTarget(_renderer, NULL)

```

For a $128 \times 192$ interior in a $480 \times 480$ viewport:

* $\text{cam\_x} = -((480 - 128) // 2) = -176$
* $\text{cam\_y} = -((480 - 192) // 2) = -144$
* The house origin $(0, 0)$ paints at screen coordinate $(176, 144)$, leaving $176\text{ px}$ side margins and $144\text{ px}$ top/bottom margins, clearing the HUD completely.


#### Draft: Cross-Layer Spatial Decoupling & Hierarchical Bindings

* **Page**: `docs/03-compositions.md`
* **Heading**: `Pseudo State`

##### Drift

The section claims child coordinates always translate linearly from the root strut position across all layers (`house-interior` at `(110, 110)` and `door-frame` at `(130, 130)`). Following the B009 patch, cross-layer transitions decouple from parent coordinates and anchor to local `(0, 0)`. Additionally, `out` teleport coordinate translation and `bind(parent.*)` resolution are omitted.

##### Update

```markdown
### Pseudo State

The state files specify Compositions to deploy. The game converts these Compositions into in-game Assets that belong to the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during [bootstrapping](./10-architecture.md#initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#board) state dynamically.

Components of Compositions have a Pseudo State. During the [application bootstrap](./10-architecture.md#initialization), each component's Pseudo State is hydrated into an actual Asset State and injected into the Board.

For example, consider the following Composition configuration:

```yaml
compositions:
    brick-house:
        root:
            strut: 
                id: frame-brick
                name: house-exterior
            components:
                objects:
                    doors:
                        -   id: mansion
                            name: house-door
                            depth: 1
                            outlayer: 'compose-layer'
                            position:
                                x: 20
                                y: 20
                            out:
                                x: 10
                                y: 10
        branches:
            -   strut: 
                    id: wall-blue
                    name: house-interior
                    owner: bind(root.owner)
                    layer: 'compose-layer'
                    position:
                        x: 10
                        y: 10
                components:
                    objects:
                        doors:
                            -   id: door-shadow
                                name: door-frame
                                layer: 'compose-layer'
                                depth: 1
                                outlayer: bind(root.layer)
                                position:
                                    x: 20
                                    y: 20
                                out:
                                    x: 10
                                    y: 10

```

!!! note
`components` is an [Asset State](https://www.google.com/search?q=./00-overview.md%2523state&utm_source=gemini) schema, identical to a state file.

!!! note
Doors utilize the `depth` attribute to ensure they render on top of their parent Struts.

This configures a `brick-house` composed of two Struts on separate [Layers](https://www.google.com/search?q=./00-overview.md%2523layers&utm_source=gemini), each containing a Door linked via a two-way traversal circuit (`'compose-layer' <-> bind(root.layer)`).

The root Strut (`brick-house.root`) does not specify a static `position` or `layer` in configuration; these are injected by the state file during deployment. Component Assets and branching Struts define Pseudo States relative to their hierarchical contexts. Deploying this Composition via state configuration:

```yaml
compositions:
    - id: brick-house
      name: player-home
      layer: '0'
      owner: player
      position:
        x: 100
        y: 100

```

Hydration uses the following rules:

* **Layer-Bounded Coordinate Translation:**
* **Same Layer:** `Child Position = Parent Position + Child Pseudo Position`.
* **Cross Layer:** When an entity defines a `layer` differing from its immediate parent, coordinates decouple from the parent's world position and anchor to layer origin `(0, 0)`: `Child Position = (0, 0) + Child Pseudo Position`.
* *Root Component (`house-door` on `'0'`):* `(100, 100) + (20, 20) = (120, 120)`
* *Branching Strut (`house-interior` on `'compose-layer'`):* `(0, 0) + (10, 10) = (10, 10)`
* *Branch Component (`door-frame` on `'compose-layer'`):* `(10, 10) + (20, 20) = (30, 30)`


* **Teleport `out` Resolution:**
* **Returning to Root Layer (`outlayer == root.layer`):** Teleport exit positions offset by the deployed root position: `Child Out = Root Position + Child Pseudo Out`. (`door-frame.out` evaluates to `(100, 100) + (10, 10) = (110, 110)`).
* **Entering Interior Layers (`outlayer != root.layer`):** Teleport exit positions remain local to the destination layer's coordinate plane: `Child Out = Child Pseudo Out`. (`house-door.out` evaluates to `(10, 10)`).


* **Contextual Bindings:** Component Pseudo States can bind attributes to either their immediate parent or the root strut context via regex evaluation:
* `bind(parent.)`: Queries the immediate parent node context (e.g., `owner: bind(parent.owner)` or `height: bind(parent.height)`).
* `bind(root.)` or `bind()`: Queries the root deployment context (e.g., `outlayer: bind(root.layer)`).



Unique entity names are generated using monotonic increments: `--` (e.g., `door-strut-house-interior-1-1`).

```

```

---

#### Draft: Decomposer Algorithm Pipeline Alignment

* **Page**: `docs/03-compositions.md`
* **Heading**: `Decomposer`

##### Drift

Steps 2 and 3 in the `Decomposition` breakdown do not document cross-layer coordinate resets, target-aware `out` resolution, or `parent.*` context lookups.

##### Update

```markdown
### Decomposition 

**1. Root Hydration (The Context)**

* **Action:** Instantiate the root Strut using the exact deployment state provided by the `Board` (e.g., `position: (100, 100)`, `layer: '0'`).
* **Role:** This instantiated state becomes the "Root Context." It provides base coordinates for root components, defines the return target for interior exit doors, and seeds the dictionary payload for `bind(root.*)` evaluations.

**2. State Superposition (Parent to Child)**

For every child node (components and branching Struts), apply the following logic:

* **Layer Parity Check:** Compare the child's resolved `layer` against `parent_context['layer']`.
* **Coordinate Translation:**
    * If layers match: `Child Absolute Position = Parent Absolute Position + Child Pseudo Position`.
    * If layers differ: `Child Absolute Position = (0, 0) + Child Pseudo Position`.
* **Teleport Out Translation:** If the asset defines an `out` coordinate:
    * If `outlayer == root_context['layer']`: `Child Absolute Out = Root Absolute Position + Child Pseudo Out`.
    * Otherwise: `Child Absolute Out = Child Pseudo Out`.
* **Attribute Inheritance:** If a child's PseudoState omits `owner` or `layer`, it inherits the value from its immediate parent context.
* **Context Propagation:** Calculate the physical bottom edge (`node_height = pos.y + dim.l`) and record `position`, `layer`, `owner`, `name`, and `height` as the active parent context for subsequent child traversals.

**3. Late-Binding Resolution**

* **Action:** Scan all string values for `bind\(([^)]+)\)`.
* **Evaluation:**
    * Matches for `bind(parent.)` query `parent_context`.
    * Matches for `bind(root.)` or `bind()` query `root_context`.
* **Override:** Substitute the target string with the resolved context value prior to ECS component instantiation.

**4. Unique Nomenclature Generation**

* **Action:** Apply a monotonic incrementor across unpacked nodes to guarantee uniqueness:
    * Root and Branch Struts: `--`
    * Components: `--`

**5. Flattening**

* **Action:** Append each resolved, named `Asset` instance into a flat 1D list returned to the caller (`Orchestrator` or `Cradle`).

```