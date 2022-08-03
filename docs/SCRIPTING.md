
# Scripts

- **Script Location**: _data/scripts/*.py_
- **Configuration Location**:

Custom scripts can be injected into the game loop lifecycle to customize sprite actions.

## Lifecycle Hooks

If you want to script the actions for an in-game sprite, set that sprite's `scripting` property to `manual` in _sprites.yaml_. When `scripting == 'manual'`, you will need to add twp secondary properties, `source` and `hook`. The first parameter is the file name of the script you have saved in _data/scripts_ and want to inject into the game loop. The second parameter is the lifecycle event into which you wish to inject your script. See below for more information on lifecycle hooks.

**Note**: Setting `scripting` to `manual` will turn off all hard-wired interactions and reactions. Your script will need to completely describe the sprite's behavior.

- `preupdate`
- `postupdate`
- `prerender`
- `postrender`

## Structure

Regardless of the lifecycle injection point, the script should be structured as follows,


```python
# data/scripts/custom.py

import onta.world as world

def state_handler(world: world.World) -> None:
    pass
```

The game loop will inject the `world` parameter into the `state_handler` function defined in your custom script. The `World` object can be modified according to your desired result. See [Architecture](./ARCHITECTURE.md) and [Definitions](./DEFINITIONS.md) for more information on the concept of the game object, `World`, and how to programmatically interact with it.

## Logic

Each game world iteration maps a sprite state to an in-game action and then iterates that state's frame index. These state-to-action-to-frame mappings cannot be modified; they are the core logic of the world's iteration method. The essence of scripting in _onta_ is determining how a sprite arrives in a given state. If `scripting == 'auto'`, the game engine will take care of the state trajectory (i.e., how the state evolves over a world iteration). These default behaviors are determined by property values in the _sprites.yaml_ configuration file.

However, if `scripting == 'manual'` for a given sprite, the game engine will ignore the default behavior and only concern itself with the state-to-action-to-frame mapping mentioned above. The state trajectory must be specified in the `source` script.

For example, if you want a villain named "roy" to enter a `slash_up` state (see [States](./STATES.md) for more information on sprite states) if the hero enters a certain radius, you can add the logic for this state trajectory as follow,


```python
import math
import onta.world as world
import onta.engine.calculator as calc

# measure in pixels
AWARE_RADIUS = 30

def state_handler(world: world.World) -> None:
    roy_pos = (world.npcs['roy']['position']['x'], world.npcs['roy']['position']['y'])
    hero_pos = world.hero['position']['x'], world.hero['position']['y']
    dis = calc.distance(hero_pos, roy_pos)
    if dis < 30:
        world.npcs['roy']['state'] = 'slash_up'
        world.npcs['roy']['frame'] = 0
```

This will cause the NPC "roy" to enter into the desired state when the player enters into a radius of 30 pixels. Note the frame of the NPC was reset so when the world's iteration method is applied, the NPC will be animated from the beginning of the state.