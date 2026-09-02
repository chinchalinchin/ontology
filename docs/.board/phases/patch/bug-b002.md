# Bug B002: Board Cache Wipe on Layerless Assets

**STATUS**: OPEN
**SEVERITY**: CRITICAL

**Description**

In `Board.add()`, the engine ensures that newly injected Assets have their layers properly cached. However, the `AssetState` type definition allows `layer` to be `None`, which is commonly used for stateless or abstract assets (e.g., Equipment wrappers).

When an asset with `layer = None` is added, the condition `if layer not in self._cached_categories:` evaluates to `if None not in self._cached_categories:`. If `None` has not been registered yet, the Board calls `self._init_cache(layer=None)`.

Because `_init_cache(layer=None)` acts as the master reset switch for the entire database (designed for initial boot), it completely zeroes out `_cached_categories`, `_cached_instances`, and all other spatial tracking dictionaries. Injecting a single layerless asset mid-game will silently wipe the entire spatial cache for all layers, breaking `MotionMechanics`, `CollisionMechanics`, and rendering.

**Steps to Replicate**

1. Boot the Engine and hydrate a world state (e.g., `world-01`).
2. Add a standard Sprite to the Board.
3. Add a stateless Equipment Asset (or any Asset where `state.layer is None`) via `board.add()`.
4. Attempt to query `board.assets('layer-1')`. The cache will return a `KeyError` or an empty list.