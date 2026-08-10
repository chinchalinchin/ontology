# Ontology: Player

TODO

## Devices

The Player Asset contains a Device, which polls for user input. The main responsiblity of the Player is to translate the data received into Player state mutations. This is achieved through an input mapping.

### Mapping

Devices have their input mapped to *Actions*, *Directions* and *Extensions*. The mapping configuration file provides a dictionary lookup for what input state corresponds to what game state.

**Keyboard Mappings**

The input state of the Keyboard is polled through SDL. Keyboard mappings correspond to SDL scancodes. See [SDL documentation](https://wiki.libsdl.org/SDL2/SDL_Scancode) for more information.

The default Keyboard mapping bundled with the game is provided below,

```yaml
--8<-- "docs/.static/yaml/examples/default-disposition-matrix.yaml"
```

## Schemas

### Device Mappings

* Location: `src/data/player/mappings.yaml`

```yaml
--8<-- "docs/.static/yaml/data-player-mappings.yaml"
```