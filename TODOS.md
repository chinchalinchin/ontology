- change all references of 'tile_units' to just 'units' or something. it no longer applies.

- compositions: tiles, struts, plates. specify relative positions in gropu dimensions and then need to resolve them down into their components so the rendering and updating algorithsm don't need updated.

- it would be nice if instead of dictionary state and configuration were kept in native python objects so values could be accessed with dot notation instead of dictionary key lookups.