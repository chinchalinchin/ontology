##### Bug B075: Aliased `Position` Reference in `CognitionMechanics._scan` & Unchecked `board.player()` Dereference

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py`:
1. Line 313 (`_scan`) assigns `sprite.state.memory.sprites[other_name] = other_state.position`, storing a live mutable reference to the other character's `Position` rather than a snapshot copy. Subsequent movement mutates `memory.sprites[other_name]` in place even after the character leaves `vision.radius` or changes Layers.
2. Line 165 (`update`) evaluates `if sprite.name == board.player().name:` inside the per-sprite loop without guarding `board.player() is None`, crashing with `AttributeError` on headless/NPC-only Boards without a deployed Player.

**Steps to Replicate**

1. Run `CognitionMechanics._scan` with Sprite A within `vision.radius` of Sprite B at `(100, 100)`.
2. Move Sprite B to `(500, 500)` outside `vision.radius` without running `_scan`.
3. Inspect `sprite_a.state.memory.sprites[sprite_b.name]` and observe `(500, 500)` instead of the last-observed `(100, 100)`.

**Proposed Remeditation**

Copy `(x, y)` coordinates into `memory.sprites[other_name]` in `Perception.scan` (updating an existing snapshot or allocating a new `Position`), and hoist `player = board.player()` with a `if player and sprite.name == player.name:` guard outside the sprite loop in `CognitionMechanics.update`.

*(Housekeeping note: the Bug Reports View currently contains two distinct open reports sharing ID `B064` — static goal subsumption in `_track` and `hunt` deadlock on Door substitution; renumbering the duplicate on the board is recommended.)*