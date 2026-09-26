##### Bug B005 - Speak Regression

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Context**

`layer` was recently added to the `Goal` model to support cross-layer Goal management (e.g. Sprite interacting with door to get to a SUBJECT it is seeking on another layer). In addition, the logic in CognitionMechanics has been modified since the `speak` Intention was originally implemented. 

**Description**

Sprites no longer transition into the `speak` Intention from the `find` Intention.

**Steps to Replicate** 

To illustrate, the following logs were taken from the game session. These logs correspond to the following events: 

- game starts. 
- `evil-empress-jasilynn` correctly generates an OBJECT goal for the door in her line of sight and pushes SUBJECT goal onto the `state.memory.goals` stack.
- `evil-empress-jasilynn` correttly transitions into `interact`, then into `idle`,
- `evil-empress-jasilynn` correctly generates a SUBJECT goal for the player from `state.memory.goals`.
- `evil-empress-jasilynn` correctly transitions into `find`. 
- `evil-empress-jasiylnn` does **not** transition into `speak` when within `mutators.parameters.action.radius`.

Initial state:

```yaml
sheets:
  players: 
    - id: player
      name: player
      layer: '0'
      depth: 0
      position:
        x: 10
        y: 80
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
        speed: 100
        impulse: 25
      mutators:
        parameters:
          action:
            radius: 30
      inventory: 
        loot: null
        equipment:
          armor: null
          tool: null
          utility: null
          weapon: shortsword
          shield: buckler
        wallet: 0
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
            radius: 128
            limit: 0.50
            enemy: 5
          vision:
            radius: 128
          action:
            radius: 5
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
        loot: null
        equipment:
          armor: 
          tool: null
          utility: null
          weapon: shortsword
          shield: null
        wallet: 0
```

Logs:

```bash
(.venv) grant@skynet:~/Projects/ontology$ python src/cli.py --dump-state start world-01
2026-09-10 10:58:25,552 - INFO - __main__ - Starting CLI with command: 'start' for board: 'world-01'
2026-09-10 10:58:25,552 - INFO - __main__ - Igniting engine for live execution...
2026-09-10 10:58:25,552 - INFO - app.services.orchestration.constructors - Loading YAML data for target state: world-01 ...
2026-09-10 10:58:25,556 - INFO - app.config.loader - Loading YAML property schemas...
2026-09-10 10:58:25,762 - INFO - app.config.loader - Loading YAML configurations...
2026-09-10 10:58:25,965 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-10 10:58:26,036 - INFO - app.services.orchestration.constructors - Initializing SDL and Cython rendering subsystems...
2026-09-10 10:58:26,260 - INFO - app.services.orchestration.constructors - Constructing Empty Board and Migrator subsystem...
2026-09-10 10:58:26,262 - INFO - app.game.board - Initializing Board with 0 incoming assets.
2026-09-10 10:58:26,262 - INFO - app.game.board - Board completely hydrated and initialized.
2026-09-10 10:58:26,263 - INFO - app.services.orchestration.constructors - Initializing Registry...
2026-09-10 10:58:26,281 - INFO - app.services.orchestration.constructors - Injecting Generators and Devices into Board...
2026-09-10 10:58:26,283 - INFO - app.services.orchestration.constructors - Building rendering pipelines, mechanics, and UI...
2026-09-10 10:58:26,285 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 480x480)
2026-09-10 10:58:26,298 - INFO - app.services.orchestration.constructors - Engine successfully assembled.
2026-09-10 10:58:26,299 - INFO - app.game.engine - Entering Game Loop...
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
2026-09-10 10:58:27,013 - INFO - app.services.orchestration.migrator - Migrator starting hydration for target state: world-01
2026-09-10 10:58:27,013 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-10 10:58:27,123 - INFO - app.services.generators.perimeter - Calculating dynamic perimeter boundaries for layer: 0
2026-09-10 10:58:27,124 - INFO - app.services.generators.perimeter - Derived simply-connected hull containing 4 edges.
2026-09-10 10:58:27,124 - INFO - app.services.generators.perimeter - Calculating dynamic perimeter boundaries for layer: brick-house-compose-layer
2026-09-10 10:58:27,124 - INFO - app.services.generators.perimeter - Derived simply-connected hull containing 8 edges.
2026-09-10 10:58:27,542 - INFO - app.game.menus.controllers.load - Hydration complete. Reallocating rendering canvases...
2026-09-10 10:58:27,543 - INFO - app.game.screen - Rebaking Screen canvases for new world state...
2026-09-10 10:58:27,642 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 480x480)
2026-09-10 10:58:27,646 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn generated goal: object(door-strut-house-interior-1-1) on layer brick-house-compose-layer
2026-09-10 10:58:29,537 - INFO - app.game.logic.mechanics.intentional.transition - Transitioning evil-empress-jasilynn from Intentions.FIND to Intentions.INTERACT
2026-09-10 10:58:29,553 - INFO - app.game.logic.mechanics.intentional.transition - Transitioning evil-empress-jasilynn from Intentions.INTERACT to Intentions.IDLE
2026-09-10 10:58:29,570 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn recalled goal from memory: subject(player)
2026-09-10 10:58:29,570 - INFO - app.game.logic.mechanics.intentional.transition - Transitioning evil-empress-jasilynn from Intentions.IDLE to Intentions.FIND
2026-09-10 10:58:37,595 - INFO - app.game.engine - [TELEMETRY] Avg FPS: 53.1 |Avg UPS (Ticks): 59.8
^C2026-09-10 10:58:37,803 - INFO - __main__ - Game engine loop interrupted by user.
2026-09-10 10:58:37,804 - INFO - __main__ - Generating state dump...
2026-09-10 10:58:37,922 - INFO - __main__ - State dump successfully written to /home/grant/Projects/ontology/20260910_105837.state-dump.md
2026-09-10 10:58:38,009 - INFO - __main__ - CLI processes completed.
```

