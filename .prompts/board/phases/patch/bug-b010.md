##### Bug B010: Overlapping Fluid Shoreline Generation During Gate Switch

**STATUS**: CLOSED
**SEVERITY**: HIGH

###### Description

Player intersects Plate and triggers an unrelated Gate to open. This produces shoreline spawning where adjacent Fluids intersect. Player manually kills application through Ctrl+C.

###### Initial Conditions 

**Property File**

```yaml
effects:
  fluids:
    # -------------------------------------------------------
    waterflow-00:
      dimensions:
        w: 32
        l: 32
      lifecycle: 
        type: continuous
        delay: 60
      count: 3
      hitboxes: null
      mass: 0
    # -------------------------------------------------------
    waterflow-01:
      dimensions:
        w: 32
        l: 96
      lifecycle:
        type: continuous
        delay: 20
      count: 5
      hitboxes: null
      mass: 0
geography:
  shorelines:
    grassy-shore:
      tile: grass
      fluid: waterflow-00
      dimensions: 
        w: 32
        l: 32
      thickness: 10
      mass: -1
      hitboxes: null
```

**State File**

```yaml
effects:
  fluids:
    - id: waterflow-00
      name: jasilynns-tears-00
      layer: '0'
      position:
        x: 70
        y: 0
      flow: 2
      source: down
    - id: waterflow-00
      name: jasilynns-tears-01
      layer: '0'
      position:
        x: 100
        y: 0
      flow: 2
      source: down
    - id: waterflow-00
      name: jasilynns-tears-02
      layer: '0'
      position:
        x: 600
        y: 600
      source: left
    - id: waterflow-00
      name: jasilynns-tears-03
      layer: '0'
      flow: 4
      position:
        x: 632
        y: 0
      source: down
```

###### Application Logs

