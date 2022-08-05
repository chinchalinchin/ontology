# Sprites

_Sprite_ are complex. By far, a _Sprite_ state trajectory is the most complex data structure in the game. So, with that mind, this section is about nothing but _Sprite_\s. 

## States

_Sprite_\s have states. Different states means different things, in terms of how they get interpretted by the engine, and thus it's possible for slightly different initial states to produce radically different outcomes (<sup><sub>otherwise known as a [singular perturbation](https://en.wikipedia.org/wiki/Singular_perturbation)</sup></sub>). Because of this complexity, we will be as precise as possible in defining what is meant by a _Sprite_ state in this section, in the hopes that everything else in other section is clearer for it.

A _Sprite_ state can be grouped into _animate_ and _null_ (or _inanimate_) states. _Animate_ states have a _frameset_ associated them, which the engine uses to animate that _Sprite_. _Null_ states do not affect the content of the _frameset_ animation, although they may alter its rendering options; for instance, when jumping, the sprite has its frame margins shifted and a shadow painted underneath it, without altering which _frameset_ is being iterated.

A _Sprite_ has twenty-one _animate_ state and four _null_ states.

An _animate_ _Sprite_ state is composed of an _action_ and a _direction_. The _direction_ of a state maps one-to-one to the direction keys the player uses for input (one-to-one, ignoring the diagonal directions, which produce diagonal movement but use the _left_ and _right_ direction state frames for animation, so for all intents and purposes, these directions can be ignored in what follows), whereas an _action_ is mapped to the secondary controls, such as `CTRL`, `SHIFT`, swiping or widgets on a touch screen.

A _Sprite_ has four directions: `left`, `right`, `up`, `down`.

A _Sprite_ has five actions: `cast`, `thrust`, `slash`, `shoot`, `walk`

The cross of these two sets, _(action, direction)_, yields 20 distinct states. In addition to this cross product, there is one more _animate_ state: `death`. `death` has no direction. It is always rendered head-on.

In addition to these 21 _animate_ states, there exists four _null_ states: `interact`, `jump`, `shield`, `use`. _null_ states do not map to frames and thus do not signify any sort of animation.

Another complexity that arises is the `run` state. The `run` state is distinct from the other states in the sense a sprite cannot enter into the `run` state without exiting its prior state. In other words, technically, there are **25** _animate_ states, but since `run` is simply a sped up version of the `walk` state, `run` shares state frames with `walk` and is essentially a _special_ "mode" of `walk`; it is typically ignored as its own distinct state.

_Sprite_ _action_ states (`cast`, `thrust`, `slash`, `shoot`, `walk`) are mapped to equipment _slots_. When a _Sprite_ has an _Equipment_ equipped to a _slot_, this appends a spritesheet onto the existing spritesheets for a _Sprite_ and alters the engine calculations for player attack damage in that state. When the player is rendered, the equipmentsheet will be rendered on top of him or her.

See [Configuration](./CONFIGURATION.md#equipment) for more information on _Equipment_.

## Paths

## Intents

User input never directly touches a sprite state. Instead, user input is mapped into an _Intent_. Part of the _World_ update iteration is applying _Sprite_ _Intent_\s to change the world state information, and this process also by necessiry handles the player input once its been mapped to an _Intent_. 

In addition to _Intent_\s that map directly to user input, there are also _Intent_\s that describe how non-playable character _Sprite_\s states evolve. Take note, there is no inherent difference in how an _Intent_ modifies a _Sprite_, whether its an NPC or the player, *but* there are certain _Intent_\s that are never applied to the player sprite. This will become clear as an _Intent_ is more carefully defined.

Each _Intent_ is described by a combination of the properties: `plot`, `mode`, `goal` and `condition`.

There are four `mode`s of _Intent_\s (for now): `dynamic_translation`, `static_translation`, `interaction` and `transition`. 

A _Intent_ is associated with a specific _Plot_ through its `plot` property. When the world state enters a _Plot_, a new set of _Intent_\s open up to it. The `plot`property determines when an _Intent_ is applicable over the course a game. See [Plotting](./PLOTTING.md) for more information on _Plots_.

The `goal` of an _Intent_ describes just that, what the _Intent_ **intends** to do. The value and meaning of this property will change depending on the `mode` of the _Intent_. THe `goal`s of various `mode`s are described in the next sections.

A `condition` is a nested object that describes when an _Intent_ obtains, i.e. when it is executed and used to update the world state information. Because it is more complex, it will be described it more detail in the next section, before proceeding onto describing the different `mode`s of _Intent_\s.

### Conditions

A `condition` is composed of a `quantifier`, a `predicate`, and a `subject`.

`quantifier` can take on the values: ``all`, `any` or `none`. This operation is applied to the `subject`, to arrive at a domain upon which the `predicate` can in turn operate, to arrive at whether or not the _Intent_ obtains and can thus be applied to the world state.

TODO: THIS ISN'T WELL THOUGHT OUT YET, NEEDS REFINED *********************************


### Static Translation

A `translate` _Intent mode_ maps directly to changing the sprite's positional information, i.e. moving in one of the directions: `north`, `south`, `west`, `east`, `northwest`, `northeast`, `southwest` and `southeast`. 

```yaml
-   name: '?'
    plot: a
    mode: translation
    state: static
    goal: <path_name>
    condition: null
```

**NOTE**: The `<path_name>` referenced in the `goal` property must be defined in the _Sprite_'s dynamic state informatmion.


### Dynamic Translation

```yaml
-   name: '?'
    plot: a
    mode: translation
    state: dynamic
    goal: <sprite_name>
    condition: 
        predicate: otherwise | aware | danger
        quantifier: all | any | none
        subject: <sprite_name>
```

**NOTE**:

### Static Interaction

```yaml
-   name: '?'
    plot: a
    mode: interaction
    state: dynamic
    goal: <plate_name>
    condition: 
        predicate: otherwise | aware | danger
        quantifier: all | any | none
        subject: <plate_name>
```

**NOTE**: The `predicate` of `danger` does not have a meaning here.

### Dynamic Interaction

```yaml
-   name: '?'
    plot: a
    mode: interaction
    state: dynamic
    goal: <sprite_name>
    condition: 
        proposition: otherwise | aware | danger
        quantifier: all | any | none
        subject: <sprite_name>
```

**NOTE**: An `interaction` _Intent_, when it obtains, creates and appends a prioritized `

### Transition

A `transition` _Intent_ describes how a _Sprite_ goes from one state action to another state action.

```yaml
-   plot: a
    mode: transition
    goal: <state_name>
    condition: 
        predicate: 
        quantifier: 
        subject: 
```
## Desires

See [Plotting](./PLOTTING.md) for more information on _Plots_.

## Expressions

## Inspirations