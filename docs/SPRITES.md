# Sprites

_Sprite_\s are complex.  By far, a _Sprite_ `stature` trajectory is the most complex data structure in the game, in terms of how it is processed and transformed over the course of a game loop iteration. In order to truly understand _onta_, you need to understand how a sprite `stature` interacts with the _World_ update method that is called each game loop.

So, with that mind, this section is dedicated to _Sprite_\s and understanding their various subtleties.  


## Sheets

You can find an example spritesheet layout in _/docs/assets/spritesheet_layout.xcf_, also shown below for reference,

![](TODO.png)

(Also TODO: provide link to xcf once hosted). 

However, the file itself contains more worthwhile information than is evident from the above picture. The _.xcf_ file has layers that provide details for various spritesheet properties, such as_Sprite_ `attackboxes` coordinates (which will be covered in later sections), row and frame coordinates, apparel coordinates, various accents and styles, etc.


## Frame

At any moment in time, a _Sprite_'s on-screen image can be resolved down into four main components that determine what rectangular area in a spritesheet is being used to represent the _Sprite_. There are other factors beyond these four core attributes, such as slotted _Equipment_ or _Armor_, but all other attributes that affect rendering are optional; every _Sprite_ rendering is dependent on the existence of atleast these four attributes. The values of these attributes, taken together, are a key used to retrieve the current _Sprite_ frame, i.e.,

```python
from onta.loader.repo import Repo

sprite_frame = Repo('/path/to/ontology').get_sprite_frame(
    sprite_key,
    stature_key,
    frame_index
    expression_key = None, # TODO: implement this
)
```

The `sprite_key` determines which spritesheets are pulled from the asset _Repo_ to form the character base. The `stature_key` and `frame_index` determines which row and column of the spritesheet is cropped to the _Sprite_'s position onscreen. The `expression_key` is an optional key that, if included, will render an _Expression_ atop the _Sprite_ frame.

## Stature

A _Sprite_ `stature` is part of the _World_'s dynamic state, meaning its value changes over the course of the game. `stature` itself is an object that can be described in terms of four subcomponents.

### Actions

A _Sprite_ `stature.action` describes what it is doing in the world. 

