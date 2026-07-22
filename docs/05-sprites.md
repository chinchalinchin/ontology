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
- Mutators:
    - Triggers: `Dict[str, bool]`
    - Parameters: `Dict[str, Dict[str, Union[int, double]]]`
- Memory: `Dict[str, Any]`
- Goal: `Dict[str, Any]
- Frame: `int`

Frame is an integer that tracks the current animation frame. It's maximum value is dependent on the Action state. For example, if a Sprite is in the `walk` Action state, then Frame will cycle from 0 to `walk.MaxFrames`.

**Calculated State**

- FrameKey: `AssetKey + Intention.Direction + Intention.Action + Frame`

## Mutators

*Mutators* are attributes that alter Sprite behavior. They are functions of the Sprite's state, i.e. they are calculated state attributes, not *primitive* state attributes.

### Triggers

- `trigger.animated`: Triggered if a Sprite is currently animate. When this is false, the Sprite does not receive animation updates from the game loop, e.g. if the user releases the right arrow key on the keyboard, leaving the Player in a `(walk, right)` state, then this mutator prevents the animation from progressing.
- `triggers.dead`: Triggered if a Sprite dies.
- `triggers.struck`: Triggered if a Sprite collides with a hitbox.
- `triggers.frightened`: Triggered for the logical disjunction of the following conditions:
    - Triggered if Sprite's health dips below `frightened.limit`
    - Triggered if Sprite is surrounded by more than `frightened.enemy` enemies with the pixel distance of `frightened.radius`.

### Paramaeters

- `parameters.frightened.radius`: Radius of separation within which the Sprite triggers the `triggers.frightened` mutator. Measured in pixels.
- `parameters.frightened.limit`: Percentage of health below which Sprite triggers the `triggers.frightened` mutator.
- `parameters.frightened.enemy`: Number of enemies within the `parameters.frightened.radius` that must be present to trigger the `triggers.frightened` mutator.

## Intentions

*Intentions* are an internal State data structure that determines and governs a Sprite's core logic. The two most basic Intentions, Direction and Action, determine the current animation of the Sprite. All Sheet assets are given an Intention state with Direction and Action that is updated by the gameplay loop when deployed. Sprites, however, have a more complex Intention state, which provides a greater variety of behavior and possibility of emergent gameplay.

The default Actions and Directions for the LPC specification are,

- Actions: `cast, thrust, walk, slash, shoot, die`
- Directions: `up, down, left, right`

The complete Intention State for a Sprite is given by the tuple,

    (Action, Direction, Extension, Disposition, Communication, Goal)

!!! note 
    In the LPC specification, the `thrust` Action plays double-duty for spears and shovels. The spear is a Weapon, whereas the shovel is Equipment. With LPC assets, the animations of these pieces of Equipment is governed by the `thrust` state.

### Extension

A Extension is a pseudo-state that does not factor into the Asset frame key calculation directly. It may indirectly alter the Sprite (Action, Direction) transitions or other properties of the Sprites, e.g. entering into the `sprint` Extension state increases the velocity of the `(walk, *)` states, but does not factor into the animation speed. Similarly, entering into the `interact` Extension state does not alter the Sprite's current animation in a way, but instead allows the Sprite to open a Chest or Door, for example.

### Disposition

A Disposition determines which Actions are currently reachable for a Sprite. In other words, a Sprite's *Disposition* determines its State Transition matrix, covered below. Dispositions are configurable, but since they are an essential piece of gameplay data, a default Disposition configuration has been provided. The default Dispositions are enumerated below.

1. `attack`
    - Reachable Actions: `cast, thrust, slash, shoot`
2. `attract`
    - Reachable Actions: `walk`
3. `barter`
    - Reachable Actions: None
4. `escape`
    - Reachable Actions: `walk`
5. `find`
    - Reachable Actions: `walk, thrust`
6. `follow`
    - Reachable Actions: `walk`
7. `idle`
    - Reachable Actions: `walk`
8. `interact`
    - Reachable Actions: None
9. `loot` 
    - Reachable Actions: None
10. `mock`
    - Reachable Actions: None
11. `recoil`
    - Reachable Actions: `die`
12. `return`
    - Reachable Actions: `walk`
13. `threaten`
    - Reachable Actions: None
14. `wander`
    - Reachable Actions: `walk`

**Default Disposition Tree**

```yaml
--8<-- "docs/.static/yaml/examples/default-disposition-tree.yaml"
```

**Dispositional Scripting**

The `condition` for each state transition is given 


###

asdf

## Memory

- `target`: 
    - `category (chest | crate | plate | gate | door | sprite | pixie)`: Category of Sprite's current target.
    - `name`: Identifier of Sprite's current target.
- `communications`: List of dialogue saved in Sprite's memory.