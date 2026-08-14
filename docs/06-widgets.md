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

### Panes

Panes are the *root* Widgets of a Menu. They are the only Widget which has a ScreenPosition. ScreenPosition for a root Pane is specified in the [Menu Schema](#menus).

Panes contain other Widgets. Their child Widgets have their Positions calculated relative to the root Pane based on the `layout` and `alignment`. Layouts are enumerated below,

- Dock: A horizontal row of Widgets.
- Stack: A vertical column of Widgets

Alignments are enumerated below,

- Start: Widgets are aligned at the start of the Pane.
- End: Widgets are aligned at the end of the Pane.
- Center: Widgets are aligned at the center of the Pane.

**Taxonomy**

* `category: widget`
* `instance: pane`

**State: PaneState**

- `position: ScreenPosition`
- `layout: Layout`
- `alignment: Alignment`
- `gap: int` : Pixel gap between child Widgets.
- `margins: Tuple[int, int, int, int]`: Margins applied around the edge of the Pane before aligning children in the layout.
- `children: List[Widget]`: List of Widgets contained in the Pane.

**Frame: SingleFrame**

* `key(asset, state): returns {asset}`
* `index(self, asset, properties, recipe): returns TODO` 

### Buttons

Buttons are selectable Widgets that enter into a Status of `selected` when triggered. Buttons contain references and content. Reference determines what is indicated by content. 

- If `reference == language`, then `content` is a key to an Language Widget. This Widget is embedded in the Button. 
- If `reference == label`, then `content` is a string containing text to be displayed on the button.

!!! warning
    The Button Asset must have large enough dimensions to accomodate Language Asset embedding.

!!! warning
    Any label content added to a Button is truncated if it exceeds the dimensions of the Button.

**Taxonomy**

* `category: widget`
* `instance: button`

**Animation: TraversalAnimation**

TODO

- `if state.status != disabled:` 

**State: ButtonState**

* `content: str`
* `reference: Enum[label, icon]` 
* `status: Enum[idle, active, selected, disabled]`

**Frame: TraversalFrame**

* `key(asset, state): returns {asset}-{state.status}`
* `index(self, asset, properties, recipe): returns TODO` 

### Choices

TODO

### Containers

TODO

### Language

TODO

### Meters

Meters are "continuous" indicators. They require a `unit` to calibrate their reading and then express a `measurement` in terms of the `unit`; All readings are expressed relative to the `unit`, e.g. the ration of the current value of the Player's health to maximum value of the Player's health is expressed as the proportion of a Meter that is filled.

Meters rows are broken up as follows:

- **Meter** First Frame: width = w
- **Marker** Second Frame: width = 0.25w, fill = 100%
- **Marker** Third Frame: width = 0.25w, fill = 75%
- **Marker** Fourth Frame: width = 0.25w, fill = 50%
- **Marker** Fifth Frame: width = 0.25w, fill = 25%

So the total width of a Meter Asset is 2w. 

The first frame of the Meter is the Meter itself. Each subsequent frame is a *Marker*. Each Marker's width is 25% of the width of Meter. The second frame is Marker width completely filled. The third frame is the Marker width 75% filled. The fourth frame is the Marker width 50% filled. The fifth frame is Marker width 25% filled. This division of the Meter and Marker frames allows a Meter to resolve an ingame attribute down to increments of 1/16. If `measurement / unit % 16 != 0`, then the increment displayed is rounded to the nearest 1/16th.

In other words, a Meter is broken up into four `markers` whose frames that are superimposed over the Meter itself, which is at frame index 0. Each Marker maps to a frame index (1 - 4). 

For example, if `player.state.meters.health.current == 75`, so that `measurement / unit = 0.625`, then

- marker 1: frame = 1
- marker 2: frame = 1
- marker 3: frame = 3
- marker 4: frame = None

The sequence to frames (1, 1, 3, None) would be superimposed over frame 0 at the positions (0, 0.25w, 0.5w, 0.75w).

**Taxonomy**

* `category: widget`
* `instance: meter`

**Animation: MeterAnimation**

TODO: calculate marker formula based on `measurement / unit`

**State: MeterState**

* `unit: int`
* `measurement: int`
* `markers: List[int | None]`

**Frame: WidgetFrame**

* `key(asset, state): returns {asset}-{state.status}`
* `index(self, asset, properties, recipe): returns TODO` 

## Menus

* Location: `/src/data/menus/main.yaml`

Menus are pre-defined arrangements of Widgets. 

**Menu State**

- `focus: str`: Widget that is currently being focused on for traversal.

**Menu Traversal**

TODO

**Menu Mechanics**

When the Board is paused, the only Mechanics that is applied during the game loop is the MenuMechanic. This Mechanic translates the [Player Device mappings](./03-player.md#device-mapping) to Menu state changes. 

The rest of this section details Menus bundled with the application.

**Menu Schema**

TODO

```yaml
--8<-- "docs/.static/yaml/data-menus.yaml"
```

**Default Menus**

```yaml
--8<-- "docs/.static/yaml/examples/default-menus.yaml"
```

### Dialogue

TODO

**Arguments**: `sprite.state.psyche.communication`

### Editor

TODO

**Arguments**: `Board`

### Inventory

TODO

**Arguments**: `sprite.state.inventory`

### Market

TODO 

**Arguments**: `buyer.state.inventory`, `seller.state.inventory`

### Main

TODO

**Arguments**: `None`

### Pause

TODO

**Arguments**

### View

!!! note

    Also known as the Heads-Up Display (HUD).

TODO

**Arguments**: `sprite.state`
