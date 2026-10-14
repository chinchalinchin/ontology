### Valuation Model & Formal Assumptions

The crafting cost $C$ evaluates material quantities from an asset's 2D bounding footprint $w \times l$, parameterized by the engine's canonical grid cell and material-structural densities.

#### Axiomatic Assumptions

1. **Unit Footprint ($A_0$)**: $A_0 = 32 \times 32 = 1,024\text{ px}^2$, matching the engine's broad-phase spatial bucket size (`TILE_HASH_SIZE = 32`) and standard tile dimension.
2. **Normalized Footprint ($N$)**: The continuous tile area of an asset is:

$$N = \frac{w \cdot l}{A_0} = \frac{w \cdot l}{1024}$$


3. **Material Weight ($\mu_{\text{mat}}$)**: Dimensionless density and rarity scalar reflecting resource tier:
* Primary Construction (`wood`, `clay`, `stone`): $\mu = 1.00$
* Refined / Metamorphic (`marble`, `cotton`): $\mu = 1.50$
* Plating / Decorative Veneer (`gold`): $\mu = 0.20$


4. **Structural Volume Factor ($\delta_{\text{type}}$)**: Volumetric solidity relative to bounding area:
* Pavements & Substrates (`floors`): $\delta = 1.00$
* Enclosures & Facades (`walls`, `frames`): $\delta = 1.00$
* Fortified Parapets (`walls` with battlements/turrets): $\delta = 1.25$
* Dense Masonry & Load-Bearing Elements (`structures`: towers, turrets, buttresses, pillars, platforms): $\delta = 1.50$
* Overhead Coverings (`roofs`): $\delta = 0.80$
* Fenestrations & Framed Openings (`windows`): $\delta = 0.50$
* Linear Enclosures & Perimeters (`railings`, fences): $\delta = 0.50$



#### Governing Cost Formula

For single-material crafts:


$$Q = \max\left(1, \operatorname{round}\left(N \cdot \delta_{\text{type}} \cdot \mu_{\text{mat}}\right)\right)$$

For multi-material composites with decorative plating (e.g., gold-plated stone):


$$Q_{\text{base}} = \max\left(1, \operatorname{round}\left(N \cdot \delta_{\text{type}} \cdot \mu_{\text{base}}\right)\right)$$

$$Q_{\text{veneer}} = \max\left(1, \operatorname{round}\left(N \cdot \delta_{\text{type}} \cdot \mu_{\text{veneer}}\right)\right)$$

---

### Cost Valuation Calculations

