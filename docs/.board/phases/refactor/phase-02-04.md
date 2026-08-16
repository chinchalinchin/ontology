#### Refactor: Phase 02.04 - Engine

**Goals** 

- CLI function for starting game engine.
- Sufficient Mechanics for basic animation, user input and Asset functionality.

**Further Analysis:**

Analyze code for bugs and logical errors.

**Tasks:**

- [x] **Task 1: Resolve Core Execution Blockers**
    - Update `Orchestrator.ignite()` to inject an instantiated list of `Mechanic` objects, replacing the placeholder dictionary.
    - Add `self` parameter to `MenuMechanics.equip()` method signature.
- [x] **Task 2: Fix Render Pipeline Depth Sorting**
    - Refactor `Screen.draw()` to apply depth-sorting (`sort(key=lambda a: a.state.position.y + a.dimensions.l)`) directly on the `assets` list *prior* to querying `asset.frame.keys()`.
- [x] **Task 3: Patch Data Hydration Edge-Cases**
    - Modify `Factory._hydrate()` to detect explicit `None` values and manually trigger the `default_factory` for collections (Lists, Dicts) to prevent `NoneType` attribute errors.
    - Standardize `AnimationMap.action()` to return `str` types uniformly (convert `Actions.CAST.value`).
- [x] **Task 4: Implement Basic Motion Mechanics**
    - Write the `MotionMechanics.update()` routine to calculate vectors between `asset.state.position` and `asset.state.goal.position`, updating the physical X/Y coordinates based on `asset.character.speed`.
- [x] **Task 5: Refactor Transition Logic**
    - Remove the hallucinated `sprite.transitions()` call in `TransitionMechanics`.
    - Query `board.configurations.intentions[sprite.state.intention]` to evaluate valid state transitions using the ISL expressions.