#### Implement: Phase 07 - Intentions

**1. Data Model Preparation**

* [ ] Update `IntentionConfiguration` in `app/models/config.py` to include `compiled_conditions: List[Callable] = field(default_factory=list)`.

**2. ISL Compilation Engine (`Orchestrator`)**

* [ ] Create a private method `_resolve_intentions(self)` in `Orchestrator` (called during `build_board`).
* [ ] Iterate through `self.context.configurations.intentions`. For each `IntentionConfiguration`, iterate through `conditions` (strings).
* [ ] Compile strings into lambdas using: `lambda_func = eval(f"lambda sprite, sprites: {condition_str}")`.
* [ ] Append the compiled functions to the `compiled_conditions` list on the `IntentionConfiguration` object.

**3. Chronological Refactoring (`TransitionMechanics`)**

* [ ] In `TransitionMechanics.update()`, generate `sprites_dict = {s.name: s for s in board.instances(AssetInstances.SPRITES) + board.instances(AssetInstances.PLAYERS)}` once at the start of the loop to satisfy the ISL target lookups.
* [ ] Invert the loop logic: evaluate the Intention Transition Matrix *first*. Use `all(cond(sprite.state, sprites_dict) for cond in transit.compiled_conditions)`.
* [ ] Apply the state transition if conditions are met, `break` the transition loop, and *then* calculate `AnimationMap.action` and `direction` using the newly resolved Intention.

**4. Complete the Finite Automaton**

* [ ] Review `/src/data/config/intentions/main.yaml` and resolve all dead ends.
* [ ] Ensure `follow` and `mock` transition logic actually evaluates environmental proximity or timers to prevent infinite state looping.
* [ ] Ensure existence checks (e.g., `sprite.goal`) precede attribute accesses (e.g., `sprite.goal.category`) in all YAML condition lists to safely exploit Python's `all()` short-circuiting.