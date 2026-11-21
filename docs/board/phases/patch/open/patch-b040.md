##### Bug B040: Board Material Cache Repercussions

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

* `CraftProperties` defaults to `mass: int = 0`. Consequently, decorative or passable surface crafts (e.g., `floors`, `flats`, `paths`, `corridors`) satisfy $m \ge 0$ (`predicates.is_weight`) and are indexed into `board.weights(layer)`.
* Every tick, `CollisionMechanics.update` (and `fields.update`) iterates through all of these passable crafts and calls `w.hitbox.elevations(w.properties, w.state)` (**2.27 million calls**, **2.37%** of total runtime) just for `MaterialHitbox.elevations` to check `MaterialIndex().is_obstacle(state.blueprint)` and return `[]`.

**Proposed Remeditation**

* Filtering passable `MaterialHitbox` crafts out of `_cached_weights` at board indexing time (or caching `elevations` on the asset/cache) would eliminate over **2 million Python calls** per 100 seconds.
