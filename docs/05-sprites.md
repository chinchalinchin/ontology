# Ontology: Sprites

Everything that is rendered in Ontology is an Asset. Therefore, Sprites are Assets. Sprites, unique in their deployment, are the most important Asset to the gameplay loop, as the gameplay loop can be understood mainly as a medium for the Sprite states to interact and react to one another and the Player's presence. 

!!! note
    The Player state does not observe the Disposition transition matrix; the Player state is entirely altered by polling the user's input and mapping input to Instructions. See [Player documentation](./06-player.md) for more information.
    
- AssetKey: `str`

**State**

- Name: `str`
- Position: `Tuple[int, int]`
- Layer: `str`
- Intention: `Dict[str, str]`
- Mutators: `Dict[str, Dict[str, Union[int, double, bool]]]`

## Mutators

*Mutators* are attributes that alter Sprite behavior.

### Triggers

- `dead.triggered`: Triggered if a Sprite dies.
- `struck.triggered`: Triggered if a Sprite collides with a hitbox.
- `frightened.triggered`: Triggered for the logical disjunction of the following conditions:
    - Triggered if Sprite's health dips below `frightened.limit`
    - Triggered if Sprite is surrounded by more than `frightened.enemy` enemies with the pixel distance of `frightened.radius`.

### Mutator Paramaeters

- `frightened.radius`: Radius of separation within which the Sprite triggers the `frightened` mutator. Measured in pixels.
- `frightened.limit`: Percentage of health below which Sprite triggers the `frightened` mutator.
- `frightened.enemy`: Number of enemies within the `frightened.radius` that must be present to trigger the `frightened` mutator.

## Intentions

*Intentions* are an internal State data structure that determines and governs a Sprite's core logic. The two most basic Intentions, Direction and Action, determine the current animation of the Sprite. All Sheet assets are given an Intention state with Direction and Action that is updated by the gameplay loop when deployed. Sprites, however, have a more complex Intention state, which provides a greater variety of behavior and possibility of emergent gameplay.

### Dispositions

A Sprite's *Disposition* determines its State Transition matrix, covered below. Dispositions are configurable, but since they are an essential piece of gameplay data, a default Disposition configuration has been provided. The default Dispositions are enumerated below,

1. `attack`
2. `attract`
3. `barter`
4. `escape`
5. `find`
6. `follow`
7. `idle`
8. `interact`
9. `loot` 
10. `mock`
11. `recoil`
12. `return`
13. `threaten`
14. `wander`

**Default Disposition Tree**

```yaml
--8<-- "docs/.static/yaml/examples/default-disposition-tree.yaml"
```

### Memory

- `target`: 
    - `category (chest | crate | plate | gate | door | sprite | pixie)`: Category of Sprite's current target.
    - `name`: Identifier of Sprite's current target.
- `communications`: List of dialogue saved in Sprite's memory.