```bash
(.venv) grant@skynet:~/Projects/ontology$ python src/cli.py --dump-state start world-01
2026-09-29 18:00:22,922 - INFO - __main__ - Starting CLI with command: 'start' for board: 'world-01'
2026-09-29 18:00:22,923 - INFO - __main__ - Igniting engine for live execution...
2026-09-29 18:00:22,923 - INFO - app.config.loader - Loading YAML property schemas...
2026-09-29 18:00:23,132 - INFO - app.config.loader - Loading YAML configurations...
2026-09-29 18:00:23,351 - INFO - app.services.orchestration.builder - Loading YAML data for target state: world-01 ...
2026-09-29 18:00:23,352 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-29 18:00:23,444 - INFO - app.services.orchestration.builder - Compiling master mechanic executors...
2026-09-29 18:00:23,451 - INFO - app.services.orchestration.builder - Initializing SDL and Cython rendering subsystems...
2026-09-29 18:00:23,692 - INFO - app.services.orchestration.builder - Constructing Empty Board and Migrator subsystem...
2026-09-29 18:00:23,693 - INFO - app.game.board - Initializing Board with 0 incoming assets.
2026-09-29 18:00:23,693 - INFO - app.game.board - Board completely hydrated and initialized.
2026-09-29 18:00:23,694 - INFO - app.services.orchestration.builder - Initializing Registry with native models...
2026-09-29 18:00:23,708 - INFO - app.services.orchestration.builder - Injecting Generators and Devices into Board...
2026-09-29 18:00:23,708 - INFO - app.services.orchestration.builder - Building rendering pipelines, mechanics, and UI...
2026-09-29 18:00:23,709 - INFO - app.services.orchestration.builder - Compiling relational indices...
2026-09-29 18:00:23,709 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 480x480)
2026-09-29 18:00:23,711 - INFO - app.services.orchestration.builder - Engine successfully assembled.
2026-09-29 18:00:23,712 - INFO - app.game.engine - Entering Game Loop...
2026-09-29 18:00:23,746 - INFO - app.services.orchestration.migrator - Migrator starting hydration for target state: world-01
2026-09-29 18:00:23,747 - INFO - app.config.loader - Loading YAML state configurations from /home/grant/Projects/ontology/src/data/state/world-01 ...
2026-09-29 18:00:23,861 - INFO - app.game.board - Appending Asset(id=frame-brick, name=strut-house-1, category=crafts, instance=struts)
2026-09-29 18:00:23,861 - INFO - app.game.board - Appending Asset(id=door-house, name=door-strut-house-1-1, category=objects, instance=doors)
2026-09-29 18:00:23,862 - INFO - app.game.board - Appending Asset(id=wall-blue, name=strut-house-interior-1, category=crafts, instance=struts)
2026-09-29 18:00:23,862 - INFO - app.game.board - Appending Asset(id=wood-bookshelf, name=crate-strut-house-interior-1-1, category=objects, instance=crates)
2026-09-29 18:00:23,862 - INFO - app.game.board - Appending Asset(id=door-shadow, name=door-strut-house-interior-1-1, category=objects, instance=doors)
2026-09-29 18:00:23,862 - INFO - app.game.board - Appending Asset(id=floor-wood, name=strut-strut-house-interior-1-1, category=crafts, instance=struts)
2026-09-29 18:00:23,862 - INFO - app.game.board - Appending Asset(id=grandfather-clock, name=passive-strut-house-interior-1-1, category=effects, instance=passive)
2026-09-29 18:00:24,010 - INFO - app.game.board - Appending Asset(id=wall-castle, name=strut-castle-exterior-2, category=crafts, instance=struts)
2026-09-29 18:00:24,011 - INFO - app.game.board - Appending Asset(id=door-castle-open, name=door-strut-castle-exterior-2-2, category=objects, instance=doors)
2026-09-29 18:00:24,011 - INFO - app.game.board - Appending Asset(id=castle-gate, name=gate-strut-castle-exterior-2-2, category=objects, instance=gates)
2026-09-29 18:00:24,011 - INFO - app.game.board - Appending Asset(id=stone-switch, name=plate-strut-castle-exterior-2-2, category=objects, instance=plates)
2026-09-29 18:00:24,011 - INFO - app.game.board - Appending Asset(id=torch, name=passive-strut-castle-exterior-2-2, category=effects, instance=passive)
2026-09-29 18:00:24,011 - INFO - app.game.board - Appending Asset(id=torch, name=passive-strut-castle-exterior-2-2, category=effects, instance=passive)
2026-09-29 18:00:24,012 - INFO - app.game.board - Appending Asset(id=grass, name=the-steppe, category=tiles, instance=back)
2026-09-29 18:00:24,018 - INFO - app.game.board - Appending Asset(id=wood-barrel, name=castle-dawn-barrel-00, category=objects, instance=crates)
2026-09-29 18:00:24,019 - INFO - app.game.board - Appending Asset(id=gray-rock-00, name=jasilynns-rock, category=objects, instance=obstacles)
2026-09-29 18:00:24,019 - INFO - app.game.board - Appending Asset(id=gray-rock-00, name=jasilynns-other-rock, category=objects, instance=obstacles)
2026-09-29 18:00:24,019 - INFO - app.game.board - Appending Asset(id=wood-bulletin, name=castle-dawn-sign-board-00, category=objects, instance=signs)
2026-09-29 18:00:24,019 - INFO - app.game.board - Appending Asset(id=spinning-dummy, name=test-dummy, category=effects, instance=reactables)
2026-09-29 18:00:24,019 - INFO - app.game.board - Appending Asset(id=waterflow-00, name=jasilynns-tears-00, category=effects, instance=fluids)
2026-09-29 18:00:24,020 - INFO - app.game.board - Appending Asset(id=waterflow-00, name=jasilynns-tears-01, category=effects, instance=fluids)
2026-09-29 18:00:24,020 - INFO - app.game.board - Appending Asset(id=waterflow-00, name=jasilynns-tears-02, category=effects, instance=fluids)
2026-09-29 18:00:24,020 - INFO - app.game.board - Appending Asset(id=waterflow-00, name=jasilynns-tears-03, category=effects, instance=fluids)
2026-09-29 18:00:24,020 - INFO - app.game.board - Appending Asset(id=jasilynn, name=evil-empress-jasilynn, category=sheets, instance=sprites)
2026-09-29 18:00:24,020 - INFO - app.game.board - Appending Asset(id=player, name=player, category=sheets, instance=players)
2026-09-29 18:00:24,020 - INFO - app.services.generators.game.perimeter - Calculating dynamic perimeter boundaries for layer: 0
2026-09-29 18:00:24,020 - INFO - app.services.generators.game.perimeter - Derived simply-connected hull containing 4 edges.
2026-09-29 18:00:24,021 - INFO - app.services.generators.game.perimeter - Calculating dynamic perimeter boundaries for layer: brick-house-compose-layer
2026-09-29 18:00:24,021 - INFO - app.services.generators.game.perimeter - Derived simply-connected hull containing 4 edges.
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
libpng warning: iCCP: known incorrect sRGB profile
2026-09-29 18:00:30,884 - INFO - app.game.menus.controllers.load - Hydration complete. Reallocating rendering canvases...
2026-09-29 18:00:30,885 - INFO - app.game.screen - Rebaking Screen canvases for new world state...
2026-09-29 18:00:30,945 - INFO - app.game.screen - Initializing Screen (Viewport: 480x480 |Board: 239x264)
2026-09-29 18:00:30,949 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn tracked Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(47, 142))
2026-09-29 18:00:30,951 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:30,969 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-4c60223a, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-665af1ed, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-1b30ea72, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-6f489a10, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-469f4874, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-607c4e90, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-85f56fe7, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-752dda1d, category=geography, instance=shorelines)
2026-09-29 18:00:30,970 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-5fe8db8f, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-add8d00c, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-a47edfb4, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-bb76fed8, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-b341955c, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-32a50910, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-25c81f21, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-16e8da87, category=geography, instance=shorelines)
2026-09-29 18:00:30,971 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-70161105, category=geography, instance=shorelines)
2026-09-29 18:00:30,972 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn tracked Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(47, 142))
2026-09-29 18:00:31,001 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:31,027 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:31,038 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): Intentions.FIND -> interact
2026-09-29 18:00:31,038 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn resolved Goal(category=object, name = door-strut-house-interior-1-1, layer = brick-house-compose-layer, position=(47, 142))
2026-09-29 18:00:31,039 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): Intentions.INTERACT -> idle
2026-09-29 18:00:31,039 - INFO - app.game.logic.mechanics.intentional.cognition - evil-empress-jasilynn remembered Goal(category=subject, name = player, layer = 0, position=(100, 200))
2026-09-29 18:00:31,039 - INFO - app.game.logic.mechanics.intentional.transition - Transition(evil-empress-jasilynn): Intentions.IDLE -> find
2026-09-29 18:00:31,056 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:31,750 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:31,800 - INFO - app.game.board - Appending Asset(id=splash, name=spawn-05c858d1, category=effects, instance=passive)
2026-09-29 18:00:32,768 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:33,785 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:34,802 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:35,819 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:36,836 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:36,906 - INFO - app.game.logic.mechanics.world.fluid - Telemetry:FluidMechanics-Invalidation:Gate-gate-strut-castle-exterior-2-2 switch: True
2026-09-29 18:00:36,924 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-ffca8869, category=geography, instance=shorelines)
2026-09-29 18:00:36,925 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-f20a0837, category=geography, instance=shorelines)
2026-09-29 18:00:36,925 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-12ff422c, category=geography, instance=shorelines)
2026-09-29 18:00:36,925 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-8873109e, category=geography, instance=shorelines)
2026-09-29 18:00:36,925 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-5d90ec45, category=geography, instance=shorelines)
2026-09-29 18:00:36,925 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-c6ce86e0, category=geography, instance=shorelines)
2026-09-29 18:00:36,926 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-f70ea957, category=geography, instance=shorelines)
2026-09-29 18:00:36,926 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-22c70af2, category=geography, instance=shorelines)
2026-09-29 18:00:36,926 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-0090f790, category=geography, instance=shorelines)
2026-09-29 18:00:36,926 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-97130062, category=geography, instance=shorelines)
2026-09-29 18:00:36,926 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-75d4f0ae, category=geography, instance=shorelines)
2026-09-29 18:00:36,926 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-e3d8f97a, category=geography, instance=shorelines)
2026-09-29 18:00:36,927 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-24feed2e, category=geography, instance=shorelines)
2026-09-29 18:00:36,927 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-44be4cf7, category=geography, instance=shorelines)
2026-09-29 18:00:36,927 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-912af574, category=geography, instance=shorelines)
2026-09-29 18:00:36,927 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-2135c79d, category=geography, instance=shorelines)
2026-09-29 18:00:36,927 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-4d8c0986, category=geography, instance=shorelines)
2026-09-29 18:00:37,847 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:38,298 - INFO - app.game.logic.mechanics.world.fluid - Telemetry:FluidMechanics-Invalidation:Gate-gate-strut-castle-exterior-2-2 switch: False
2026-09-29 18:00:38,317 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-a24c92cb, category=geography, instance=shorelines)
2026-09-29 18:00:38,317 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-51d49be1, category=geography, instance=shorelines)
2026-09-29 18:00:38,317 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-9350bba3, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-5fee0134, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-7ec1a494, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-a9792684, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-1b4eba6f, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-5c36e8bc, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-e134fc04, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-0bbabf1b, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-65c08a1b, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-6500966d, category=geography, instance=shorelines)
2026-09-29 18:00:38,318 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-a713a1a5, category=geography, instance=shorelines)
2026-09-29 18:00:38,319 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-e255bfd9, category=geography, instance=shorelines)
2026-09-29 18:00:38,319 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-6388aa00, category=geography, instance=shorelines)
2026-09-29 18:00:38,319 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-7b7d5297, category=geography, instance=shorelines)
2026-09-29 18:00:38,319 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-336f027c, category=geography, instance=shorelines)
2026-09-29 18:00:38,319 - INFO - app.game.board - Appending Asset(id=grassy-shore, name=spawn-44d98111, category=geography, instance=shorelines)
2026-09-29 18:00:38,872 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:39,889 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:40,906 - INFO - app.game.logic.mechanics.intentional.navigation - Pathfinding stalled for evil-empress-jasilynn; no valid route found.
2026-09-29 18:00:40,955 - INFO - app.game.engine - Avg FPS: 34.8 |Avg UPS: 59.9
^C2026-09-29 18:00:41,312 - INFO - __main__ - Signal 2 received. Requesting graceful engine shutdown...
2026-09-29 18:00:41,315 - INFO - __main__ - Generating state dump...
2026-09-29 18:00:41,631 - INFO - __main__ - State dump successfully written to /home/grant/Projects/ontology/20260929_180041.state-dump.md
2026-09-29 18:00:41,631 - INFO - app.game.engine - Stopping Engine and releasing resources...
2026-09-29 18:00:42,017 - INFO - __main__ - CLI processes completed.
```

