
### Bug B033: `predicates.in_fluid` Short-Circuits Active Child Branches When Parent `fluid.state.length == 0`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

In `src/app/game/logic/predicates.py` (lines 134–142), `in_fluid(position, fluid)` checks `if fluid.state.length > 0 and in_stream(position, fluid):`. Inside `in_stream()`, parent corridor evaluation is already guarded by `if slen > 0:` (line 95), while child `fluid.state.branches` are evaluated independently (lines 107–125). If a fluid emitter's parent stream is immediately obstructed at `fluid.state.length == 0` while spawning active child branches (`branch.length > 0`), `in_fluid()` short-circuits before calling `in_stream()` and erroneously returns `False` for positions inside active branches.

**Steps to Replicate**

1. Instantiate a `fluid` asset at `Position(64, 64)` with `fluid.state.length = 0`, `fluid.state.pool = None`, and an active branch `Branch(position=Position(96, 64), source=Directions.DOWN.value, flow=1, length=64)`.
2. Observe that `predicates.in_stream(Position(100, 96), fluid)` returns `True`, whereas `predicates.in_fluid(Position(100, 96), fluid)` returns `False`.

**Proposed Remeditation**

Remove the redundant `fluid.state.length > 0` guard in `predicates.in_fluid()` and delegate directly to `if in_stream(position, fluid): return True`.