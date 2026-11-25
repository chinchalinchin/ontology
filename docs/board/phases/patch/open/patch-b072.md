##### Bug B072: `TypeError` Crash on Missing Inventory/Price Keys in `intentions/main.yaml` (`barter` and `mine`)

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/data/configurations/automata/intentions/main.yaml`:
1. `barter -> threaten` (line 32) evaluates `sprite.inventory.pouch.get(sprite.goal.name) < sprite.memory.prices.get(sprite.goal.name)`.
2. `mine -> build` (line 161) evaluates `sprite.inventory.pack.get(sprite.goal.name) > 0`.
3. `mine -> mine` (line 169) evaluates `sprite.inventory.pack.get(sprite.goal.name) == 0`.

When `sprite.goal.name` is absent from `pouch`, `pack`, or `prices`, `dict.get()` returns `None`. Comparing `None < float` or `None > 0` raises `TypeError` — which neither `CompilerExecutor` nor `LambdaExecutor` catches (they only catch `AttributeError`), crashing the Engine loop. Meanwhile `None == 0` evaluates to `False`, preventing `mine` persistence.

**Steps to Replicate**

1. Place an autonomous Sprite in `Intentions.MINE` with a `Goals.RESOURCE` whose `name` is not yet present in `sprite.state.inventory.pack`.
2. Run `TransitionMechanics.update()`.
3. Observe `TypeError: '>' not supported between instances of 'NoneType' and 'int'`.

**Proposed Remeditation**

Provide explicit numeric defaults in `intentions/main.yaml` (`sprite.inventory.pack.get(sprite.goal.name, 0) > 0`, `sprite.inventory.pack.get(sprite.goal.name, 0) == 0`, and `sprite.inventory.pouch.get(sprite.goal.name, 0) < sprite.memory.prices.get(sprite.goal.name, 0)`).