| Asset ID | Dimensions ($w \times l$) | Area ($\text{px}^2$) | Footprint ($N$) | $\delta_{\text{type}}$ | Material | $\mu_{\text{mat}}$ | Prior Cost | Recalibrated Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Floors** |  |  |  |  |  |  |  |  |
| `floor-area-wood` | $128 \times 96$ | 12,288 | 12.00 | 1.00 | `wood` | 1.00 | 10 | **12 wood** |
| `floor-horizontal-stone` | $289 \times 81$ | 23,409 | 22.86 | 1.00 | `stone` | 1.00 | 100 | **23 stone** |
| `floor-area-carpet-palace` | $161 \times 160$ | 25,760 | 25.16 | 1.00 | `cotton` | 1.50 | 50 | **38 cotton** |
| `floor-area-marble-checkered` | $265 \times 166$ | 43,990 | 42.96 | 1.00 | `marble` | 1.50 | 100 | **64 marble** |
| `floor-vertical-marble-diamonds` | $66 \times 192$ | 12,672 | 12.38 | 1.00 | `marble` | 1.50 | 100 | **19 marble** |
| **Frames** |  |  |  |  |  |  |  |  |
| `frame-adobe` | $96 \times 160$ | 15,360 | 15.00 | 1.00 | `clay` | 1.00 | 10 | **15 clay** |
| `frame-brick` | $96 \times 190$ | 18,240 | 17.81 | 1.00 | `stone` | 1.00 | 10 | **18 stone** |
| **Railings** |  |  |  |  |  |  |  |  |
| `railing-horizontal-fence` | $72 \times 73$ | 5,256 | 5.13 | 0.50 | `wood` | 1.00 | 10 | **3 wood** |
| `railing-vertical-fence` | $8 \times 87$ | 696 | 0.68 | 0.50 | `wood` | 1.00 | 10 | **1 wood** |
| `railing-up-stone` | $206 \times 17$ | 3,502 | 3.42 | 0.50 | `stone` | 1.00 | 10 | **2 stone** |
| `railing-left-stone` | $17 \times 81$ | 1,377 | 1.34 | 0.50 | `stone` | 1.00 | 10 | **1 stone** |
| `railing-right-stone` | $17 \times 81$ | 1,377 | 1.34 | 0.50 | `stone` | 1.00 | 10 | **1 stone** |
| **Roofs** |  |  |  |  |  |  |  |  |
| `roof-slate` | $256 \times 127$ | 32,512 | 31.75 | 0.80 | `stone` | 1.00 | 100 | **25 stone** |
| **Structures** |  |  |  |  |  |  |  |  |
| `buttress-stone` | $190 \times 33$ | 6,270 | 6.12 | 1.50 | `stone` | 1.00 | 50 | **9 stone** |
| `tower-stone` | $32 \times 143$ | 4,576 | 4.47 | 1.50 | `stone` | 1.00 | 250 | **7 stone** |
| `turret-stone` | $66 \times 131$ | 8,646 | 8.44 | 1.50 | `stone` | 1.00 | 250 | **13 stone** |
| `pillar-marble` | $20 \times 96$ | 1,920 | 1.88 | 1.50 | `marble` | 1.50 | — | **4 marble** |
| `platform-marble` | $96 \times 111$ | 10,656 | 10.41 | 1.50 | `marble` | 1.50 | — | **23 marble** |
| **Walls** |  |  |  |  |  |  |  |  |
| `wall-up-blue` | $128 \times 96$ | 12,288 | 12.00 | 1.00 | `wood` | 1.00 | 10 | **12 wood** |
| `wall-up-palace` | $128 \times 96$ | 12,288 | 12.00 | 1.00 | `stone` | 1.00 | 10 | **12 stone** |
| `wall-up-stone` | $188 \times 80$ | 15,040 | 14.69 | 1.00 | `stone` | 1.00 | 100 | **15 stone** |
| `wall-up-stone-turret` | $222 \times 133$ | 29,526 | 28.83 | 1.25 | `stone` | 1.00 | 100 | **36 stone** |
| `wall-up-stone-gold-plated` | $196 \times 96$ | 18,816 | 18.38 | 1.00 | `stone` / `gold` | 1.0 / 0.2 | 10 / 10 | **18 stone, 4 gold** |
| `wall-slant-left-down-stone` | $112 \times 151$ | 16,912 | 16.52 | 1.00 | `stone` | 1.00 | 100 | **17 stone** |
| `wall-slant-right-down-stone` | $112 \times 151$ | 16,912 | 16.52 | 1.00 | `stone` | 1.00 | 100 | **17 stone** |
| **Windows** |  |  |  |  |  |  |  |  |
| `window-stone` | $254 \times 112$ | 28,448 | 27.78 | 0.50 | `stone` | 1.00 | 100 | **14 stone** |


### Documentation Blurb (`docs/01-assets.md#craft-valuation`)

```markdown
### Craft Valuation & Material Economics

Craft costs follow a square-footage valuation model indexed to canonical $32 \times 32$ pixel cells ($A_0 = 1,024\text{ px}^2$). Rather than arbitrary static thresholds, an asset's material consumption reflects its planar footprint, structural density, and material class:

$$Q = \max\left(1, \operatorname{round}\left(\frac{w \cdot l}{1024} \cdot \delta_{\text{type}} \cdot \mu_{\text{mat}}\right)\right)$$

#### Parameter Reference

- **Structural Factor ($\delta_{\text{type}}$)**:
  - `floors`, `walls`, `frames`: $1.00$
  - `roofs`: $0.80$
  - `windows`, `railings`: $0.50$
  - `structures` (pillars, platforms, buttresses, turrets, towers): $1.50$
  - Fortified parapets: $1.25$
- **Material Multiplier ($\mu_{\text{mat}}$)**:
  - Base structural substrates (`wood`, `stone`, `clay`): $1.00$
  - Processed / decorative masonry (`marble`, `cotton`): $1.50$
  - Surface veneers & gilding (`gold`): $0.20$

Composite items declare multiple `cost` entries by evaluating primary masonry at $\delta_{\text{type}} \cdot \mu_{\text{base}}$ and surface treatments at $\delta_{\text{type}} \cdot \mu_{\text{veneer}}$.

```