###### State Dump

```markdown
# Ontology: State Dump

- **Board:** world-01
- **Timestamp:** 20260929_180041

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
  - Position: (182, 868)
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
  - Position: (33, 71)
  - Velocity: (-0.0, -0.0)
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
    - Position: (193, 913)
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
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 12
- **State:**
  - Layer: `brick-house-compose-layer`
  - Depth: 0
  - Position: (1, 30)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 1
    - Tick: 41
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## strut-castle-exterior-2

- **Taxonomy:**
  - Category: `crafts`
  - Instance: `struts`
  - ID: `wall-castle`
  - Name: `strut-castle-exterior-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 222
    - Length: 133
  - Mass: 0
  - Cost:
    - `stone`: 100
  - Hitboxes:
    - Position: (178, 102) | Dimensions: w: 25, l: 12
    - Position: (17, 102) | Dimensions: w: 25, l: 12
    - Position: (5, 39) | Dimensions: w: 203, l: 63
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (250, 250)
  - Owner: `the-government`
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## door-strut-castle-exterior-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `doors`
  - ID: `door-castle-open`
  - Name: `door-strut-castle-exterior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 64
    - Length: 64
  - Mass: -1
  - Count: 1
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 383
  - Position: (331, 299)
  - Door Out:
    - Layer: `castle-compose-layer`
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## gate-strut-castle-exterior-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `gates`
  - ID: `castle-gate`
  - Name: `gate-strut-castle-exterior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.BinaryAnimation'>`
  - Frame: `<class 'app.assets.frames.core.IterableFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 64
    - Length: 64
  - Mass: 0
  - Count: 2
- **State:**
  - Layer: `0`
  - Depth: 1
  - Height: 383
  - Position: (331, 299)
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 1
  - Switch: False
  - Link: `castle-gate-link`
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## plate-strut-castle-exterior-2-2

- **Taxonomy:**
  - Category: `objects`
  - Instance: `plates`
  - ID: `stone-switch`
  - Name: `plate-strut-castle-exterior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.BinaryAnimation'>`
  - Frame: `<class 'app.assets.frames.core.IterableFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 15
    - Length: 14
  - Mass: -1
  - Count: 2
- **State:**
  - Layer: `0`
  - Depth: 1
  - Height: 383
  - Position: (274, 395)
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 1
  - Switch: False
  - Link: `castle-gate-link`
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## passive-strut-castle-exterior-2-2

- **Taxonomy:**
  - Category: `effects`
  - Instance: `passive`
  - ID: `torch`
  - Name: `passive-strut-castle-exterior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.IterableFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 64
  - Mass: -1
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=15, frequency=0, cooldown=60, persist=False)
  - Count: 9
