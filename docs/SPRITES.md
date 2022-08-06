# Sprites

_Sprite_ are complex. By far, a _Sprite_ state trajectory is the most complex data structure in the game. So, with that mind, this section is about nothing but _Sprite_\s. 

At any moment in time, a _Sprite_ state can be resolved down into three main components that determine what animation is being used to represent the _Sprite_ onscreen. There are other factors beyond these three core attributes, such as slotted _Equipment_ or _Armor_, but all other attributes that affect rendering are optional; every _Sprite_ rendering is dependent on the existence of these three values. These three values, taken together, are essentially a key used to retrieve the current _Sprite_ frame, i.e.,

```python
from onta.loader.repo import Repo

sprite_frame = Repo('/path/to/ontology').get_sprite_frame(
    action_key, 
    direction_key,
    emotion_key
)
```

## Actions

A _Sprite_ `action` describes what it is doing in the world. 

Five of the _Sprite_ `actions`, (`cast`, `thrust`, `shoot`, `slash` and `shield`) are mapped to equipment _slots_. When a _Sprite_ has an _Equipment_ equipped to a _slot_ (slotted), this appends a spritesheet onto the existing spritesheets for a _Sprite_ and alters the engine calculations for player attack hitboxes and damage: When the player frame is rendered, the _Equipment_ frame will be rendered on top; when the player attacks, the _Equipment_ hitbox is appended to the player position. See [Configuration](./CONFIGURATION.md#equipment) for more information on _Equipment_.


**Values**: `cast`, `slash`, `thrust`, `shoot`, `shield`, `use`, `interact`

## Directions

A _Sprite_ `direction` describes where sprite is facing or travelling.

**Values**: `up`, `down`, `left`, `right`, `up_left`, `up_right`, `down_left`, `down_right`

## Emotions

A _Sprite_ `emotion` describes how a sprite "feels".

**Values**: `anger`, `joy`, `sadness`, `love`, `hate`, `surprise`, `confusion`


## Paths

## Intents

User input never directly touches a sprite state. Instead, user input is mapped into an _Intent_. Part of the _World_ update iteration is applying _Sprite_ _Intent_\s to change the world state information, and this process also by necessity handles the player input once its been mapped to an _Intent_. In other words, there is no inherent difference in how a player _Sprite_ and a non-playable _Sprite_ (NPC) have their statures updated. Both will have _Intents_ that get consumed each iteration and are used to update the _Sprite_ stature. The difference lies in how those _Intent_ are generated. 

In the case of the player, the _Intent_\s are mapped from user input, but in the case of the non-playable _Sprite_\s, new _Intent_\s are transmitted to the _Sprite_ via its _Desires_ and their corresponding `conditions`. 

_Intents_ are essentially instructions to change the _Sprite_ stature. As such, they look this,

```yaml
sprite_name:
    #...
    intent: 
        intention: intention_name
        action: action_name
        direction: direction_name
        emotion: emotion_name
```

**NOTE**: While this would be the theoretical data structure of an _Intent_, _Intent_\s are not defined or configured in any external file. They are generated in-game through either user input or _Sprite Desires_. 

Each iteration of the _World_, a _Sprite Intent_ is consumed. It will be processed into a new _Sprite_ stature. For example, if an _Intent_ has an `action` of `walk` and a `direction` of `up`, in the next world iteration, the _Sprite_ will move one unit in the up direction (where one unit is defined in the _Sprite_'s `speed` configuration property). If a _Sprite_ has an intent with the `action` of `interact`, the _Sprite_ will enter into the `interact` stature. Note, `interact` does not have a direction associated with it due it being a "singular stature" (see above). Therefore, not all properties in an `intent` are necessarily defined. 
 

Therefore, at the beginning of a new iteration, a _Sprite_ will require a new _Intent_ to consume. There is a constant generation and consumption of _Intent_\s underlying all _Sprite_ action (or inaction) in-game. Once a _Sprite_ exhausts its _Intent_\s and no new _Intent_\s are incoming, it is effectively "dead", insofar as the _Sprite_ itself is no longer able "animate itself". The _Sprite_ will be rendered as an artifact of its having a position, but it will no longer get animated or display motion. However, this does not mean the _Sprite_ is dead in-game. Any _Sprite_ with an in-game position is a possible object of another _Sprite_'s desires. In order to explain further, the notion of _Desires_ will need further elaboration.

### 

## Desires

See [Plotting](./PLOTTING.md) for more information on _Plots_.

## Expressions

## Inspirations