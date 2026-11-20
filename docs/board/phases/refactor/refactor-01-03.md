#### Refactor: Phase 01.03 - Hierarchy Refinement

##### Notes

Although `Asset` (`src/app/assets/base.py`) is designed as a uniform component container, core systems bypass its strategy interfaces:

* **`Screen` Inspects Concrete State Types**: `Screen._assemble` (`src/app/game/screen.py`, line 157) checks `if not isinstance(asset.state, SheetState):` to suppress missing frame warnings for sparse equipment sheets. `Screen._widgets`, `Screen.stamp`, `Screen.bake`, and `Screen.release` (lines 213, 224, 250, 286, 294) repeatedly check `isinstance(widget.state, PaneState)`.

* **`Widget` Subclasses `Asset` to Override `dimensions`**: `src/app/game/menus/core.py` (lines 37–49) defines `class Widget(Asset)` solely to attach `binding` and branch on `if isinstance(self.state, PaneState): return self.state.span`.

* **Hardcoded Entity IDs and `getattr` Guards in Sheet Components**:
  * `SpriteFrame.keys` (`src/app/assets/frames/sheets.py`, line 103) checks `if id != RequiredAssets.PLAYER.value and state.psyche.expression:`.
  * `SpriteAnimation.animate` (`src/app/assets/animations/sheets.py`, line 32) is type-annotated for `state: SpriteState`, yet uses `if getattr(state, 'psyche', None) is None: return state` because `Player` is hydrated with `SheetState` (which lacks `psyche`) while sharing `SpriteAnimation` and `SpriteFrame`.
  * Meanwhile, `SheetState` (`src/app/models/state/assets/sheets.py`, lines 128–136) bundles `intention`, `character`, `inventory`, `meters`, and `goal` onto the base class for all `Sheets`, forcing `Pixies` (`docs/01-assets.md`, *Sheet: Pixies*) to inherit full character/inventory structures if they use `SheetState`.

* **Remediation**: Separate `SheetState` (strictly `position`, `velocity`, `animation`), `CharacterState(SheetState)` (adding `character`, `slots`, `inventory`, `meters`, `intention`, `goal` for `Player`), and `SpriteState(CharacterState)` (adding `psyche`, `memory`, `trajectory`). Give `Player` and `Sprite` distinct `Frame` and `Animation` recipes (or let `PlayerFrame` be `SpriteFrame` without expression overlays and `SpriteFrame` subclass `PlayerFrame`), eliminating `getattr` and `id != "player"` checks.
