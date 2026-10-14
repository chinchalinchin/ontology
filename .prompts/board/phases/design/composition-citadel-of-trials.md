#### Design: Composition - Citadel of Trials

!!! "context"

  Used during [Phase 07.03](../refactor/refactor-07-03.md) UAT Testing.

##### User Acceptance Gates

1. **West Wing — 3-Tier Stepped Cascade ($E = 3 \to E = 2 \to E = 1 \to E = 0$)**:

* **`sanctum-platform-e3-west`** (`platform-corinthian`, `elevation: 2`, $x \in [0, 96], y \in [0, 124]$): Walkable deck at $E = 3$ ($y \in [8, 124]$). Stepping South off $y = 125$ triggers freefall for $55\text{ px}$ to $y = 180$ (sprite hitbox $y \in [203, 224]$), transitioning $E: 3 \to 2$ and landing inside **`sanctum-platform-e2-west`**.
* **`sanctum-platform-e2-west`** (`platform-ionic`, `elevation: 1`, $x \in [0, 96], y \in [140, 264]$): Walkable deck at $E = 2$ ($y \in [148, 264]$). Stepping South off $y = 265$ drops $55\text{ px}$ to $y = 320$ (sprite hitbox $y \in [343, 364]$), transitioning $E: 2 \to 1$ and landing inside **`sanctum-platform-e1-west`**.
* **`sanctum-platform-e1-west`** (`platform-doric`, `elevation: 0`, $x \in [0, 96], y \in [280, 405]$): Walkable deck at $E = 1$ ($y \in [288, 405]$). Stepping South off $y = 406$ drops $55\text{ px}$ to $y = 461$, transitioning $E: 1 \to 0$ onto the ground substrate.


2. **Central Span — Elevated Sensor Strut Skywalk & 3-Tier Continuous Freefall ($E = 3 \to E = 0$)**:

* **`sanctum-skywalk-e3`** (`floor-stone`, `mass: -1`, `elevation: 3`, `anchor: -160`, $x \in [80, 369], y \in [16, 97]$): Tests `_extract_tier_support_primitives` for `AssetInstances.STRUTS` at $E = 3$ while negative `anchor` keeps its `ground_y` below $E = 3$ entities. Stepping South into the central courtyard ($x \in [120, 230], y = 98$), where no $E = 2$ or $E = 1$ substrate exists below, drops the entity continuously through $E = 2$ ($y = 153$) and $E = 1$ ($y = 208$) to land at $E = 0$ after $3 \times 55 = 165\text{ px}$ ($y = 263$).


3. **East Inner Lane — 2-Tier Skip Landing ($E = 3 \to E = 1$)**:

* **`sanctum-platform-e3-east`** (`platform-corinthian`, `elevation: 2`, $x \in [256, 352], y \in [0, 124]$, deck at $E = 3$) sits above **`sanctum-platform-e1-mid`** (`platform-marble`, `elevation: 0`, $x \in [256, 352], y \in [196, 307]$, deck at $E = 1$) with no $E = 2$ platform in between. Stepping South off $y = 125$ passes unsupported through $E = 2$ at $y = 180$ and lands on $E = 1$ after $2 \times 55 = 110\text{ px}$ at $y = 235$ (hitbox $y \in [258, 279] \subset [204, 307]$).

4. **East Ascent Column — Multi-Tier Stair Traversal ($E = 0 \leftrightarrow 1 \leftrightarrow 2 \leftrightarrow 3$)**:

* **`sanctum-stairs-e0-e1`** (`elevation: 0, delta: 1`), **`sanctum-stairs-e1-e2`** (`elevation: 1, delta: 1`), and **`sanctum-stairs-e2-e3`** (`elevation: 2, delta: 1`) connect `sanctum-platform-e1-east` ($E = 1$), `sanctum-platform-e2-east` ($E = 2$), and `sanctum-platform-e3-far-east` ($E = 3$).
* Because `_extract_tier_support_primitives` only registers stairs for `base_e < elevation <= base_e + delta`, sensor struts **`sanctum-underbridge-e1`** (`elevation: 1`) and **`sanctum-underbridge-e2`** (`elevation: 2`) span the stair footprints so downward traversal ($E: 3 \to 2$ and $E: 2 \to 1$) remains supported at the lower tier along the full stair length.

5. **Door Interaction Loop Isolation**:

| Source Door | Layer ($E$) | Door Footprint $[x_1, x_2] \times [y_1, y_2]$ | Destination Layer | `out` $(x, y)$ | Arrival Frame ($64 \times 64$) | Target Return Door Footprint | Clearance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `citadel-main-entrance` | `root.layer` ($0$) | $[62, 126] \times [16, 80]$ | `citadel-sanctum-layer` | $(192, 340)$ | $[192, 256] \times [340, 404]$ | $[192, 256] \times [420, 484]$ | $16\text{ px}$ |
| `sanctum-ground-exit` | `citadel-sanctum-layer` ($0$) | $[192, 256] \times [420, 484]$ | `bind(root.layer)` | $(62, 96)$ | $[62, 126] \times [96, 160]$ | $[62, 126] \times [16, 80]$ | $16\text{ px}$ |
| `exterior-balcony-door` | `root.layer` ($1$) | $[252, 284] \times [-60, -12]$ | `citadel-sanctum-layer` | $(356, 316)$ | $[356, 420] \times [316, 380]$ | $[356, 388] \times [252, 300]$ | $16\text{ px}$ |
| `sanctum-balcony-exit` | `citadel-sanctum-layer` ($1$) | $[356, 388] \times [252, 300]$ | `bind(root.layer)` | $(236, 12)$ | $[236, 300] \times [12, 76]$ | $[252, 284] \times [-60, -12]$ | $24\text{ px}$ |
| `sanctum-belfry-door` | `citadel-sanctum-layer` ($3$) | $[384, 416] \times [-28, 20]$ | `citadel-belfry-layer` | $(112, 160)$ | $[112, 176] \times [160, 224]$ | $[128, 160] \times [240, 288]$ | $16\text{ px}$ |
| `belfry-return-exit` | `citadel-belfry-layer` ($3$) | $[128, 160] \times [240, 288]$ | `citadel-sanctum-layer` | $(368, 28)$ | $[368, 432] \times [28, 92]$ | $[384, 416] \times [-28, 20]$ | $8\text{ px}$ |