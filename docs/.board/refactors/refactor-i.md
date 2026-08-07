#### Refactor: The Great Phase I Refactor

After review of Phase I, several modifications and refactors have been initiated.

- It has been decided all Assets of a common Category (Tile, Object, etc.) should implement the same Properties schema, e.g. all Objects have the same Property fields (not necessarily values). In other words, an Asset's Category determines what type of Properties it will parse and inject into its Deployment.
- It has been decaded all Assets of a common Instance (Crate, Sprite, etc.) should implement the same State schema, e.g. all Chests have the same Container state fields (not necessarily values). In other words, an Asset's Instance determines what type of State it will parse and inject into its Deployment.

**Struts**

Struts have been added to support the `CommerceMechanics`. Refer to the [Struts Documentation](../../01-assets.md#struts) and [Struts schemas](../../01-assets.md#schemas) for more information on their use and data models.

**Tiles**

Tiles have been decomposed from a Category with a single Instance to multiple Instances, Fore and Back.

**Sheets**

To support this structural change, the schemas of Sheets have been modified to align their properties. The Pixie Schema is now reworked, and some of the properties have been renamed to correspond to their Sprite counterparts.

