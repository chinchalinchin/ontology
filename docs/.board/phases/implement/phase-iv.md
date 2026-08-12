#### Implement: Phase IV - Intentions

##### Intentional Scripting Language (ISL)

To maintain performance, the custom ISL defined in `/src/data/intentions/main.yaml` must be compiled into executable Python `lambda` functions during the orchestration phase of the application bootstrap.

1. Board & Orchestrator Global Properties
    - [ ] Update Board.__init__ to accept and store a properties: Dict field.
    - [ ] Update Orchestrator.orchestrate() to inject self.properties into the Board upon instantiation.
2. ISL Compilation Engine (The Pythonic Way)
    - [ ] Create a parsing utility (e.g., inside app.hooks.factory or a new app.config.compiler module) to load /src/data/intentions/main.yaml.
    - [ ] Iterate over the transitions and convert the YAML condition strings into executable lambdas using eval(f"lambda sprite, sprites: {condition}").
    - [ ] Hydrate the IntentionProperties and Transition POPOs with these Callables and store the result in the Orchestrator's properties dictionary under the "intentions" key.
3. Refactor IntentionMechanics
    - [ ] Remove the transits = sprite.transitions() call from IntentionMechanics.update().
    - [ ] Generate a dictionary of all active sprites once per frame to satisfy the ISL sprites argument: sprites_dict = {s.name: s.state for s in board.instances(AssetInstances.SPRITES)}.
    - [ ] Retrieve the valid transitions for a sprite via board.properties["intentions"].intentions.get(sprite.state.intention, []).
    - [ ] Evaluate the compiled lambdas using all(cond(sprite.state, sprites_dict) for cond in transit.conditions) and update sprite.state.intention.
4. Complete the Finite Automaton
    - [ ] Review /src/data/intentions/main.yaml and resolve all dead ends. Provide valid next transitions and conditions for hunt, interact, mine, speak, sprint, and build.
    - [ ] Ensure speak transitions out when sprite.psyche.communication evaluates to false.