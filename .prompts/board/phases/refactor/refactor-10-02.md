#### Refactor: Phase 10.02 - Shoreline Reindexing

**Overview**

Overhaul and respecification of Shoreline Frame to achieve the following:

- Integrate Shorelines with Seasonality by adding a compound field to the secondary key relation ShorelineIndex, so the Shoreline frame being rendered is a function of the three-tuple `(tile, fluid, season)`. 
- Shoreline Frames will still have Cardinal rows, but they will now have Season columns, i.e. a Shoreline is identified as a cell in a sheet by (Direction, Season)