- **State:**
  - Layer: `0`
  - Depth: 1
  - Height: 383
  - Position: (265, 308)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 11
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## passive-strut-castle-exterior-2-2

- **Taxonomy:**
  - Category: `effects`
  - Instance: `passive`
  - ID: `torch`
  - Name: `passive-strut-castle-exterior-2-2`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.IterableFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 64
  - Mass: -1
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=15, frequency=0, cooldown=60, persist=False)
  - Count: 9
- **State:**
  - Layer: `0`
  - Depth: 1
  - Height: 383
  - Position: (424, 308)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 4
    - Tick: 11
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


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
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## castle-dawn-barrel-00

- **Taxonomy:**
  - Category: `objects`
  - Instance: `crates`
  - ID: `wood-barrel`
  - Name: `castle-dawn-barrel-00`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 28
    - Length: 38
  - Mass: 5
  - Count: 1
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 28, l: 38
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (140, 250)
  - Velocity: (0.0, 0.0)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## jasilynns-rock

- **Taxonomy:**
  - Category: `objects`
  - Instance: `obstacles`
  - ID: `gray-rock-00`
  - Name: `jasilynns-rock`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 56
    - Length: 56
  - Mass: 0
  - Count: 1
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (68, 600)
  - Velocity: (0.0, 0.0)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## jasilynns-other-rock

