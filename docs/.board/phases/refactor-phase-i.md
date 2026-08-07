#### Refactor: The Great Phase I Refactor

After review of Phase I, several modifications and refactors have been initiated. The following decisions have been made regarding the core architecture of the game engine,

- An Asset Hierarchy has been codified through (Category, Instance). This is a pure data abstraction on top of the configuration which drives the Entity Component System for Object Instantiation.
- It has been decided all Assets of a common Category (Tile, Object, etc.) should implement the same Properties schema, e.g. all Objects have the same Property fields (not necessarily values). In other words, an Asset's Category determines what type of Properties it will parse and inject into its Deployment.
- It has been decaded all Assets of a common Instance (Crate, Sprite, etc.) should implement the same State schema, e.g. all Chests have the same Container state fields (not necessarily values). In other words, an Asset's Instance determines what type of State it will parse and inject into its Deployment.

The changes entailed by these shifts are detailed below.

One of the motivations for this structural change is removing the complexity of the `src/app/orchestration.py` and `src/app/game/factory.py`. In other words, these refactor seeks to align the data structures of the in-game Asset so the dimensions of their configuratiion are determined entirely by their Asset Category.

**Orchestration & Hydration**

The imposition of the Category and Instance partition should signficantly reduce the verbosity in `orchestration.py`, since all Asset Category Instances now have the same general schema in the property and state files.

In addition, Pydantic Models for validating the new state and properties have been added.

- [ ] Refactor orchestration complexity.
- [ ] Ensure POPOs are updated to match the data being received through the Pydantic DTOs.
- [ ] TODO: TASKING

**Crafts**

A Craft Asset Categry has been devised, and a single Instance has been added to it. Struts have been added to support the `CommerceMechanics`. Refer to the [Struts Documentation](../../01-assets.md#struts) and [Struts schemas](../../01-assets.md#schemas) for more information on their use and data models.

- Ensure Craft Properties and State are correctly instantiated.
- TODO: TASKING

**Tiles**

Tiles have been decomposed from a Category with a single Instance to multiple Instances, Fore and Back, i.e. a nesting has been add to the Tile state and property configuration. This will substantially alter the object hydration flows for Tiles.

- [ ] Ensure the Tiles remained indexed correctly in the `libs/registry.pyx`
- [ ] Create another buffer in the renderer to hold the Fore tiles. This should be initialized during the application initialization, along with the Back tile buffer. During `render` superimpose the dynamic Assets onto the Back tile buffer, and then superimpose the Fore tiles on top of the dynamic Assets.
- TODO: TASKING

**Sheets**

To support this structural change, the schemas of Sheets have been modified to align their properties. 

The Pixie Schema is now reworked, and some of the properties have been renamed to correspond to their Sprite counterparts. Pixies used to be constrained to have a certain number of rows and frames. But to generalize across the asset hierarchy, their properties have been brought in line with Sprites.

The Sprite Schema used to assemble the Sprite Sheets from a `base` and `features` attribute specified in the `/assets/sheets/main.yaml` configuration file. To align the Pixie and Sprite configurations, a more general Property schema has been adopted, with Actions and Personas alterations to ensure they conform with both Asset Instance types. See [Sheets documentation](../../01-assets.md#sheets) for more information.

- [ ] Ensure Sheets remained indexed correctly in the `libs/registry.pyx`
- [ ] Re-hydrate the Pixie states in `src/app/orchestration.py`, `src/app/game/factory.py`.
- [ ] Re-index the Pixie assets in `libs/registry.pyx`
- [ ] Re-hydrate Sprite states in `src/app/orchestration.py`, `src/app/game/factory.py`

**General Debugging**

- [ ] This may have ancillary and knock-on effects in some of the libraries. Ensure the application has not be substantially broken by this refactor by mentally simulating the data flows.