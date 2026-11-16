#### Refactor: Phase 07.06 - Crafting

**Overview**

Building upon the Material aspect of Assets, design and introduce a Crafting system managed through a new Craft Menu.

##### Specification

**(Blueprints, Materials)**

* materials: 
    * organics: cottons, thatches, wood
    * ceramics: clay
    * geologics: limestone, feldspar, granite, marble
    * metallics: copper, iron, gold
    * chromatics: neutral, blue, red, yellow, green
* blueprints: 
    * buildings: floors, walls, flats, roofs, paths, halls
    * corridors: solids, stripes, designs
    * columns: crowns, shafts, bases 
    * decor: decor
    * enclosures: north, east, south, west
    * inclines: up, left, right
    * orientations: horizontal, vertical

**Definition: Primitives**

Primitive Crafts can be constructed by the User without a Composition container.

* Stairs
* Bridges
* Decor Struts

**Definition: Armatures**

To hide the complexity of the Strut (Blueprint, Material) space from the User, a subdirectory of Compositions (`/src/data/config/compositions/armatures/**/*.yaml`)will be maintained, known as *Armatures*. In a sense, Armatures integrate a Strut over its Blueprint partition. 

```yaml
compositions:
  armature/building/home:
    root:
      strut:
        id: home
        name: roof
        blueprint: roofs
      components:
        objects:
          doors:
            - id: panel
              name: door
              anchor: anchor(exterior)
              material: neutral
              outlayer: house-layer
              position:
                x: (bind(parent.dimensions.w) - bind(self.dimensions.w)) // 2
                y: bind(exterior.position.y) + bind(exterior.dimensions.l) - bind(self.dimensions.l)
              out:
                x: bind(interior.position.x) + (bind(interior.dimensions.w) - bind(self.dimensions.w)) // 2
                y: bind(interior.position.y) + bind(floor.position.y) + bind(floor.dimensions.l) - bind(self.dimensions.l)
        crafts:
          struts:
            - id: home
              name: exterior
              material: bind(root.material)
              blueprint: walls
              position:
                x: 0
                y: bind(parent.dimensions.l)
    branches:
      - strut:
          id: home
          name: interior
          material: bind(root.material)
          blueprint: halls
          layer: house-layer
          position:
            x: 10
            y: 10
        components:
          crafts:
            struts:
              - id: home
                name: floor
                layer: house-layer
                material: bind(root.material)
                blueprint: floors
                position:
                  x: 0
                  y: bind(parent.dimensions.l)
```

These are "*User Facing Crafts*". Users do not directly instantiate Struts. They instantiate Armatures of Struts (e.g. parameterized Compositions). In the example above, the branch Struts depend on the `material` of the root Struts, which is dependent on the parameter passed into the Composition. In this way, the parameter of Material is a degree of freedom determined by User selection.

Each Armature will be keyed according to the following schema:

* `armature/<icon-filter>/<strut>`
    * `<icon-filter>`: The Icon to which the Armature activates when filtering. (See **Feature: Craft Filters**)
    * `<strut>`: The Primitive Strut which the Armature integrates over its Blueprint Partition.

* `icon-filters`: `building`, `road`, `tower`, `carpentry`, `railing`

**Initialization**: 

* The MaterialIndex Relation and Materializer Service are used to construct a Cost Ledger for all indexed Primitive Crafts and configured Armatures.
    * Each separate instance of a Primitive Craft will need to be unpacked across the dimension of (Blueprints, Materials). For example, a `steps` Stair unpacks into `steps-up-limestone`, `steps-left-limestone`, `steps-right-limestone`, `steps-up-feldspar`, `steps-left-feldspar`, `steps-right-feldspar`, ... 

**Minimum Viable Product: Craft Menu**

1. Player opens Craft Menu.
2. Menu populates the Craft Formulae Pane with Slots hydrated from *all* entries in the Primitive Cost Ledger and initializes each one with the `disabled` Status. 
3. Controller takes Player Inventory and compares it to the Primitive Cost Ledger. Any entry in the Primitive Cost Ledger that is satisfied by the Player Inventory is set to `enabled` Status.
4. Player selects a constructable Craft.
5. Craft Menu closes.
6. A Craft is instantiated *level* with the Player (where *level* is defined as their ground baseline's being equal) and directly *adjacent* (where *adjacent* is defined as touching with no pixel overlap).
 
**Feature: Craft Filters**

The `crafts` Icon Widget can be utilized to represent user-facing Crafts