- **Taxonomy:**
  - Category: `objects`
  - Instance: `obstacles`
  - ID: `gray-rock-00`
  - Name: `jasilynns-other-rock`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 56
    - Length: 56
  - Mass: 0
  - Count: 1
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (632, 600)
  - Velocity: (0.0, 0.0)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## castle-dawn-sign-board-00

- **Taxonomy:**
  - Category: `objects`
  - Instance: `signs`
  - ID: `wood-bulletin`
  - Name: `castle-dawn-sign-board-00`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 30
    - Length: 32
  - Mass: 0
  - Count: 1
  - Hitboxes:
    - Position: (4, 4) | Dimensions: w: 22, l: 24
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (430, 370)
  - Persona: `castle-dawn-sign`
  - Lexicon: `spring`
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## test-dummy

- **Taxonomy:**
  - Category: `effects`
  - Instance: `reactables`
  - ID: `spinning-dummy`
  - Name: `test-dummy`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.IterableFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 64
    - Length: 64
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.TEMPORARY: 'temporary'>, delay=5, frequency=0, cooldown=30, persist=True)
  - Count: 8
  - Hitboxes:
    - Position: (2, 20) | Dimensions: w: 14, l: 14
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (225, 500)
  - Active: `False`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 0
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False
  - Intention: `attack`


## jasilynns-tears-00

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow-00`
  - Name: `jasilynns-tears-00`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.effects.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (70, 1)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 1
    - Tick: 41
  - Source: `down`
  - Flow: 2
  - Length: 599
  - Dirty: False
  - Pool:
    - Position: (0, 512)
    - Dimensions: w: 192, l: 224
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 599
    - Position: (-70, 511) | Dimensions: w: 192, l: 224
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## jasilynns-tears-01

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow-00`
  - Name: `jasilynns-tears-01`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.effects.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (104, 1)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 1
    - Tick: 41
  - Source: `down`
  - Flow: 2
  - Length: 599
  - Dirty: False
  - Pool:
    - Position: (0, 512)
    - Dimensions: w: 192, l: 224
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 599
    - Position: (-103, 511) | Dimensions: w: 192, l: 224
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## jasilynns-tears-02

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow-00`
  - Name: `jasilynns-tears-02`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.effects.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (600, 600)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 1
    - Tick: 41
  - Source: `left`
  - Flow: 1
  - Length: 476
  - Dirty: False
  - Pool:
    - Position: (32, 544)
    - Dimensions: w: 128, l: 160
  - Hitboxes:
    - Position: (-476, 0) | Dimensions: w: 476, l: 32
    - Position: (-568, -56) | Dimensions: w: 128, l: 160
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## jasilynns-tears-03

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow-00`
  - Name: `jasilynns-tears-03`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.effects.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (632, 1)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 1
    - Tick: 41
  - Source: `down`
  - Flow: 4
  - Length: 599
  - Dirty: False
  - Pool:
    - Position: (480, 448)
    - Dimensions: w: 352, l: 352
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 599
    - Position: (-152, 447) | Dimensions: w: 352, l: 352
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## evil-empress-jasilynn

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `sprites`
  - ID: `jasilynn`
  - Name: `evil-empress-jasilynn`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.SpriteAnimation'>`
  - Frame: `<class 'app.assets.frames.sheets.SpriteFrame'>`
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
  - Position: (141, 880)
  - Velocity: (-3.0092408657073975, -49.90936279296875)
  - Animation:
    - Action: `walk`
    - Direction: `up`
    - Frame: 7
    - Tick: 1
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
    - Position: (100, 200)
  - Mutators:
    - Triggers:
      - Animated: True
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False
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
      - `player`: (100, 200)
    - Doors:
      - `door-strut-house-interior-1-1`: `0`
    - Relationships:
      - `player`: `friend`
  - Psyche:
    - Persona: `empress-jasilynn`
    - Motivation: `conquest`
    - Dialogue: `greeting`
  - Intention: `find`


