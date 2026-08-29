# Ontology: Appendix I - Schemas

## Compositions Schemas

- [brick-house](../static/xcf/compositions/brick-house.xcf)
- [postern-gate](../static/xcf/compositions/postern-gate.xcf)

## Hitboxes Schemas

- [sheet-sprite-walk-down-0](../static/xcf/hitboxes/sheet-sprite-walk-down-0.xcf)
- [craft-strut-frame-brick](../static/xcf/hitboxes/craft-strut-frame-brick.xcf)
- [craft-strut-wall-blue](../static/xcf/hitboxes/craft-strut-wall-blue.xcf)
- [craft-strut-wall-castle](../static/xcf/hitboxes/craft-strut-wall-castle.xcf)

![LPC Sprite Hitboxes](static/png/hitboxes/sheet-sprite-walk-down-0.png)
/// caption
LPC Sprite Hitbox in (Walk, Down, 0) State
///

![Brick Frame Strut Hitboxes](static/png/hitboxes/craft-strut-frame-brick.png)
/// caption
Brick Frame Strut Hitbox
///

## File Schemas

### Configuration: Actions

Action Configurations determine the (Action, Direction) partitions employed by a Sheet Asset.

* Location: `/src/data/config/actions/main.yaml`

```yaml
--8<-- "static/yaml/data-actions.yaml"
```

**Default Action Configuration**

```yaml
--8<-- "static/yaml/examples/default-actions.yaml
```

### Configuration: Compositions

Composition Configuration defines a collection of Assets that can be deployed as a unit onto the Board.

* Location: `/src/data/config/compositions.yaml`

```yaml
--8<-- "static/yaml/data-compositions.yaml"
```

### Configuration: Intentions
    
* Location: `/src/data/config/intentions/main.yaml`

```yaml
--8<-- "static/yaml/data-intentions.yaml"
```

**Default Intention Configuration**

```yaml
--8<-- "static/yaml/examples/default-intention-matrix.yaml"
```

### Configuration: Library

* Location: `/src/data/config/library/main.yaml`

TODO

### Configuration: Mapping

* Location: `/src/data/config/mappings/main.yaml`

```yaml
--8<-- "static/yaml/data-mappings.yaml"
```

**Defaults**

The default mappings bundled with the game are provided below,

```yaml
--8<-- "static/yaml/examples/default-mappings.yaml"
```

### Configuration: Mechanics

Mechanics Configuration defines what Mechanic classes are instantiated by the game engine. The order in which they are specified in the schema becomes the order of execution in the game engine.

* Location: `/src/data/config/mechanics/main.yaml`

```yaml
--8<-- "static/yaml/data-mechanics.yaml"
```

**Default Mechanics Configuration**

```yaml
--8<-- "static/yaml/examples/default-mechanics.yaml"
```

### Configuration: Menus

```yaml
--8<-- "static/yaml/data-menus.yaml"
```

**Default Menus**

```yaml
--8<-- "static/yaml/examples/default-menus.yaml"
```

### Configuration: Recipes

Recipe Configuration files determine the specific (State, Animation, Frame) components injected into an Asset Category Instance. The Category and Instance key are encoded into the top-level fields of each Recipe.

* Location: `/src/data/config/recipes/main.yaml`

```yaml
--8<-- "static/yaml/data-recipes.yaml"
```

**Default Recipe Configuration**

```yaml
--8<-- "static/yaml/examples/default-recipes.yaml"
```


### Model: Properties

Asset property index files hydrate the Registry and set the static attributes of Assets.

* Location: `/src/assets/<category>/main.yaml`

```yaml
--8<-- "static/yaml/asset-properties.yaml"
```

### Model: State

Asset state files populate the [Board](./00-overview.md#board). 

* Location: `/src/data/state/<board-key>/*.yaml`

```yaml
--8<-- "static/yaml/asset-state.yaml"
```
