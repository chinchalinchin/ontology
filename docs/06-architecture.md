# Ontology: Architecture

This section contains an in-depth presentation of the game engine's programmatic architecture.

## Initialization

1. Create `Registry`.
    * Load Assets into memory
        - Recursive load `/src/assets/**` using the `main.yaml` contained in each `/src/asset/<category>` directory. Create a map using the key-values `<registry-key>: <frame>`, where `<registry-key>` is the Asset file name (`<asset-key>`), unless otherwise specified below:
            - Parse and index Chests, Gates and Plates so each frame is indexed with    `<asset-key>-<idle | activated>`.
            - Parse and index Pixie sheets so each frame is indexed with `<asset-key>-<direction>-<number>`, with `<number>` starting at 0.
            - Parse and index Sprite sheets so each frame is indexed with `<asset-key>-<action>-<direction>-<number>`, with `<number>` starting at 0.
2. Create `Board`.
    * Load Board into memory
        - Load the following YAML files from the `/src/data/boards/<board-key>` directory, where `<board-key>` is the selected board.
            - `/src/data/boards/<board-key>/immutable/inanimate.yaml`
            - `/src/data/boards/<board-key>/immutable/animate.yaml`
            - `/src/data/boards/<board-key>/mutable/inanimate.yaml`
            - `/src/data/boards/<board-key>/mutable/animate.yaml`
        - Initalize dictionaries of Asset lists, keyed by the Asset Layer. 

**Example of Asset list dictionary,

```python
sprites = {
    "layer-0": [
        # ....
    ],
    "layer-1": [
        # ...
    ],
    # ...
}
```
            