## player

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `players`
  - ID: `player`
  - Name: `player`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.SpriteAnimation'>`
  - Frame: `<class 'app.assets.frames.sheets.SpriteFrame'>`
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
  - Position: (253, 386)
  - Velocity: (0.0, 0.0)
  - Animation:
    - Action: `walk`
    - Direction: `left`
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
    - Position: (253, 386)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False
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


## spawn-a24c92cb

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-a24c92cb`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (70, 1)
  - Orientation: `left`
  - Thickness: 10
  - Bidirectional: True
  - Length: 511
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 10, l: 511
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-51d49be1

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-51d49be1`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (103, 1)
  - Orientation: `left`
  - Thickness: 10
  - Bidirectional: True
  - Length: 511
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 10, l: 511
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-9350bba3

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-9350bba3`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (103, 1)
  - Orientation: `right`
  - Thickness: 10
  - Bidirectional: True
  - Length: 511
  - Hitboxes:
    - Position: (22, 0) | Dimensions: w: 10, l: 511
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-5fee0134

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-5fee0134`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (160, 512)
  - Orientation: `right`
  - Thickness: 10
  - Bidirectional: True
  - Length: 88
  - Hitboxes:
    - Position: (22, 0) | Dimensions: w: 10, l: 88
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-7ec1a494

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-7ec1a494`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (160, 632)
  - Orientation: `right`
  - Thickness: 10
  - Bidirectional: True
  - Length: 104
  - Hitboxes:
    - Position: (22, 0) | Dimensions: w: 10, l: 104
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-a9792684

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-a9792684`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (480, 448)
  - Orientation: `left`
  - Thickness: 10
  - Bidirectional: True
  - Length: 152
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 10, l: 152
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-1b4eba6f

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-1b4eba6f`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (480, 632)
  - Orientation: `left`
  - Thickness: 10
  - Bidirectional: True
  - Length: 168
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 10, l: 168
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-5c36e8bc

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-5c36e8bc`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (632, 1)
  - Orientation: `left`
  - Thickness: 10
  - Bidirectional: True
  - Length: 447
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 10, l: 447
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-e134fc04

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-e134fc04`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (632, 1)
  - Orientation: `right`
  - Thickness: 10
  - Bidirectional: True
  - Length: 447
  - Hitboxes:
    - Position: (22, 0) | Dimensions: w: 10, l: 447
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-0bbabf1b

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-0bbabf1b`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (800, 448)
  - Orientation: `right`
  - Thickness: 10
  - Bidirectional: True
  - Length: 352
  - Hitboxes:
    - Position: (22, 0) | Dimensions: w: 10, l: 352
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-65c08a1b

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-65c08a1b`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (480, 448)
  - Orientation: `up`
  - Thickness: 10
  - Bidirectional: True
  - Length: 152
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 152, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-6500966d

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-6500966d`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (664, 448)
  - Orientation: `up`
  - Thickness: 10
  - Bidirectional: True
  - Length: 168
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 168, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-a713a1a5

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-a713a1a5`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (0, 512)
  - Orientation: `up`
  - Thickness: 10
  - Bidirectional: True
  - Length: 70
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 70, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-e255bfd9

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-e255bfd9`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (135, 512)
  - Orientation: `up`
  - Thickness: 10
  - Bidirectional: True
  - Length: 57
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 57, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-6388aa00

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-6388aa00`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (192, 600)
  - Orientation: `up`
  - Thickness: 10
  - Bidirectional: True
  - Length: 288
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 288, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-7b7d5297

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-7b7d5297`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (192, 600)
  - Orientation: `down`
  - Thickness: 10
  - Bidirectional: True
  - Length: 288
  - Hitboxes:
    - Position: (0, 22) | Dimensions: w: 288, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-336f027c

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-336f027c`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (0, 704)
  - Orientation: `down`
  - Thickness: 10
  - Bidirectional: True
  - Length: 192
  - Hitboxes:
    - Position: (0, 22) | Dimensions: w: 192, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False


## spawn-44d98111

- **Taxonomy:**
  - Category: `geography`
  - Instance: `shorelines`
  - ID: `grassy-shore`
  - Name: `spawn-44d98111`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.geography.ShorelineFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Tile: `grass`
  - Fluid: `waterflow-00`
  - Thickness: 10
- **State:**
  - Layer: `0`
  - Depth: 0
  - Height: 0
  - Position: (480, 768)
  - Orientation: `down`
  - Thickness: 10
  - Bidirectional: True
  - Length: 352
  - Hitboxes:
    - Position: (0, 22) | Dimensions: w: 352, l: 10
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
      - Submerged: False

---

# Perimeters

## Layer: 0

* Position: (0, 0) | Dimensions: w: 1, l: 3200
* Position: (3200, 0) | Dimensions: w: 1, l: 3200
* Position: (0, 0) | Dimensions: w: 3200, l: 1
* Position: (0, 3200) | Dimensions: w: 3200, l: 1

## Layer: brick-house-compose-layer

* Position: (0, 0) | Dimensions: w: 1, l: 192
* Position: (128, 0) | Dimensions: w: 1, l: 192
* Position: (0, 0) | Dimensions: w: 128, l: 1
* Position: (0, 192) | Dimensions: w: 128, l: 1
```