Five of the _Sprite_ `action`s, `cast`, `thrust`, `shoot`, `slash` and `shield`, are mapped to equipment _Slots_. When a _Sprite_ has an _Equipment_ equipped (_slotted_) to a _Slot_, this appends a spritesheet onto the existing spritesheets for a _Sprite_ and alters the engine calculations for player attack hitboxes and damage; When the player frame is rendered, the _Equipment_ frame will be rendered on top; when the player attacks, the _Equipment_ hitbox is appended to the player position. See [Configuration](./CONFIGURATION.md#equipment) for more information on _Equipment_ and _Slots_.

The other _Sprite_ `action`s, `use` and `interact`, do not map directly to an animate `stature`, meaning when the _Sprite_ `action` is set to this value, the _Sprite_ will not be animated on screen, but rendered at a static position. `stature`s without animation mapping are called _singular_ `stature`s.

**Values**: `cast`, `slash`, `thrust`, `shoot`, `shield`, `use`, `interact`

A comparison with the included spritesheet diagram shows an animate _Sprite_ `action` determines the grouping of rows in the spritesheet to use for the onscreen representation.

### Directions

A _Sprite_ `stature.direction` describes where sprite is facing or travelling.

**Values**: `up`, `down`, `left`, `right`, `up_left`, `up_right`, `down_left`, `down_right`

* Real Directions: The directions `up`, `down`, `left` and `right` are said to be _real_, because they map directly to row in the spritesheet.
* Composite Directions: The directions `up_left`, `up_right`, `down_left` and `down_right` are said to be _composite_, meaning these directions are accessible via keystroke combinations (in the case of the player, NPCs can also move in this directions, but it is slightly more complicated) and move the sprite in the indicated direction, but they do not map to rows in a spritesheet. In other words, `up_left` and `down_left` both use the `left` spritesheet frames, and `up_right` and `down_right` both use the `right` spritesheet frames.

### Expressions

A _Sprite_ `stature.expression` describes how a sprite "feels". To be more concrete, it affects which _Expression_ is rendered on top of the _Sprite_ frame. That cosmetic alteration belies a hidden complexity, though, as an _Expression_ is the result of calculations involving _Sprite_ `desires`, `plots` and their corresponding transformations relative to the current _World_ state. A _Sprite Expression_ is a dynamic property that symbolizes the internal mechanics of a _Sprite_, or atleast that is its intention.

**Values**: `anger`, `joy`, `sadness`, `love`, `hate`, `surprise`, `confusion`

### Intentions

In addition to the three main animate `stature` properties in a _Sprite_, there is another, hidden property that secretly drives the sprite animation. A _Sprite_ `intention` can be thought of a vessel that receives `intent` and once filled, continually updates the _Sprite_ `stature` until the `intention` is exhausted, at which point another `intent` will be inserted into the _Sprite_ `intention`. 

The `update()` method consumes a _Sprite_ `intent`, transforms it into an `intention` which then becomes a `stature` trajectory. This `intention` is the "motive" force propelling _Sprite_\s through their animate `statures`. 

The practical effect of `intention` is to collapse a _Sprite_'s animate `stature` into groups of similar operations. In order to generalize the _World_ `update()` method across player and non-player _Sprite_\s (NPCs), an _Intent_ provides a layer of abstraction on top of_Sprite_'s `stature`.

More information about `Intent`s is found in the sections below. 

**Values**: `move`, `combat`, `defend`, `use`, `interact`, `express`

## Intents

User input never directly touches a sprite `stature`. Instead, user input is mapped into an `intent`. Part of the _World_ `update()` is applying _Sprite_ `intent`s to change the world state, so, by necessity,  the player input must be injected into this loop as an `intent`. In other words, there is no inherent difference in how a player _Sprite_ and a non-playable _Sprite_ (NPC) have their `stature`s updated. Both will have `intents` that get consumed each iteration and are used to update their _Sprite_'s `stature`. The difference lies in how those `intent`s are generated. 

In the case of the player, as mentioned, user input is mapped to `intent`\s, but in the case of non-playable _Sprite_\s, new `intent`\s are transmitted to the _Sprite_ via its `desires` and their corresponding `conditions`. More information on `desires` can be found in the next section. 

`intents` are essentially instructions to change the _Sprite_ `stature`. As such, they look this,

```yaml
sprite_name:
    #...
    intent: 
        intention: intention_name
        action: action_name
        direction: direction_name
        emotion: emotion_name
```

**NOTE**: While this would be the theoretical data structure of an `intent`, `intent`s are not defined, configured or stored in any external file. They are generated in-game through either user input or _Sprite_ `desires` and never leave the memory. 

Each iteration of the _World_, a _Sprite_ `intent` is consumed and then processed into a new _Sprite_ `stature`. For example, if an `intent` has an `action` of `walk` and a `direction` of `up`, in the next _World_ iteration, the _Sprite_ will move one unit in the up direction (where one unit is defined in the _Sprite_'s `speed` configuration property). If a _Sprite_ has an `intent` with the `action` of `interact`, the _Sprite_ will enter into the `interact` `stature`. Note, `interact` does not have a direction associated with it due it being a "singular stature" (see above). Therefore, not all properties in an `intent` are necessarily defined. 
 
At the beginning of a new iteration, a _Sprite_ will require a new `intent` to consume. There is a constant generation and consumption of `intent`s underlying all _Sprite_ action (or inaction) in-game. Once a _Sprite_ exhausts its `intent`s and no new `intent`s are incoming, it is effectively "dead", insofar as the _Sprite_ itself is no longer able "animate itself". The _Sprite_ will be rendered as an artifact of its having a position, but it will no longer get animated or display motion. However, this does not mean the _Sprite_ is dead in-game. Any _Sprite_ with an in-game position is a possible object of another _Sprite_'s `desires`. In order to explain further, the notion of `desires` will need further elaboration.

## Desires

See [Plotting](./PLOTTING.md) for more information on `plots`.

## Path

## Memory

## Expressions

## Inspirations