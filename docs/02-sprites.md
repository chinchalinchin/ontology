# Ontology Docs: Sprites

Everything that is rendered in Ontology is an Asset. Therefore, Sprites are Assets. Sprites, however, unique in their deployment, are the most important Asset to the game and thus have many unique attributes and methods; the gameplay loop can be understood mainly as a medium for the Sprite states to interact and react to one another, the Player included. 

## Specification: Sprites

### Category: Sheets

* Property File: `/src/assets/sheets/**/*.yaml`

See [Sheets](./01-assets.md#category-sheets) for a complete description of the Asset Category.

#### Sheet: Sprite

**State: SpriteState**

* `position: Position`
* `velocity: Velocity`
* `layer: str`
* `intention: Intentions`
* `character: Character`
    * `strength: int`
    * `defense: int`
    * `speed: int` (Maximum magnitude of Velocity vector)
    * `impulse: int` (Amount of acceleration applied to Velocity per game-tick)
* `animation: AnimationState`
    * `action: str`
    * `direction: str`
    * `frame: int`
* `slots: Slots`
    * `equipment: Equipment`
        * `armor: ArmorPalette`
        * `weapon: WeaponPalette`
        * `tool: ToolPalette`
        * `utility: UtilityPalette`
        * `shield: ShieldPalette`
    * `grip: Grip`
        * `left: Optional[ItemPalette]`
        * `right: Optional[ItemPalette]`
* `inventory: Inventory`
    * `bag: List[UtilityPalette]`
    * `belt: List[ToolPalette]`
    * `sheathe: List[WeaponPalette]`
    * `pouch: Dict[ItemPalette, int]`
    * `pack: Dict[MaterialPalette, int]`
    * `sack: Dict[CropPalette, int]`
* `meters: Meters`
    * `health: Meter`
        * `current: int`
        * `maximum: int`
    * `magic: Meter`
        * `current: int`
        * `maximum: int`
* `mutators: Mutators`
    * `triggers: MutatorTriggers`
    * `parameters: MutatorParameters`
* `memory: Memory`
    * `doors: Dict[str, str]`
    * `goals: Dict[str, Goal]`
    * `relationships: Dict[str, str]`
    * `prices: Dict[str, float]`
    * `property: Dict[str, Position]`
    * `sprites: Dict[str, Position]`
    * `rumors: List[str]`
* `psyche: Psyche`
    * `dialogue: str`
    * `expression: AttachmentState`
    * `motivation: Motivations`
    * `persona: str` (*Key for [Library](./08-narratives.md#service-library) dialogue retrieval*)
* `goal: Goal`
    * `name: str`
    * `layer: str`
    * `category: Goals`
    * `position: Position`
* `trajectory: Trajectory`
    * `target: Position`
    * `vertices: List[Position]`
    * `stalled: bool`
    * `cooldown: int`

**Animation: SpriteAnimation**

* `state.animation.frame += 1`
* `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`
* `state.psyche.expression.ttl -= 1`

**Frame: SpriteFrame**

* `keys(id, state): returns [ ("{id}-{state.animation.action}-{state.animation.direction}-{animation.frame}", 0, 0) ] + [ (<equipment-frames>, 0, 0) ] + [ (<expression-frames>, offset.x, offset.y) ]`
* `index(self, id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**Hitbox: StaticHitbox**

* `get(properties, state, frame): returns properties.hitboxes`

##### Field: Intention

Intentions are an internal State field that governs a Sprite's core logic. 

See [Intentions documentation](./04-intentions.md) for more information.

##### Model: Goal

Goals are the current focus of the Sprite's path-finding and Direction resolution.

See [Goals documentation](./04-intentions.md) for more information.

##### Model: Trajectory

Sprite Pathfinding is managed via its Trajectory. When a direct line of sight to a  Goal is blocked, [NavigationMechanics](./05-mechanics.md#mechanics-intentional) executes an [Rapidly-exploring Random Tree pathfinding routine](./12-architecture.md#math) and populates the trajectory buffer:

* `target`: The immediate physical coordinate $(x, y)$ that [MotionMechanics](./05-mechanics.md#core-mechanic-motionmechanics) steers toward on the current tick. If line of sight to the Goal is clear, then the Sprite steers directly towards its Goal. If the line of sight is blocked, then the Sprite iterates over the `vertices` in its Trajectory.
* `vertices`: The FIFO queue of intermediate RRT coordinates, adjusted for sensory anchor displacement.
* `stalled`: Boolean flag set when RRT fails to resolve a valid route, signaling deliberative systems of an impassable obstruction.
* `cooldown`: Tick accumulator enforcing a backoff interval before retrying path generation against impassable geometries.

Sprite Trajectories are managed by the [NavigationMechanics](./05-mechanics.md#intentional-mechanic-navigationmechanics).

##### Model: Meters

Every Meter has a `current` value and a `maximum` value.

**Field: Health**

Represents the Sprite's current and potential "*life*".

**Field: Magic**

Represents the Sprite's current and potential capacity for "*magic*"

##### Model: Character

**Field: Strength**

TODO

**Field: Defense**

TODO

**Field: Speed**

Speed determines the maximum magnitude of a Sprite's Velocity vector.

**Field: Impulse**

Impulse determines the rate of change of a Sprite's Velocity vector.

##### Model: Mutators

Mutators are attributes that alter Sprite behavior. They are functions of the Sprite's state, i.e. they are calculated from state attributes, not *primitive* state attributes themselves.

**Behavior: Conditionality**

Mutators are *condition-driven*. They may also be *parameterized*; In other words, all Mutators are *conditional* but not all Mutators are parameterized. Parameters modulate the conditions underlying the Mutator calculation. 

* Parameterized Mutators: `fear`, `vision`, `action`, `hand`, `squeeze`, `community`
* Conditional Mutators: `animated`, `dead`

**Fields: Triggers**

* `trigger.action`: Triggers if a Sprite is within acting distance of its Goal.
* `trigger.animated`: Triggered if a Sprite is currently able to animate, i.e. alter its AnimationState. When this Mutator trigger is false, the Sprite does not receive animation updates from the game loop.
* `triggers.dead`: Triggered if a Sprite dies. This can only occur if the Sprite's `meters.health.current == 0`
* `triggers.fear`: Triggered for the logical disjunction of the following conditions:
    * Triggered if Sprite's health dips below `fear.limit`
    * Triggered if Sprite is surrounded by more than `fear.enemy` enemies with the pixel distance of `fear.radius`.
* `triggers.submerged`: Triggered when the entity's footprint intersects an active Fluid stream or pool without being aboard a Raft or Bridge. When active, `Screen.draw` renders a semi-transparent water tint over the lower half of the Sprite, and `Cradle` dispatches a temporary `splash` effect.
* `triggers.vision`: Trigger if a Sprite is within visible distance of its Goal.

**Fields: Parameters**

* `parameters.fear`:
    * `radius`: Radius of separation within which the Sprite triggers the `triggers.fear` mutator. Measured in pixels.
    * `limit`: Percentage of health below which Sprite triggers the `triggers.fear` mutator.
    * `enemy`: Number of enemies within the `parameters.fear.radius` that must be present to trigger the `triggers.fear` mutator.
* `parameters.vision`:
    * `radius`: Radius of separation within which the Sprite triggers the `triggers.vision` mutator. Measured in pixels.
* `parameters.action:`
    * `radius`: Radius of separation within which the Sprite triggers the `triggers.action` mutator. Measured in pixels.
* `parameters.squeeze`:
    * `radius`: Buffer radius used for avoiding obstacles during path-finding.
* `parameters.community`: 
    * `radius`: Radius used for [Town Formation Mechanics](./11-emergence.md#towns).
* `parameters.hand`: Active hand (`left` or `right`) parameterizing the `use` Intention to resolve the corresponding item in `slots.grip`.

##### Model: Animation

Animations are tuples of (Action, Direction, Frame). Action and Direction were previously defined in the [Assets documentation](./01-assets.md#category-sheets).

##### Model: Psyche

The *Psyche* is an internal State data structure that governs a Sprite's ancillary Animation and Intention logic. All Sprite Assets besides the Player are given a Psyche State when deployed onto the Board. Psyche coordinates encode alterations and modulations of the Sprite State. The complete Psyche state for a Sprite is given by the tuple,

$$
(\text{Dialogue}, \text{Persona}, \text{Expression}, \text{Motivation})
$$

**Field: Dialogue**

The Dialogue dimension of a Sprite's Psyche can be thought of as the short-term memory or a buffer for dialogue the Sprite is about to transmit. This field holds the lexicon key that will be exchanged at the [Library](./08-narratives.md#library) for content and rendered in a [Dialogue Menu](./06-widgets.md#menu-data) if the Player enters into the `speak` Intention with the Sprite. 

In addition, Sprites may enter into `speak` Intentions with other Sprites, but these events are not routed to [Menus](./06-widgets.md#configuration-menus). Instead, Sprite-to-Sprite Dialogue is used by the [RumorMechanics](./05-mechanics.md).

**Field: Persona**

A Sprite Persona is a data structure used to index Dialogue to a Sprite through the [Library](./08-narratives.md#library). It can be thought of as the "*personality*" of the Sprite.

**Field: Expression**

Expressions alter the Sprite's appearance by appending a [Cursor Expression](./01-assets.md#cursor-expressions) to the upper right corner of the Sprite's boundaries. Expressions can be visualized as speech bubbles containing symbols that express the Sprite's internal State. 

Expressions possess a strict Time-To-Live (TTL) dictating their visual duration. This decay is managed by the Sprite [Animation](#model-animation), decoupled from the Sprite's internal State or [Mechanics](./05-mechanics.md). 

This separation of concerns ensures that a Sprite can visually retain a psychological state (e.g., lingering `confusion` from a lost target, or `loquacity` after being interrupted) even as it physically transitions between distinct Actions, such as snapping from `speak` to `idle` or `escape`. 

Furthermore, the visual expiration of an Expression does not inherently nullify underlying drivers like `psyche.dialogue`. If a speech bubble fades before a `subject` [Goal](#model-goal) is satisfied, the Sprite's intentional logic remains intact, i.e. the Sprite will continue pursuing its Goal, even as its loses sight of the Player.

**Semantics: ExpressionPalette**

* `agreement`, `anger`, `confusion`, `curiosity`, `disagreement`, `loquacity`, `surprise`, `tired`

**Field: Motivation**

Motivations are long-term state variables that are used to modulate the [Intention Transition matrix](./04-intentions.md). 

**Semantics: Motivations**

* `conquest`, `profit`, `survival`, `love`, `revenge`, `rebellion`, `safety`

##### Model: Memory

*Memory* stores episodic and relational data while the Sprite's active [Goal](#model-goal) focuses elsewhere:

* `memory.goals: Dict[str, Goal]`: Episodic store of true strategic [Goals](#model-goal). Keyed by the Asset `name`. Strategic memory stores no intermediate [Trajectory](#model-trajectory) waypoints.
* `memory.sprites: Dict[str, Position]`: Map of last-known Sprite locations keyed by Asset `name`.
* `memory.doors: Dict[str, str]`: Map of [Doors](./01-assets.md#object-doors) the Sprite has used, keyed by `name`.
* `memory.prices: Dict[str, Dict[str, float]]`: Subjective Sprite valuations for [Inventory](#model-inventory).
* `memory.property: Dict[str, Position]`: Locations of Sprite-owned structures, keyed by `name`.
* `memory.relationships: Dict[str, Relationships]`: Sprite social relationships, keyed by `name`.
* `memory.rumors: List[str]`: Lexicon dialogue keys received via conversation.

**Semantics: Relationships**

* `friend`, `family`, `foe`, `stranger`

**Field: Prices**

Sprites keep a dictionary keyed by Inventory Slot and Key for the Inventory's associated value, known as Prices. This distionary represents the Sprite's "*belief*" regarding the fair value of its Inventory when engaging in the `barter` [Intention](./04-intentions.md). This dictionary only has new keys appended when the Sprite acquires a new item in its Inventory, e.g. the Sprite doesn't have "initial" Prices.

**Behavior: Price Discovery**

When two Sprites enter the `speak` Intention within a certain radius of each other, the `SpeechMechanic` does the following:

1. It averages the intersection of Prices. For example, if one Sprite has a price of 1 for Loot A and another has a price of 5 for Loot A, then the new price of Loot A for both Sprites will be (1 + 5)/2 = 3. It performs this calculation for every such Loot Key the Sprites have in common.
2. For each Sprite A and Sprite B, the prices of A subtracted (in the set-theoretic sense) from the prices of B is added to A and visa versa. In other words, if a Sprite converses with another Sprite that has Price information it does not possess, the `SpeechMechanic` will populate the Sprite's Prices.

**Field: Property**

A Sprite can acquire property through the `build` [Intention](./04-intentions.md). When a Sprite creates a [Strut](./03-compositions.md#craft-struts), the location of that Strut is stored in `memory.property`, keyed to the name of the Strut Asset.

**Field: Rumors**

TODO

##### Model: Slots

Slots represent the active (ready-at-hand) Inventory currently wielded or worn by a Sprite or Playerl

$$
(\text{Equipment}, \text{Grip})
$$

**Fields: Equipment**

Active pieces of [Equipment](#instance-equipment) injected into Sprite Frame.
* `armor`: (*Gear*) Passive defense.
* `shield`: (*Gear*) Active blocking (`intention = block`).
* `weapon`: Active combat (`intention = attack`), equipped from `inventory.sheathe`.
* `tool`: Active harvesting (`intention = mine`), equipped from `inventory.belt`.
* `utility`: Persistent environmental and character effects, equipped from `inventory.bag`.

**Fields: Grip**

Active usable items drawn from the [Pouch](#field-inventory)

* `left`: Usable item (`intention = use`, `mutators.parameters.hand = left`).
* `right`: Usable item (`intention = use`, `mutators.parameters.hand = right`).

##### Model: Inventory

The Inventory represents items and content the Sprite has "*on its person*", but is not currently slotted. In other words, Inventory is *storage*. 

The Inventory is partitioned into containers for Inventory that only has a single instance, known as *Gear*, and containers for Inventory that can be accumulated, e.g. Crops, Materials, etc. 

The diagram below shows the mapping between Slots and Inventory fields.

--8<-- "static/mmd/sprite-inventory.mmd"

$$
\Big((\text{Bag}, \text{Belt}, \text{Sheathe}, \text{Pouch}, \text{Pack}, \text{Sack}\Big))
$$

**Field: Bag**

Container for Utilities , slottable into `slots.equipment.utility`.

**Field: Belt**

Container for Tools, slottable into `slots.equipment.tool`.

**Field: Pouch**

Container for Items, slottable into `slots.grip.left` and `slots.grip.right`.

**Field: Pack**

Container for Materials.

**Field: Sack**

Container for Crops.

**Field: Sheathe**

Container for Weapons, slottable into `slots.equipment.weapon`.

#### Sheet: Equipment

Equipment is a grouping of several [Sheet Instances](./01-assets.md#category-sheets) that share the common feature of having no [State](./00-overview.md#core-state). Instead, their rendering is dependent on a Sprite State. Equipment is not an Asset Category in and of itself, but a label applied to particular Instances of Sheets in the Hierarchy. 

*Equipment: Armor, Tools, Utilities, Weapons, Shields

!!! important "Equipment Sheet Specification"
    It assumed Equipment Sheets conform to the same (Action, Direction) grouping utilized by the [Sprite Sheet](./01-assets.md#category-sheets) equipping it. In other words, the frames coordinates and dimensions in an Equipment Sheet must correspond exactly to frames in a Sprite Sheet. This does not mean Equipment frames may not be present in every frame, but rather what is present must conform to the schema. For example, the `longbow` only occupies the `(shoot, *)` rows of a Sheet, while all other rows of the `longbow` Asset file are blank.

##### Equipment: Frame

Equipment is a stateless Sheet Asset. It is not deployed onto the Board in a fashion like other Assets. Instead, only Properties and Frames are supplied for Equipment, i.e. Equipment has a Frame Recipe. This allows the Registry to index and load all Equipment Sheets. However, since Equipment does not possess a State, it is not instantiated by the [Application](./00-overview.md#application) when the State directory is traversed during the [bootstrapping](./12-architecture.md#specification-initialization). Instead, Equipment Frame keys are generated by SpriteFrames when Sprites have Equipment slotted into their `sprite.state.inventory.equipment`, e.g.

```yaml
# /src/data/state/<board-key>/sheets.sprites.state.slots: 
equipment:
    armor: plate
    tool: shovel
    utility: lantern
    shield: buckler
    weapon: dagger
```

When this Sprite's Frame `keys()` interface is called, it will return a list of Frame keys that include Equipment Frame keys. The Screen will then retrieve each of these keys from the Registry and render them in the order they were received, thus stacking the Equipment on top of the Sprite that is equipping it.

**Frame: StateFrame**

!!! important "Equipment Frame Indexing"
    Equipment must utilize the StateFrame to get indexed by the Registry.
    
* `keys(id, state): returns [ ("{id}-{state.animation.action}-{state,animation.direction}-{state.animation.frame}", 0, 0) ]`
* `index(id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

##### Equipment: Animation

When Equipment is configured in the Sheet Property index file, the Equipment `actions` property determines which Actions in a Sprite's state will result in extra Frame Keys being appended to the `keys()` return result. 

Equipment is divided in four kinds: Armor, Tools, Utilities and Weapons. Each Kind modifies the gameplay in different ways. Just as active Equipment affects the Frame Keys returned by a Sheet Asset, it also affects State transitions. When a piece of Equipment is active, it directly determines which Animation Action state are enterable from the `attack` Intention (or the `build` Intention, etc.). The translation between [Intention](./04-intentions.md) and Equipment into Animation is achieved through an [AnimationMap](./04-intentions.md#animationmap)

```python
sprite.state.animation.action = AnimationMap.action(
    sprite.state,
    board.equipment
)
```

!!! note "Equipment"
    Equipment Properties are stored in the [Board](./00-overview.md#component-board) database, *not* the Sprite Asset.

#### Sheet: Player

A Player is a special type of Sprite Sheet. It may be thought of as a "*pseudo*"-Asset. It has no Properties that differentiate it in the Hierarchy; Instead, it utilizes Sprite Sheet properties. However, it is differentiated by having a unique [State](./00-overview.md#core-state) and isolated [Intention](./04-intentions.md) management Mechanics. 

The Player Sprite Sheet is configured through the `player` Sprite Sheet. 

!!! important "Player Required"
    The `player` Sprite *must* be defined in `/src/assets/sheets/main.yml#sprites`.

**State: PlayerState**

* `position: Position`
* `velocity: Velocity`
* `layer: str`
* `meters: Meters`
* `character: Character`
* `animation: AnimationState`
    * `action: Actions`
    * `direction: Direftions`
    * `frame: int`
* `goal: Goal`
* `intention: Intentions` 
* `slots: Slots`
* `inventory: Inventory`

!!! note "PlayerState vs. SpriteState"
    The PlayerState is a *truncated* SpriteState, i.e. it lacks the complex data structures for managing its `intention`.

##### Field: Player Goals & Intentions

Players utilize the same information channel (e.g. Goals and Intentions) as Sprites for communicating state changes.

* **Goals (Level-Triggered & Polymorphic):** Players use a "pseudo" Goal to project their input into their intended direction of motion. Multiple directional inputs can overlap simultaneously (e.g., `UP` and `RIGHT`) and are accumulated as a list to allow for diagonal vector movement. This determines the direction of the Player's Velocity in their [kinematic sliding](./05-mechanics.md#core), i.e. $\text{player.velocity} \parallel \text{player.state.goal.position} - \text{player.state.position}$.
* **Intentions (Edge-Triggered & Singular):** Unlike Goals, Intentions represent discrete state transitions. The hardware polling layer enforces a strict singularity rule: overlapping Intention inputs are collapsed into a single scalar value based on configuration order. This acts as a blocking mechanism, preventing impossible state superpositions (e.g., trying to `build` and `attack` simultaneously).

## Devices

The [Board](./00-overview.md#component-board) contains a Device, which polls for user input. The Device uses a Mapping to translate the polling data into a structured `DevicePayload`, resolving hardware inputs based on their discrete or continuous nature. The [Mapping Configuration](./appendices/01-schemas.md#configuration-mapping) file provides a translation key between input state and game state.

**Keyboard**

The input state of the Keyboard is polled through SDL. Keyboard mappings correspond to SDL scancodes. See [SDL documentation](https://wiki.libsdl.org/SDL2/SDL_Scancode) for more information.

### Device: Contexts

The Device class implements a stateful context flag (`world`, `menu`). Each Device mapping includes a nested mapping for each separate context, which strictly segregates the resulting `DevicePayload`:

* `world`: Resolves a World Payload containing a singular Intention, a singular Grip trigger (`left` or `right`, which defaults `intention` to `use` and sets `mutators.parameters.hand`), a singular Menu trigger (`pause`, `equipment`, `pouch`, `pack`, `trade`), and a polymorphic list of Goals.
* `menu`: Resolves a Menu Payload containing a singular Traversal direction and a singular Interaction.

When the [Board](./00-overview.md#component-board) Menus are populated, [MenuMechanics](./05-mechanics.md#core-mechanic-menumechanics) toggles the device context to `menu`, ensuring the [SDL polling](./12-architecture.md#specification-cython-libraries) only evaluates and returns Menu commands.