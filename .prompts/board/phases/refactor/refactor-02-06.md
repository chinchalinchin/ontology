#### Refactor: Phase 02.06 - Effects

**Goals**: Refactor the Effect Asset.

##### Anaylsis

###### Effect Assets

After examination of the available Effect assets, there appears to be ambiguity in how the specifications relate to the physical asset files. From inspection, logical groupings seem to exist that should be codified. 

All Effect frame indexing can continue utilize the existing `IterableFrame`, as none of the architectural shifts should affect the underlying image files. Rather, the goal is divide Effects into their logical units based on common behavior.

The partitioning of Effects appears to be along two major categorical axes:

- The *type* of animation: `temporary`, `continuous` and `periodic`.
- The *function* of the Effect: `passive`, `collectable`, `hazard` and `interactable`

**Classification**

This is a list of some of the available Asset files, and the proposed categorization,

- Lava: `continuous`, `hazard`
- Spinning Dummy: `temporary`, `interactable`
- Floor Spike: `periodic`, `hazard`
- Coin: `continuous`, `collectable`
- Grandfather Clock: `continuous`, `passive`
- Water Ripples: `continuous`, `passive`
- Magic: `temporary`, `hazard`
- Bomb: `temporary`, `hazard`
- Rain: `periodic`, `passive`
- Candle: `continuous`, `passive`
- Torch: `continuous`, `passive`
- Birdbath: `periodic`, `passive`
- Furnance: `continuous`, `interactable`
- Chemistry Set: `temporary`, `interactable`
- Falling Leaves: `periodic`, `passive`

!!! note
    Not all Temporary effects should be garbage collected.

There are more, but they all appear to fall into the categorical scheme.

###### Effect Schema Updates

**EffectProperties**

Properties require minimal changes. Optional hitboxes and mass will need added to account for the `interactable` and `collectable` instances of Effects.

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
```

**Effect Animations**

- `temporary`: Ephemeral effects that halt once they reach the `count`.
    - `if state.animation.frame =< properties.count: state.animation.frame += 1`
- `continuous`: Perpetual effects that never stop iterating over their animation frames. 
    - `if state.animation.frame >= properties.count: state.animation.frame = 0`
- `periodic`: Perpetual effects that periodically repeat their animation frames.
    - `if state.animation.frame < properties.count: state.animation.frame += 1`
    - `if state.animation.frame >= state.frequency: state.animation.frame = 0`

**Effect States**

- PassiveState: Default Effect state. Has no attributes beyond what is necessary to achieve instantiation and animation in the game.
- HazardState: Effect Animations that represent environmental hazards (lava, poisonous gas, rushing water, etc.). When Sprite enter into the Effect's area, they suffer `effect.state.damage`.
    - `damage`:
        - `amount`: Amount of health deducted each `duration`
        - `duration`: How quickly the `amount` is applied to the Sprite.
        - `effect (hinder | bounce)`: Key to determine intersection effects of Hazard, e.g. whether the Sprite's movement is hindered (slowed down) or bounced (jolted away from the Hazard bounds)
- CollectableState: Effect Animations that represent collectable items (spinning coins, bubbling potions, etc.) to be added to `sprite.state.inventory.loot`. Produced when a Sprite in the `mine` Intention acts on a Resource (Resources not yet implemented). When Collectables are collected by a Sprite, they are instantly garbage-collected from the board.
    - `loot`: Loot inventory key received upon intersecting the Effect's hitbox.
- InteractableState: Effect Animations that are triggered when a Sprite within `action` radius of the Effect enters into the preqrequisite `effect.state.action`. 
    - `action`: Action which triggers the animation, e.g. (`cast`, `slash`, `thrust`, `shoot`).

```yaml
objects:
    effects:
        <passive-id>:
            layer: str
            depth: int
            height: int
            frequency: int
            position: Position
            animation: AnimationState
        <hazard-id>:
            layer: str
            depth: int
            height: int
            frequency: int
            position: Position
            animation: AnimationState
            damage: 
                amount: int
                duration: int
                reaction: str
        <collectable-id>:
            layer: str
            depth: int
            height: int
            frequency: int
            position: Position
            animation: AnimationState
            loot: Loot
        <interactable-id>: 
            layer: str
            depth: int
            height: int
            frequency: int
            position: Position
            animation: AnimationState
            action: Actions
```

**Problem**: in current setup, each instance has a determinate state, frame and animation. In other words, the current setup does not support a `<hazard-id-1>` having a TemporaryAnimation and a HazardState, while `<hazard-id-2>` has a ContinuousAniamtion and a HazardState; all instances with a HazardState must have the same Animation implementation. 

The obvious solution is create instances for each permutation of HazardPeriodic, HazardContinuous, HazardTemporary, etc. Doing so, however, is not very Pythonic or DRY. 

Anaylze the problem of Effect Assets.

##### Tasks

**1. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO

**2. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO