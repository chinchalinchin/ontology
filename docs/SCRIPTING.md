
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

def state_handler(world: world.World, user_input: dict) -> None:
    pass
```

The game loop will inject the `world` and `user_input` parameter into the `state_handler` function defined in your custom script. The `World` object can be modified according to your desired result. See [Architecture](./ARCHITECTURE.md) and [Definitions](./DEFINITIONS.md) for more information on the concept of the game object, `World`, and how to programmatically interact with it.