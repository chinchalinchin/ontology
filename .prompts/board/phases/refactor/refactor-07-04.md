#### Refactor: Phase 07.04 - Materialization

**Overview** 

- Reduce the Strut overhead and Asset proliferation by affecting a simplification through hierarchical organization of Struts via `material` and `purpose`.

**Notes**

- Determine which Assets need pruned to ensure all conform to the schema and simplify the amount of boilerplate.
- Many assets will need edited so their dimensions align along the `material` axis, or else MaterialHitbox will need introduced so segregate hitboxes by `material`.
- How to handle decor, which has a Material dependence, but does not conform to partitioning. Perhaps Decor should be a separate Craft category, due to the bespoke nature of the Asset file.
- Strut Frames (`frame-brick`, `frame-adobe`, etc.) do not exactly conform to the `material`, `purpose` schema due to the specialization of the Asset file. They may also be candidates for a separate Instance in the Craft Category.
- Materials: Enumeration of all game materials.
- MaterialFrame: Index Assets by material columns.
- PropertyState: `material` and `purpose` definition and specification. Logic handling.

