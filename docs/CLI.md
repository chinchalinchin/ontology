# Command Line Interface

## Rendering

To render the world state without starting the game loop and output the result to file,

```shell
onta --ontology <path/to/ontology> \
    --render <path/to/save>
```

To render a specific world layer,

```shell
onta --ontology <path/to/ontology> \
    --render <path/to/save> \
    --layer <layer>
```