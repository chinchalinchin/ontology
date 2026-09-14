#### Refactor: Phase 02.06 - Effects

**Goals**: Refactor the Effect Asset.

##### Goal: Effect Schema Updates

**EffectProperties**

```yaml
objects:
    effects:
        dimensions:
            w: int
            l: int
        hitboxes:
            - position:
                x: int
                y: int
              dimensions:
                w: int
                l: int
        count: int 
        mass: int
        lifecycle: str
```

**Effect Animations**

- `temporary`
- `continuous`
- `periodic`

**Effect States**

- PassiveState, HazardState, CollectableState, InteractableState

```yaml
objects:
    effects:
        <passive>:
            layer: str
            depth: int
            height: int
            position: Position
            animation: AnimationState
        <hazard>:
            layer: str
            depth: int
            height: int
            position: Position
            animation: AnimationState
            damage: 
                radius: int
                amount: int
                duration: int
        <collectable>:
            layer: str
            depth: int
            height: int
            position: Position
            animation: AnimationState
            loot: str
        <interactable>: 
            layer: str
            depth: int
            height: int
            position: Position
            animation: AnimationState
```

##### Tasks

**1. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO

**2. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO