#### Refactor: Phase I, Part I

After review of Phase I, several modifications and refactors have been initiated. The following decisions have been made regarding the core architecture of the game engine,

- An Asset Hierarchy has been codified through (Category, Instance). This is a pure data abstraction on top of the configuration which drives the Entity Component System for Object Instantiation.
- It has been decided all Assets of a common Category (Tile, Object, etc.) should implement the same Properties schema, e.g. all Objects have the same Property fields (not necessarily values). In other words, an Asset's Category determines what type of Properties it will parse and inject into its Deployment.
- It has been decaded all Assets of a common Instance (Crate, Sprite, etc.) should implement the same State schema, e.g. all Chests have the same Container state fields (not necessarily values). In other words, an Asset's Instance determines what type of State it will parse and inject into its Deployment.

The changes entailed by these shifts are detailed below.

One of the motivations for this structural change is removing the complexity of the `src/app/orchestration.py` and `src/app/game/factory.py`. In other words, these refactor seeks to align the data structures of the in-game Asset so the dimensions of their configuratiion are determined entirely by their Asset Category.

**Orchestration & Hydration**

The imposition of the Category and Instance partition should signficantly reduce the verbosity in `orchestration.py`, since all Asset Category Instances now have the same general schema in the property and state files.

In addition, Pydantic Models for validating the new state and properties have been added.

- [x] Refactor orchestration complexity in `src/app/orchestration.py`.
- [x] Ensure POPOs are updated to match the data being received through the Pydantic DTOs.
- [x] Implement Board Asset Caching. Refactor `src/app/game/board.py`. Pre-calculate and cache dictionaries for categories and instances mapped by layer during `__init__`. The methods `categories()` and `instances()` must return references to these existing lists, completely eliminating list comprehensions from the main loop.
- [x] Optimize Mechanic Queries. Ensure no Mechanic class (`SwitchMechanics`, `CollisionMechanics`, etc.) utilizes `chain()` or list comprehensions inside `update()`. Rely entirely on the newly cached lists from the `Board`.
- [x] Refactor orchestration complexity in `src/app/orchestrator.py`. The orchestrator functions are far too complex. Use the data structures intelligently to hydrate the asset models. 
- [x] Ensure factory methods align with schemas and models.
- [x] Ensure POPOs are updated to match the data being received through the Pydantic DTOs.
- [x] Rewrite the CLI from scratch. CLI should not be interacting with low-level objects and SDL interfaces. Have it create an Orchestrator, retrieve the Board and Screens. 
    - [x] Add default args to the CLI for screensize.
    - [x] Add method to Board to calculate the boardsize based on the position and multiples of Tiles.
    - [x] Add export methods to Screen.
- [x] Fix `Board.relayer()` to accurately remove/append assets to the `_cached_layers` arrays so `board.assets(layer)` queries return accurate data.

**Crafts**

A Craft Asset Categry has been devised, and a single Instance has been added to it. Struts have been added to support the `CommerceMechanics`. Refer to the [Struts Documentation](../../01-assets.md#struts) and [Struts schemas](../../01-assets.md#schemas) for more information on their use and data models.

- [x] Ensure Craft properties and state are correctly instantiated.
- [x] Ensure `src/app/game/factory.py` has the explicit mapping to route `CraftProperties` and `PropertyState` correctly when hydrating crafts from the orchestrator.

**Tiles**

Tiles have been decomposed from a Category with a single Instance to multiple Instances, Fore and Back, i.e. a nesting has been add to the Tile state and property configuration. This will substantially alter the object hydration flows for Tiles.

- [x] Ensure the Tiles remained indexed correctly in the `libs/registry.pyx`
- [x] Create another buffer in the renderer to hold the Fore tiles. This should be initialized during the application initialization, along with the Back tile buffer. During `render` superimpose the dynamic Assets onto the Back tile buffer, and then superimpose the Fore tiles on top of the dynamic Assets.
- [x] Update Cython Render Signature. Modify `libs/render.pyx` -> def `render(...)` to accept a `TexturePtr` foreground parameter.
- [x] Implement Painter's Algorithm in C. Inside the render function, add a step immediately before `SDL_RenderPresent` to copy the foreground texture to the renderer, using the exact same `bg_src `camera coordinates used for the background.
- [x] Orchestrate Foreground Canvas. In `src/app/screen.py`, instantiate two canvases (`self.bg_canvas` and `self.fg_canvas`) during `__init__`. Route Back Tile assets to the background constructor and Fore Tile assets to the foreground constructor, then pass both pointers to the `render()` call.

**Sheets**

To support this structural change, the schemas of Sheets have been modified to align their properties. 

The Pixie Schema is now reworked, and some of the properties have been renamed to correspond to their Sprite counterparts. Pixies used to be constrained to have a certain number of rows and frames. But to generalize across the asset hierarchy, their properties have been brought in line with Sprites.

The Sprite Schema used to assemble the Sprite Sheets from a `base` and `features` attribute specified in the `/assets/sheets/main.yaml` configuration file. To align the Pixie and Sprite configurations, a more general Property schema has been adopted, with Actions and Personas alterations to ensure they conform with both Asset Instance types. See [Sheets documentation](../../01-assets.md#sheets) for more information.

- [x] Ensure Sheets remained indexed correctly in the `libs/registry.pyx`
- [x] Re-hydrate the Pixie states in `src/app/orchestration.py`, `src/app/game/factory.py`.
- [x] Re-index the Pixie assets in `libs/registry.pyx`
- [x] Re-hydrate Sprite states in `src/app/orchestration.py`, `src/app/game/factory.py`
- [x] Verify Sprite Stacking. Confirm that the compose() method in `libs/render.pyx` correctly flattens the newly aligned Persona configurations into a single GPU texture without memory leaks.