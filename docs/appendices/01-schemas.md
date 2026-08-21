# Ontology: Appendix I - Schemas

## Hitboxes

### Category: Sheet, Instance: Sprite

- [Download xcf](../static/xcf/sheet-sprite-walk-down-0.xcf)

![LPC Sprite Hitboxes](static/png/hitboxes/sheet-sprite-walk-down-0.png)
/// caption
LPC Sprite Hitbox in (Walk, Down, 0) State
///

### Category: Craft, Instance: Strut

- [Download xcf](../static/png/hitboxes/craft-strut-frame-brick.png)

![Brick Frame Strut Hitboxes](static/png/hitboxes/craft-strut-frame-brick.png)
/// caption
Brick Frame Strut Hitbox
///

## Schemas

### Composition Configuration

Composition Configuration defines a collection of Assets that can be deployed as a unit onto the Board.

* Location: `/src/data/config/compositions.yaml`

```yaml
--8<-- "static/yaml/data-compositions.yaml"
```

### Mapping Configuration

* Location: `/src/data/config/mappings/main.yaml`

```yaml
--8<-- "static/yaml/data-mappings.yaml"
```

**Defaults**

The default mappings bundled with the game are provided below,

```yaml
--8<-- "static/yaml/examples/default-mappings.yaml"
```

### Mechanics Configuration

Mechanics Configuration defines what Mechanic classes are instantiated by the game engine. The order in which they are specified in the schema becomes the order of execution in the game engine.

* Location: `/src/data/config/mechanics/main.yaml`

```yaml
--8<-- "static/yaml/data-mechanics.yaml"
```

**Default Mechanics Configuration**

```yaml
--8<-- "static/yaml/examples/default-mechanics.yaml"
```

### Menu Configuration

```yaml
--8<-- "static/yaml/data-menus.yaml"
```

**Default Menus**

```yaml
--8<-- "static/yaml/examples/default-menus.yaml"
```

### Recipe Configuration

Recipe Configuration files determine the specific (State, Animation, Frame) components injected into an Asset Category Instance. The Category and Instance key are encoded into the top-level fields of each Recipe.

* Location: `/src/data/config/recipes/main.yaml`

```yaml
--8<-- "static/yaml/data-recipes.yaml"
```

**Default Recipe Configuration**

```yaml
--8<-- "static/yaml/examples/default-recipes.yaml"
```

### Action Configuration

Action Configurations determine the (Action, Direction) partitions employed by a Sheet Asset.

* Location: `/src/data/config/actions/main.yaml`

```yaml
--8<-- "static/yaml/data-actions.yaml"
```

**Default Action Configuration**

```yaml
--8<-- "static/yaml/examples/default-actions.yaml
```

### Intention Configuration
    
* Location: `/src/data/config/intentions/main.yaml`

```yaml
--8<-- "static/yaml/data-intentions.yaml"
```

**Default Intention Configuration**

```yaml
--8<-- "static/yaml/examples/default-intention-matrix.yaml"
```

### Property Indices

Asset property index files hydrate the Registry and set the static attributes of Assets.

* Location: `/src/assets/<category>/main.yaml`

```yaml
--8<-- "static/yaml/asset-properties.yaml"
```

### State Files

Asset state files populate the [Board](./00-overview.md#board). 

* Location: `/src/data/state/<board-key>/*.yaml`

```yaml
--8<-- "static/yaml/asset-state.yaml"
```