##### Root Cause Analysis

The bug is caused by a **property misconfiguration in the property file**: `mass: 0` was configured for `waterflow-00` and `waterflow-01`.

In Ontology’s physics and spatial indexing architecture, $m = 0$ denotes an **immovable, solid static body** (such as a stone wall or obstacle), while $m = -1$ denotes a **sensor** (such as a plate, ledge, or trigger area) that registers overlap queries but is strictly bypassed by collision and spatial displacement resolution.

```
Expected Architecture:
  Fluid (m = -1: Sensor)   ---> Bypassed by CollisionMechanics ---> Stays at x=70, x=100 (Overlapping)
                                                                 ---> Cartographer sweeps merged water mask
                                                                 ---> NO inter-stream shorelines

Actual Architecture:
  Fluid (m = 0: Static Body) ---> Board._cached_weights[layer] ingests Fluids (mass >= 0)
                              ---> CollisionMechanics detects stream & boundary AABB overlap
                              ---> Post-frame overlap separation displaces tears-01: x=100 -> x=104, y=0 -> y=1
                              ---> 2px dry land gap emerges between stream margins (x=102..104)
                              ---> Gate switch invalidates layer -> Cartographer regenerates
                              ---> Cartographer finds dry substrate at x=103 -> Spawns opposing shorelines!

```

---

##### Step-by-Step Breakdown of the Execution Failure

###### 1. Registration into Collision Structures

In `src/app/game/board.py`:

```python
if hasattr(asset.properties, 'mass') and asset.properties.mass >= 0:
    self._cached_weights[layer].append(asset)

```

Because `waterflow-00` has `mass: 0` in `effects/fluids`, every spawned fluid instance (`jasilynns-tears-00`, `jasilynns-tears-01`, etc.) is registered into `board._cached_weights[layer]`.

###### 2. Frame 1 (Startup Hydration)

On the very first frame:

* `FluidMechanics.update()` executes its initialization pass (`not self._initialized`), running `Cartographer.generate()` on the initial state coordinates: `tears-00` at $x \in [70, 102)$ and `tears-01` at $x \in [100, 132)$.
* The two corridors overlap across $x \in [100, 102)$.
* `geometry.contours()` merges the overlapping intervals in its sweep-line pass, dissolving the shared internal edges. As expected, **zero shorelines are generated between the streams**.

###### 3. Steady-State Gameplay (Physical Overlap Separation)

As gameplay proceeds:

