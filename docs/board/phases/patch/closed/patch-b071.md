##### Bug B071: `CognitionMechanics._project` Re-Assigns `WANDER` Goal Same Tick, Making `wander -> idle` Unreachable

**STATUS**: CLOSED
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py`, `update()` invokes `_resolve()` (line 170) before `_project()` (line 182). When a Sprite in `Intentions.WANDER` reaches its `Goals.POSITION` waypoint, `_resolve()` clears `sprite.state.goal = None` (line 277). On the same tick, `_project()` checks `elif intention == Intentions.WANDER: if not sprite.state.goal or self.complete(sprite, board):` (lines 512–513) and immediately assigns a new `wander` Goal before `TransitionMechanics` executes.

Because `sprite.state.goal` is never `None` when `TransitionMechanics` evaluates `wander`, the `wander -> idle` transition (`conditions: [not sprite.goal]`) in `src/data/configurations/automata/intentions/main.yaml` is completely unreachable. Once a Sprite enters `wander`, it remains trapped in `wander` indefinitely and never returns to `idle` to run `_ideate`, `_motivate`, or `Recall` (forcing ad-hoc `wander -> hunt` and `wander -> find` bypasses).

**Steps to Replicate**

1. Deploy a Sprite in `Intentions.WANDER` with `goal = Goal(name="wander", category=Goals.POSITION, layer=L, position=sprite.state.position)` and `psyche.dialogue = "greeting"`.
2. Execute `CognitionMechanics.update()` followed by `TransitionMechanics.update()`.
3. Observe `_resolve` clears the completed `wander` Goal, `_project` immediately creates a new `wander` Goal on the same tick, and `sprite.state.intention` stays `Intentions.WANDER` without ever transitioning to `Intentions.IDLE`.

**Proposed Remeditation**

Move `wander` Goal generation into `WanderInstinct` executing strictly during `IDLE`-only Acquisition (`sprite.state.intention == Intentions.IDLE and sprite.state.goal is None`). When `position.complete` or `position.lost` clears `sprite.state.goal` during `WANDER`, Acquisition is skipped so `TransitionMechanics` cleanly transitions `wander -> idle`, restoring the `idle` hub invariant and eliminating the need for `wander -> hunt` and `wander -> find` bypasses.

