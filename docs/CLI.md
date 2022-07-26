# Command Line Interface

## Logging

Console output can be set with the `LOG_LEVEL` environment variable,

```shell
export LOG_LEVEL=VERBOSE
onta --ontology <path/to/ontology>
```

Allowable values for `LOG_LEVEL` are `INFO`, `DEBUG`, `VERBOSE` and `INFINITE`.

## Rendering

To render the world state and output the result to file without starting the game loop,

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

## Separating Ontology Directories

You can specify the asset directory, the configuration directory and the state directory through separate command line arguments, if you need to separate the directories themselves for whatever reason. If any one of these arguments is missing, the default data directory in the installation will be used,

```shell
onta --asset-dir <> \
        --conf-dir <> \
        --state-dir <> 
```

TODO: implement this.