* `CollisionMechanics` iterates over `board.weights(layer)`.
* Because `tears-00` and `tears-01` both have $m = 0$ with intersecting hitboxes, and intersect the static upper perimeter boundary at $y = 0$, `physics.collide` and boundary constraints resolve the spatial overlap:
* Overlap with the map perimeter ($y=0, l=1$) displaces $y$ from `0` to `1` across all downward fluids.
* Overlap between `tears-00` and `tears-01` ($x \in [100, 102)$) resolves by pushing `tears-01` along $+X$, displacing it from $x = 100$ to **$x = 104$** (as recorded in the state dump: `Position: (104, 1)`).
* `tears-00` now terminates at $x = 102$, while `tears-01` begins at $x = 104$, creating a **2-pixel gap of dry substrate (`the-steppe` grass tile)** between $x = 102$ and $x = 104$.
* However, because gate states have not changed, `fluid.state.dirty` remains `False`, so `Cartographer` does not execute and the visual anomaly remains dormant.

###### 4. The Gate Switch Trigger

When the player steps on `plate-strut-castle-exterior-2-2`:

* `FluidMechanics.update()` detects `curr_switch != prev_switch` on `gate-strut-castle-exterior-2-2` and marks all layer `0` fluids `dirty = True`.
* `Cartographer.purge(layer, board)` wipes the initial 17 shorelines.
* `Cartographer.generate(layer, board, self.shorelines)` samples the **current, physically displaced positions**:
    * Rect 1 (`tears-00`): $x \in [70, 102)$
    * Rect 2 (`tears-01`): $x \in [104, 136)$
* Because the streams no longer overlap or touch, `geometry.contours()` detects two distinct water bodies with dry land between them:
* A right-facing boundary at $x = 102$ (Land East, Water West) $\to$ `spawn-9350bba3` (Position: (103, 1), `orientation: right`).
* A left-facing boundary at $x = 104$ (Land West, Water East) $\to$ `spawn-51d49be1` (Position: (103, 1), `orientation: left`).
* **Result**: Opposing vertical shorelines suddenly spawn along the entire length ($L = 511$) of the inter-stream corridor where the fluids were meant to be merged.

---

##### Remediation

###### 1. Correct Fluid Properties (`src/assets/effects/*.yaml`)

Fluids are environmental flow fields and sensors; they must have `mass: -1`:

```yaml
effects:
  fluids:
    waterflow-00:
      dimensions:
        w: 32
        l: 32
      lifecycle: 
        type: continuous
        delay: 60
      count: 3
      hitboxes: null
      mass: -1
    waterflow-01:
      dimensions:
        w: 32
        l: 96
      lifecycle:
        type: continuous
        delay: 20
      count: 5
      hitboxes: null
      mass: -1

```

###### 2. Defensive Weight Filtering on `Board` (`src/app/game/board.py`)

To prevent configuration errors from injecting non-physical effects into the collision broad-phase, explicitly exclude `AssetCategories.EFFECTS.value` and `AssetCategories.GEOGRAPHY.value` from `_cached_weights`:

```python
# src/app/game/board.py
if (
    hasattr(asset.properties, 'mass') 
    and asset.properties.mass >= 0 
    and asset.category not in (AssetCategories.EFFECTS.value, AssetCategories.GEOGRAPHY.value)
):
    self._cached_weights[layer].append(asset)

```

---

##### Telemetry Logs for Verification

To verify that fluid positions remain immutable and that `Cartographer` receives merged water AABBs without spatial drift during gate switch cycles, add the following telemetry logs:

###### 1. Fluid Position Drift Check in `FluidMechanics.update`

```python
# src/app/game/logic/mechanics/world/fluid.py
for f in layer_fluids:
    logger.info(
        f"Telemetry:FluidMechanics:PrePropagate:{f.name} pos=({f.state.position.x}, {f.state.position.y}) "
        f"len={f.state.length} pool={f.state.pool}"
    )

```

###### 2. Water Mask & Contour Segment Log in `Cartographer.generate`

```python
# src/app/services/generators/game/cartographer.py
@classmethod
def generate(cls, layer: str, board: Board, index: ShorelineIndex) -> List[Asset]:
    water_rects = cls._collect_water_rectangles(layer, board)
    logger.info(f"Telemetry:Cartographer:{layer}:CollectedWaterRects={water_rects}")
    boundaries = geometry.contours(water_rects)
    logger.info(
        f"Telemetry:Cartographer:{layer}:DerivedContours="
        f"{[(b.position.x, b.position.y, b.dimensions.w, b.dimensions.l) for b in boundaries]}"
    )
    ...

```





