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

See [Plotting](./PLOTTING.md) for more information on _Plots_.

## Desires

See [Plotting](./PLOTTING.md) for more information on _Plots_.

## Expressions

## Inspirations