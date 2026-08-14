# Ontology: Widgets

Widgets are a type of [Asset](./01-assets.md); however, they reside outside of the core loop and have a special place in the application flow.

## Overview

Widgets are components of Menus. Or put another way, Menus are assembled from schemas of Widgets. Widgets have properties that configure their static attributes and state that describes their dynamic attributes. However, their state is not updated in concert with the game loop. Instead, Menus are controlled through the flow of Events.

**Events**

To illustrate Events, consider the following example. A Player may enter into the `barter` [Intention](./04-intentions.md) with another Sprite. This causes the gameplay loop to emit an Event containing the Menu key `trade` along with the Event data, i.e. the Sprite States. When an Event is detected by the gameplay, it causes the Board to pause the game loop and pass the Event to be processed to the Bus. The Bus in turn uses the Event data to construct and display the Menu referenced by the Event's Menu key. 

When a Menu is instantiated, its Widgets acquire state. This state is populated through transformations applied to the Menu arguments (in most cases, Sprite state).

**ScreenPosition**

- `ScreenPosition`:
    - `px: double`
    - `py: double`

Some Menu positions (e.g. Windows) are specified as ScreenPositions. A ScreenPosition is a tuple of percentages relative to the screensize, e.g. the following coordinates denote a position `(0.75w, 0.85h)`, where `(w, h)` is the screensize.

```python
menu.position.x = 0.75
menu.position.y = 0.75
```

## Asset Specification

It is assumed all Widget frames are organized in single row in a `.png` image file. The number of frames (i.e. `len(frames)`) multipled by the width of a single frame(i.e. `dimension.w`) must equal the width of the image file.

**Properties: WidgetProperties**

- `dimensions: Dimension`: Dimensions of a single frame.
- `frames: List[str]`: List of frame keys.

### Buttons

TODO

Buttons contain references and content. Reference determines what is indicated by content. 

- If `reference == icon`, then `content` is a key to an Icon. This Icon is embedded in the button. 
- If `reference == label`, then `content` is a string containing text to be displayed.

!!! warning
    The Button Asset must have large enough dimensions to accomodate Icon Asset embeddings.

!!! warning
    Any label content added to a Button is truncated if it exceeds the dimensions of the Button.

**Taxonomy**

* `category: widget`
* `instance: button`

**Animation: WidgetAnimation**

TODO

- `if state.status != disabled:` 

**State: ButtonState**

* `content: str`
* `reference: Enum[label, icon]` 
* `status: Enum[enabled, active, selected, disabled]`

**Frame: WidgetFrame**

* `key(asset, state): returns {asset}-{state.status}`
* `index(self, asset, properties, recipe): returns TODO` 

### Choices

TODO

### Containers

TODO

### Language

TODO

### Meters

TODO 

### Panes

TODO

## Menus

* Location: `/src/data/menus/main.yaml`

Menus are pre-defined arrangements of Widgets. 

**Properties**

- `layout: Enum[dock, stack]`: Layout of the Menu.

**State**

- `focus: str`: Widget that is currently being focused on for traversal.

**Layouts**

- Dock: A horizontal row of Widgets.
- Stack: A vertical column of Widgets

**Menu Traversal**

TODO

**Menu Schema**

TODO

```yaml
--8<-- "docs/.static/yaml/data-menus.yaml"
```

**MenuMechanics**

When the Board is paused, the only Mechanics that is applied during the game loop is the MenuMechanic. This Mechanic translates the [Player Device mappings](./03-player.md#device-mapping) to Menu state changes. 

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