State Dump (Relevant sections):

```markdown

## evil-empress-jasilynn 

**Taxonomy:** 
  - Category: `sheets` 
  - Instance: `sprites`
  - ID: `jasilynn`
**Layer:** 0
- **Depth:** 0
- **Position:** (-8, 135)
- **Velocity:** (, )
- **Animation:** 
  - Action: `walk`
  - Direction: `down`
  - Frame: 5
  - Tick: 0
- **Character:** STR: 5, DEF: 5, SPD: 50, IMP: 25
- **Psyche**:
  - Persona: empress-jasilynn
  - Motivation: conquest
  - Dialogue: greeting
- **Meters:**
  - Health: 50 / 100
  - Magic: 100 / 100
- **Inventory:**
  - Wallet: 0
  - Equipment: 
    - Armor: `None` 
    - Weapon: `shortsword`
    - Tool: `None`
    - Utility: `None`
    - Shield: `None`
- **Goal:** 
  - Name: `player`
  - Category: `subject`
  - Layer: `0
  - Position: (10, 155)
- **Mutators:**
  - Triggers: Animated: True, Struck: , Frightened: False, Dead: False, Vision: True
  - Parameters:
    - Fear: Radius 128, Limit 0.5, Enemy 5
    - Vision: Radius 128
    - Action: Radius 5
- **Memory:**
  - Sprites:
    - `player`: `(10, 155)`
  - Relationships: `{'player': <Relationships.FRIEND: 'friend'>}`
- **Intention:** `Intentions.FIND`

## player 

**Taxonomy:** 
  - Category: `sheets` 
  - Instance: `players`
  - ID: `player`
**Layer:** 0
- **Depth:** 0
- **Position:** (10, 155)
- **Velocity:** (, )
- **Animation:** 
  - Action: `walk`
  - Direction: `down`
  - Frame: 0
  - Tick: 0
- **Character:** STR: 5, DEF: 5, SPD: 100, IMP: 25
- **Meters:**
  - Health: 50 / 100
  - Magic: 100 / 100
- **Inventory:**
  - Wallet: 0
  - Equipment: 
    - Armor: `None` 
    - Weapon: `shortsword`
    - Tool: `None`
    - Utility: `None`
    - Shield: `buckler`
- **Goal:** 
  - Name: `None`
  - Category: `None`
  - Layer: `None
  - Position: (10, 155)
- **Mutators:**
  - Triggers: Animated: False, Struck: , Frightened: False, Dead: False, Vision: False
  - Parameters:
    - Fear: Radius 30, Limit 0.5, Enemy 5
    - Vision: Radius 30
    - Action: Radius 30
- **Intention:** `Intentions.IDLE`
```

##### Root Cause Analysis

The root cause of this regression stems from a mathematical conflict between the engine's rigid-body spatial resolution (`CollisionMechanics`) and the pure-point distance logic used by the Intentional Scripting Language (`is_near`), compounded by a misconfigured parameter.

Based on the provided game logs and engine architecture, `evil-empress-jasilynn` is behaving exactly as programmed, but she is mathematically blocked from fulfilling the transition conditions for `speak`.

1. **Physics Collision Constraints:** Both the Player and Jasilynn are `sprites` with mass ($m > 0$). When Jasilynn attempts to navigate to the Player's coordinates, `physics.collide` resolves their physical overlap by separating their Hitboxes. For standard LPC sprites, the bounding boxes dictate that their top-left `Position` origins can never get closer than the sum of their hitbox half-extents (approximately 22 pixels).
2. **ISL Distance Logic:** The Intentional Scripting Language condition for `find:speak` evaluates `functions.is_near(sprite.position, target.position, action.radius)`. The `is_near` function in `Environ` calculates a strict Euclidean point-to-point distance between the two top-left origins, without accounting for the entity's dimensions or bounding boxes.
3. **Parameter Mismatch:** In the state dump, `evil-empress-jasilynn` is configured with `mutators.parameters.action.radius` set to `5`.

Because the physics engine rigidly enforces a minimum origin distance of ~22 pixels, the condition `(dx*dx + dy*dy) <= (5 * 5)` perpetually evaluates to `False` ($22^2 = 484 \gg 25$). Visually, the sprites are touching, but programmatically, they are not within the 5-pixel origin threshold required to trigger the transition.

*(Note: The transition from `find` to `interact` for the door succeeded because the door is a sensor/static object that does not repel the sprite's origin, allowing her to achieve an exact coordinate match).*

### Proposed Remediation

Two avenues for resolving this issue, depending on whether it is the engine that is patched or the asset configurations.

**Option 1: Configuration Patch (Recommended)**

Update the NPC YAML configurations to ensure their `action.radius` accounts for physical bounding box separation. The `player` asset already utilizes an `action.radius` of `30`, which successfully bridges the ~22-pixel physical gap.

* **Fix:** Increase `evil-empress-jasilynn`'s `action.radius` to `30`.

**Option 2: Engine Patch**

If `action.radius` is strictly intended to represent edge-to-edge distance rather than origin-to-origin distance, `Environ.is_near` must be brought into alignment with the spatial logic used by the rest of the engine.

* **Fix:** Refactor `functions.is_near` in `app.services.translators.environ` to evaluate intersecting Axis-Aligned Bounding Boxes (AABBs) padded by the radius, mirroring the logic currently successfully implemented in `SocialMechanics.proximities`.