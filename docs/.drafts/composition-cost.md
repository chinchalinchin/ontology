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

---

### Calibrated YAML Schema Updates

```yaml
# src/assets/crafts/struts/floors.yaml
crafts:
  struts:
    floor-area-carpet-palace:
      dimensions:
        w: 161
        l: 160
      mass: -1
      cost:
        - item: cotton
          quantity: 38
    floor-area-marble-checkered:
      dimensions: 
        w: 265
        l: 166
      mass: -1
      cost:
        - item: marble
          quantity: 64
    floor-area-wood:
      dimensions:
        w: 128
        l: 96
      mass: -1
      cost: 
        - item: wood
          quantity: 12
    floor-horizontal-stone:
      dimensions:
        w: 289
        l: 81
      mass: -1
      cost:
        - item: stone
          quantity: 23
    floor-vertical-marble-diamonds:
      dimensions:
        w: 66
        l: 192
      mass: -1
      cost:
        - item: marble
          quantity: 19

# src/assets/crafts/struts/frames.yaml
crafts:
  struts:
    frame-adobe:
      dimensions:
        w: 96
        l: 160
      mass: 0
      hitboxes:
        - position: { x: 0, y: 0 }
          dimensions: { w: 96, l: 160 }
      cost:
        - item: clay
          quantity: 15
    frame-brick:
      dimensions:
        w: 96
        l: 190
      mass: 0
      hitboxes:
        - position: { x: 10, y: 20 }
          dimensions: { w: 76, l: 144 }
      cost:
        - item: stone
          quantity: 18

# src/assets/crafts/struts/railings.yaml
crafts:
  struts:
    railing-horizontal-fence:
      dimensions:
        w: 72
        l: 73
      mass: 0
      hitboxes:
        - position: { x: 0, y: 0 }
          dimensions: { w: 72, l: 73 }
      cost:
        - item: wood
          quantity: 3
    railing-vertical-fence:
      dimensions:
        w: 8 
        l: 87
      mass: 0
      hitboxes:
        - position: { x: 0, y: 0 }
          dimensions: { w: 8, l: 87 }
      cost:
        - item: wood
          quantity: 1
    railing-up-stone:
      dimensions:
        w: 206
        l: 17
      mass: 0
      hitboxes:
        - position: { x: 0, y: 0 }
          dimensions: { w: 206, l: 17 }
      cost:
        - item: stone
          quantity: 2
    railing-left-stone:
      dimensions:
        w: 17
        l: 81
      mass: 0
      hitboxes:
        - position: { x: 0, y: 0 }
          dimensions: { w: 17, l: 81 }
      cost:
        - item: stone
          quantity: 1
    railing-right-stone:
      dimensions:
        w: 17
        l: 81
      mass: 0
      hitboxes:
        - position: { x: 0, y: 0 }
          dimensions: { w: 17, l: 81 }
      cost:
        - item: stone
          quantity: 1

# src/assets/crafts/struts/roofs.yaml
crafts:
  struts:
    roof-slate:
      dimensions:
        w: 256
        l: 127
      mass: 0
      hitboxes:
        - position: { x: 10, y: 10 }
          dimensions: { w: 230, l: 100 }
      cost:
        - item: stone
          quantity: 25

# src/assets/crafts/struts/structures.yaml
crafts:
  struts:
    buttress-stone:
      dimensions:
        w: 190
        l: 33
      mass: 0
      hitboxes:
        - position: { x: 10, y: 5 }
          dimensions: { w: 160, l: 20 }
      cost:
        - item: stone
          quantity: 9
    tower-stone:
      dimensions:
        w: 32
        l: 143
      mass: 0
      hitboxes:
        - position: { x: 4, y: 5 }
          dimensions: { w: 20, l: 110 }
      cost:
        - item: stone
          quantity: 7
    turret-stone:
      dimensions:
        w: 66
        l: 131
      mass: 0
      hitboxes:
        - position: { x: 10, y: 15 }
          dimensions: { w: 40, l: 100 }
      cost:
        - item: stone
          quantity: 13
    pillar-marble:
      dimensions:
        w: 20
        l: 96
      mass: 0
      hitboxes: null
      cost:
        - item: marble
          quantity: 4
    platform-marble:
      dimensions:
        w: 96
        l: 111
      mass: 0
      hitboxes: null
      cost:
        - item: marble
          quantity: 23

# src/assets/crafts/struts/walls.yaml
crafts:
  struts:
    wall-up-blue:
      dimensions:
        w: 128
        l: 96
      mass: 0
      cost: 
        - item: wood
          quantity: 12
      hitboxes:
        - position: { x: 6, y: 17 }
          dimensions: { w: 116, l: 54 }
    wall-up-palace:
      dimensions:
        w: 128
        l: 96
      mass: 0
      cost: 
        - item: stone
          quantity: 12
      hitboxes: null
    wall-up-stone:
      dimensions: 
        w: 188
        l: 80
      mass: 0
      cost: 
        - item: stone
          quantity: 15
      hitboxes:
        - position: { x: 8, y: 15 }
          dimensions: { w: 150, l: 40 }
    wall-up-stone-turret:
      dimensions:
        w: 222
        l: 133
      mass: 0
      cost: 
        - item: stone
          quantity: 36
      hitboxes:
        - position: { x: 178, y: 102 }
          dimensions: { w: 25, l: 12 }
        - position: { x: 17, y: 102 }
          dimensions: { w: 25, l: 12 }
        - position: { x: 5, y: 39 }
          dimensions: { w: 203, l: 63 }
    wall-up-stone-gold-plated:
      dimensions:
        w: 196
        l: 96
      mass: 0
      cost: 
        - item: stone
          quantity: 18
        - item: gold
          quantity: 4
      hitboxes: null
    wall-slant-left-down-stone:
      dimensions: 
        w: 112
        l: 151
      mass: 0
      cost: 
        - item: stone
          quantity: 17
      hitboxes: null
    wall-slant-right-down-stone:
      dimensions: 
        w: 112
        l: 151
      mass: 0
      cost: 
        - item: stone
          quantity: 17
      hitboxes: null

# src/assets/crafts/struts/windows.yaml
crafts:
  struts:
    window-stone:
      dimensions:
        w: 254
        l: 112
      mass: 0
      hitboxes:
        - position: { x: 10, y: 10 }
          dimensions: { w: 220, l: 90 }
      cost:
        - item: stone
          quantity: 14

```

---

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