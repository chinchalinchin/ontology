
#### Implement: Phase 06 - Editor

**Overview**

Construct an integrated Editor Menu utilizing a dual-mode workflow (Selecting vs. Editing). The UI will utilize a custom Canvas Widget that dynamically scales and bakes an abstract game Board into a fixed-size texture.

**Specifications**:
  - Initializes a Board.
  - Adds Assets to the Board based on user input.
  - Outputs state YAMLs. 

##### Goal: Canvas Widget & Bindings

Extend the UI ECS pipeline to support rendering scaled World representations on a Menu Widget.


##### Goal: Dual-Mode Workflow

Implement the input routing and Cython rebaking pipeline.

##### Design: Data Models

**EditorState**

- `mode: Enum[creating | selecting | editing ]`
- `selection: Taxonomy`:
    - `id`: str
    - `name`: str
    - `instance`: str
    - `category`: str
- `palettes: dict`
  - `tiles: List[Asset]`
  - `objects: List[Asset]`
- `grid: Dict[hash: (x,y)]`
- `focus: str`

**CanvasState**

- `texture: TexturePtr`
- `board: Board`

- `undo(asset: Asset) -> None: board.remove(asset)`

**BoardBinding**

```yaml
bind:
  schema: board
  target: <component>.board
```

Returns a live reference to a Board object. 

##### Design: MVP

Editor Menu has the following layout:

- A Header of Buttons:
  - New: Creates a New Modal to get Canvas size from User.
  - Save: Create a Save Modal to get World name from User.
  - Mode: Toggle between `selecting` and `editing`
- Pane:
  - Tabs:
    - Pane(World Canvas): Disabled when `selecting`
    - Pane(Tile Palette): Disabled when `editing`
    - Pane(Object Palette): Disabled when `editing`
- Pane:
  - Slot(Palette Selection): Current `selection` from `palettes` and its metadata.

###### Tab: Pane(Tile Palette)

All Tiles in the Property Index are read in from the registry and scaled into icons. 

**Layout**: `stack` of `docks`. The number of elements in a `dock` is calulated based on pane size, slot size and the number of Tiles loaded into the registry. For example, if the pane is 100px wide, the slot is 20px wide and there are 14 Tiles in the registry. There will be two `docks` of five Tiles and one `dock` of four tiles. The `docks` will be aligned `center`.

**Pane Workflow**

- User clicks on Tile.
- Selection loads with Tile. 

###### Tab: Pane(Object Palette)

**Layout**: `stack` of `docks`. The number of elements in a `dock` is calulated based on pane size, slot size and the number of Tiles loaded into the registry. For example, if the pane is 100px wide, the slot is 20px wide and there are 14 Tiles in the registry. There will be two `docks` of five Tiles and one `dock` of four tiles. The `docks` will be aligned `center`.

**Pane Workflow**

- User clicks on Object.
- Selection loads with Object.

###### Tab: Pane(World Canvas)

A Pane containing a specialized Widget for representing the Board World state.

**Pane Workflow**

- EditorController hijacks focus traversal.
- Focus traverses grid.
- User pastes Selection into grid coordinates of the Widget.

###### Assets

**Canvas**: It holds a Cython `TexturePtr` (the visual canvas) and an isolated `Board` object (the abstract representation of the world being edited)
**Grid**: Basically a fixed transparent Tile with a border (32x32 px), to highlight the lattice. There are exactly *two* Grid Tiles, required by the application, `focus` and `cell`. `focus` is the frame displayed when the Editor is focused on a particular cell of its `grid`. `cell` is the frame displayed when a particular cell of the grid does not have `focus`. Grid Tiles are superimposed over the Canvas.

###### Workflow

- All Buttons in Bar are disabled but New. 
- User is forced to select New.
  - User enters (width, length) into New Modal.
- Canvas(world=(width, length)) is created.
  - **NOTE**: Canvas Size is part of the Editor configuration. Canvas calculates a constant of portionality, `ratio`, upon instantiation. This represents the conversion rate between World space and Canvas space.
  - Editor uses Grid Tiles to construct a scaled replica of World space in Canvas space. Editor assumes World is partitioned into grid of `(tiles.grid.dimension.w, tiles.grid.dimensions.l)` squares.
  - Editor uses `ratio` to scale the World to Canvas size.
- User enters `selecting` mode. Canvas is displayed next to empty Selection Slot.
  - User is able to navigate `grid` by shifting `focus` at this point, but selecting does nothing.
