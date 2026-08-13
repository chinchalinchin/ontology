# Ontology: Widgets

Widgets are a type of [Asset](./01-assets.md); however, they reside outside of the core loop and have a special place in the application flow.

Widgets are components of Menus. Or put another way, Menus are assembled from schemas of Widgets. Widgets have properties that configure their static attributes and state that describes their dynamic attributes. However, their state is not updated in concert with the game loop. Instead, Menus are controlled through the flow of Events.

**Events**

To illustrate Events, consider the following example. A Player may enter into the `barter` [Intention](./04-intentions.md) with another Sprite. This causes the gameplay loop to emit an Event containing the Menu key `trade` along with the Event data, i.e. the Sprite States. When an Event is detected by the gameplay, it causes the Board to pause the game loop and pass the Event to be processed by the Bus. The Bus in turn uses the Event data to construct and display the Menu referenced by the Event's Menu key. 

When a Menu is instantiated, its Widgets acquire state. This state is populated through transformations applied to the Menu arguments (in most cases, Sprite state).

**MenuMechanics**

When the Board is paused, the only Mechanics that is applied during the game loop is the MenuMechanic. This Mechanic translates the [Player mapping](./03-player.md#mapping) of (Goal, Intention) to a Menu state change.

**ScreenPosition**

- `ScreenPosition`:
    - `px: double`
    - `py: double`

Menu positions are specified as ScreenPositions. A ScreenPosition is a tuple of percentages relative to the screensize, e.g. the following coordinates denote a position `(0.75w, 0.85h)`, where `(w, h)` is the screensize.

```python
menu.position.x = 0.75
menu.position.y = 0.75
```

## Asset Specification

**Properties: WidgetProperties**

- `dimensions: Dimension`
- `ids: List[str]`

### Buttons

TODO

**Taxonomy**

- `category: widget`
- `instance: button`

**Animation: WidgetAnimation**

**State: ButtonState**

- `content: str` 
- `status: Enum[enabled, active, selected, disabled]`

**Frame: WidgetFrame**

- `key(asset, state): returns {asset}-{state.status}`

### Choices

TODO

### Containers

TODO

### Language

TODO

### Meters

TODO 

### Windows

TODO

## Menus

* Location: `/src/data/menus/main.yaml`

Menus are pre-defined arrangements of widgets. 

**Menu Schema**

TODO

```yaml
--8<-- "docs/.static/yaml/data-menus.yaml"
```

The rest of this section details Menus bundled with the application.

###  Dialogue

TODO

**Arguments**: `sprite.state.psyche.communication`

### Inventory

TODO

**Arguments**: `sprite.state.inventory`

### Market

TODO 

**Arguments**: `buyer.state.inventory`, `seller.state.inventory`

### Main

TODO

### Pause

TODO

**Arguments**

### View

!!! note

    Also known as the Heads-Up Display (HUD).

TODO

**Arguments**: `sprite.state.inventory`
