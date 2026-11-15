#### Refactor: Phase 07.06 - Primitive Crafting

**Overview**

Before tackling the Crafting of Compositions, the basis of Crafting will be laid with *Primitive Crafting*, where a Player or Sprite creates a single instance, possibly multiplied, of a Craft. 

##### Specification

**Initialization**: 

* The MaterialIndex Relation and Materializer Service are used to construct a Primitive Cost Ledger for all indexed Crafts (Stairs, Struts, Bridges, and all future additions).
    * Each separate instance of Craft will need to be unpacked across the dimensions of (Blueprints, Materials). For example, a `steps` Stair unpacks into `steps-limestone`, `steps-feldspar`, `steps-granite`, `steps-marble`.

**Minimum Viable Product: Craft Menu**

1. Player opens Craft Menu.
2. Menu populates the Craft Formulae Pane with Slots hydrated from *all* entries in the Primitive Cost Ledger and initializes each one with the `disabled` Status. 
3. Controller takes Player Inventory and compares it to the Primitive Cost Ledger. Any entry in the Primitive Cost Ledger that is satisfied by the Player Inventory is set to `enabled` Status.
4. Player selects a constructable Craft.
5. Craft Menu closes.
6. A Craft is instantiated *level* with the Player (where *level* is defined as their ground baseline's being equal) and directly *adjacent* (where *adjacent* is defined as touching with no pixel overlap).
 
**Considerations: Icons vs Text**

* Craft Formulae Icon: If using Icons, the Assets will need to be atlased and indexed for each Primitive Craft. This present a problem. Will need to do an assessment of what Assets are available for this task before making any decisions.
* Craft Formula Labels: Could just use text labels that are binding to the Primitive Cost Ledger entries. 