- User navigates to the Palette Tab
  - `focus` moves between Canvas and Button Bar.
  - `focus` traverses Button Bar.
  - `focus` selects appropriate Tab.
- Palette Tab is displayed.
- User makes a Selection. 
- Selection is saved into the `selection` buffer. 
- Selection Slot is updated with `selection`.
- Editor automatically switches to `editing` mode. Palette tabs are disabled and Canvas tab is shown.
- User navigates `grid` by shifting focus. 
- User selects `grid` coordinates, where (x,y) is the top left of the grid square.
- Selection is instantiated at (x, y) and added to the Board. 
  - Update/CamvasEvent is fired to rebake Canvas.
  - Canvas (or TBD component) renders entire Board state, scales it down to the Canvas size for stamping the Canvas display.
  - Canvas is redrawn. 
- Editor is still in `editing` mode. Selection is still selected in Selection Slot. 
  - User may continue instantiating the selected Palette Asset.
  - User may presses `CANCEL` to undo the Selection paste.
- User clicks Save. Board is serialized into state file.
  - User enters `<board-key>` into Save Modal.
  - Board is saved to `/src/data/state/<board-key>/<timestamp>.yaml`

**Notes**

1. *Hardware Texture Limits (The Rebake Method)*: Do not render at 1:1. The `render.construct()` interface in `libs/graphics/render.pyx` already accepts `dx, dy, dw, dl`. Calculate the proportional constant on the Python side, scale every asset's dimensions and positions, and pass those reduced integers across the boundary. Bake *directly* onto the fixed-size Canvas Widget texture.
2. *Traversal Hijacking*: Right now, `MenuMechanics` blindly reads `DevicePayload.menu.traversal` and checks `active_menu.graph` to jump focus from widget to widget. If user presses `EAST` while focused on the Canvas, it will try to jump to the next Widget in the traversal grpah button. `MenuMechanics` needs an explicit mechanism to relinquish traversal control. When the "editing" toggle is active, `MenuMechanics` must stop querying the AABB graph and route `NORTH/SOUTH/EAST/WEST` directly into the `EditorController.update()` to move the grid coordinate.
3 *The `CANCEL` Undo Conflict\* In the current implementation, passing `Interactions.CANCEL` pushes a `TerminalEvent` to the bus, which instantly pops the active Menu off the stack and closes it. If `CANCEL` is to act as "undo", this behavior must be intercepted. The `EditorController` must intercept the `CANCEL` input when in `editing` mode, pop the last modification from an internal `undo_stack`, and swallow the input so it never reaches the `MenuMechanics` teardown logic.

#### Tasks

**1. Task: Board Binding Implementation**

*Objective*: Create a binding schema to link a World Board to a Menu Widget.

* [ ] Subtask: Create `BoardBinding(Binding)` in `app.game.menus.bindings.py`. Implement `bind()` to return a `board_function` closure resolving the target abstract Board.
* [ ] Subtask: Register `schema == 'board'` in `Binder.binding()` (`app.services.generators.binder.py`).

**2. Task: Canvas State Models**

*Objective*: Define the data models for the Canvas Widget.

* [ ] Subtask: Create `CanvasState` in `app.models.state.widgets`.
* [ ] Subtask: Include fields: `board` (abstract Board), `world_size` (Dimensions), `ratio` (float), `cursor_grid` (Position), `undo_stack` (List).

**2. Task: Provider Instantiation**

*Objective*: Allow the Provider to instantiate the Canvas Widget.

* [ ] Subtask: Implement `_unpack_canvas` in `app.services.generators.provider`.
* [ ] Subtask: Initialize the Canvas by calculating the `ratio` (`widget.dimensions.w / world_size.w`). Allocate the fixed-size UI texture via `render.canvas()`.

**3. Task: The Rebake Pipeline**

*Objective*: Bake the abstract world onto the Canvas texture using scaled primitive tuples.

* [ ] Subtask: Implement a `_rebake_canvas()` helper in the `EditorController`.
* [ ] Subtask: Iterate over `CanvasState.board`. Multiply each asset's `dx, dy, dw, dl` by the `ratio`.
* [ ] Subtask: Pass the scaled primitive tuples, along with a tiled grid asset and the highlighted cursor coordinate asset, to `render.construct()` targeting the Canvas Widget's `TexturePtr`.

**4. Task: Traversal & Undo Routing**

*Objective*: Intercept inputs based on the mode toggle.

* [ ] Subtask: Refactor `MenuMechanics.update()` to check for an `editing_mode` flag. If true, bypass `active_menu.graph` traversal and route directional input to the Controller.
* [ ] Subtask: Intercept `Interactions.CANCEL` in `MenuMechanics`. If `editing_mode` is true, route to the Controller for Undo logic instead of firing a `TerminalEvent`.

**5. Task: Editor Controller Logic**

*Objective*: Implement the core mode-switching and placement behaviors.

* [ ] Subtask: Implement `select()`. If in `selecting` mode, update the active `Taxonomy` selection. If in `editing` mode, push the current cell state to the `undo_stack`, append the selected asset to the abstract `Board` at `cursor_grid * 32`, and trigger `_rebake_canvas()`.
* [ ] Subtask: Implement `update()`. If in 'editing' mode, listen for traversal inputs to increment/decrement `cursor_grid` and trigger `_rebake_canvas()` to update the highlight position.










#### Backlog: Implement Phase 06 - Editor

**Overview**
Construct an integrated Editor Menu utilizing a dual-mode workflow (Selecting vs. Editing). The UI will utilize a custom Canvas Widget bound to a Board via `BoardBinding`. The `EditorController` manages mode toggling, internal grid coordinates, and the undo stack.

##### Goal: Canvas Widget & Bindings

Extend the UI ECS pipeline to support rendering scaled World representations on a Menu Widget.

##### Tasks

**1. Task: Board Binding Implementation**
*Objective*: Create a binding schema to link a World Board to a Menu Widget.

* [ ] Subtask: Create `BoardBinding(Binding)` in `app.game.menus.bindings.py`. Implement `bind()` to return a `board_function` closure resolving the target abstract Board.
* [ ] Subtask: Register `schema == 'board'` in `Binder.binding()` (`app.services.generators.binder.py`).

**2. Task: Canvas Widget Core**
*Objective*: Define the data models for the Canvas Widget.

* [ ] Subtask: Create `CanvasState` in `app.models.state.widgets`. Include `board_function` (Callable), `proportional_constant` (float), and `canvas` (TexturePtr).
* [ ] Subtask: Implement `_unpack_canvas` in `app.services.generators.provider`. Calculate `proportional_constant = widget.dimensions.w / world_size.w` and allocate the fixed-size UI texture via `render.canvas()`.

**3. Task: The Editor Controller State**
*Objective*: Consolidate Editor logic into the Controller.

* [ ] Subtask: Create `EditorController(MenuController)` in `app.game.menus.controllers`.
* [ ] Subtask: Initialize instance variables on the Controller: `editing_mode: bool`, `grid_cursor: Position`, and `undo_stack: List[Asset]`.

##### Goal: Dual-Mode Workflow

Implement the input routing and Cython rebaking pipeline.

##### Tasks

**4. Task: Traversal & Undo Routing**
*Objective*: Intercept inputs based on the mode toggle.

* [ ] Subtask: Refactor `MenuMechanics.update()` to check for `active_menu.controller.editing_mode` (or similar flag). If true, bypass `active_menu.graph` traversal and route `NORTH/SOUTH/EAST/WEST` to `active_menu.controller.update()`.
* [ ] Subtask: Intercept `Interactions.CANCEL` in `MenuMechanics`. If `editing_mode` is true, route to the Controller for Undo logic instead of firing a `TerminalEvent`.

**5. Task: Placement and Rebaking Pipeline**
*Objective*: Implement the core placement behaviors and Canvas texture updates.

* [ ] Subtask: Implement `EditorController._rebake(canvas_widget)`. Retrieve the Board via `canvas_widget.state.board_function()`. Iterate over the Board's assets, scaling their primitives by `proportional_constant`. Pass to `render.construct()` targeting the `TexturePtr`.
* [ ] Subtask: Implement `EditorController.update()`. When receiving directional input in editing mode, increment/decrement `grid_cursor`, clamp to boundaries, and trigger `_rebake()` (passing a scaled highlight decal primitive).
* [ ] Subtask: Implement `EditorController.select()`. If editing, append the selected taxonomy to the Board at `grid_cursor * 32`, push the Asset to `undo_stack`, and `_rebake()`. If `CANCEL`, pop the `undo_stack`, call `board.remove([popped_asset])`, and `_rebake()`.