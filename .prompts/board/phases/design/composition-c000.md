#### Design: Composition C000 - Castle Dawn

* **Purpose**: Testing Gravity and Elevation in Phase 07.03.
* **Description**: The fortress of Evil Empress Jasilynn. Should be brooding and imposing, but also elegant. Needs an atrium for visitors, stairwells to the roof and a throne room. Throne Asset is forth coming, so leave a spot empty for the throne.

### Architectural Overview: Composition C000 (`castle-dawn`)

`castle-dawn` models an $864 \times 768\text{ px}$ ($9 \times 8$ `mansion` grid) multi-elevation fortress on a unified layer so that entities can transition seamlessly between ground rooms (`elevation: 0`) and roof battlements (`elevation: 1`) to test **Phase 07.03 (Gravity & Elevation)**:

* **Ground Foundation & Bastion Perimeter (`elevation: 0`)**:
* **Root Strut (`castle-foundation`)**: A $9 \times 8$ `granite` `mansion` floor (`x: 0..864, y: 0..768`, `substrate: -2`).
* **Outer Bastion Walls**: $192\text{ px}$-thick West (`x: 0..192, y: 0..672`) and East (`x: 672..864, y: 0..672`) `granite` walls, a $96\text{ px}$-thick North sanctum wall (`x: 192..672, y: 0..96`), and South gatehouse walls (`x: 0..384` and `x: 480..864` at `y: 672..768`), anchored by four corner `granite` `tower` columns (`64x192`).
* **Grand Entrance (`x: 384..480, y: 672..768`)**: Framed by `feldspar` `pillar`s (`x: 384` and `x: 464`) with a central $64 \times 64\text{ px}$ `granite` `postern` gate (`x: 400, y: 688`) and interior `stone-switch` plate (`x: 424, y: 656`).


* **Visitors' Atrium (`x: 192..672, y: 384..672`, `elevation: 0`)**:
* Features an inlaid `marble` `avenue` border, a central crimson (`red`) processional `carpet` (`x: 384..480, y: 384..768`), six `feldspar` colonnade `pillar`s, and a `marble` `plaque` sign (`castle_dawn_atrium`).


* **Stairwells to the Roof (`elevation: 0` to `elevation: 1`)**:
* **North Ascent Stairwells (`blueprint: up`)**: Twin `marble` `steps` at `{ x: 192, y: 384 }` and `{ x: 608, y: 384 }` ascending from the Atrium (`elevation: 0`) onto the inner roof landings (`y: 288..384`, `elevation: 1`).
* **Lateral Bastion Stairwells (`blueprint: left` / `right`)**: Twin `feldspar` `steps` at `{ x: 192, y: 576 }` (`left`) and `{ x: 608, y: 576 }` (`right`) ascending from the Atrium side courts onto the West (`x: 0..192`) and East (`x: 672..864`) roof bastions (`elevation: 1`), exercising all three `inclines` blueprints (`up`, `left`, `right`).


* **Throne Room (`x: 192..672, y: 96..288`, `elevation: 0`)**:
* Separated from the Atrium by a `feldspar` `halls` partition (`y: 288..384`) with a central $96\text{ px}$ archway (`x: 384..480`).
* Paved with crimson `hallway` flooring (`x: 192..672, y: 96..288`) and a striped `red` `carpet` runner leading to a $96 \times 96\text{ px}$ inlaid `marble` `avenue` **Throne Dais** at `x: 384..480, y: 96..192`.
* **Empty Throne Footprint**: The $96 \times 96\text{ px}$ dais (`x: 384..480, y: 96..192`, center `{ x: 432, y: 144 }`) is left completely clear for the forthcoming Throne Asset, flanked outside its bounds by `feldspar` `pillar`s (`x: 352` and `x: 496`), `gold` `trunk` chests (`x: 256` and `x: 576`), and an imperial `poster` decree (`empress_jasilynn_decree`).


* **Walkable Roof & Gravity Drop Zones (`elevation: 1`)**:
* Seven branch struts with `blueprint: flats` (`elevation: 1`, `substrate: -2`) sit directly over the `elevation: 0` solid bastion and partition walls (`x: 0..192`, `x: 672..864`, `y: 0..96`, `y: 288..384`, and `y: 672..768`) so they never occlude the open `elevation: 0` Atrium or Throne Room.
* Outer edges are fortified with `granite` `crenellation`s (`elevation: 1`), while inner roof edges overlooking the Atrium and Throne Room leave intentional unrailed drop-offs so stepping off the `flats` deck tests **Gravity** back down to `elevation: 0`.



---

### 1. Composition Configuration

**Location**: `src/data/config/compositions/main.yaml`

```yaml
compositions:
  castle-dawn:
    # =========================================================================
    # ROOT: GROUND FOUNDATION, ATRIUM, STAIRWELLS & THRONE ROOM (ELEVATION 0)
    # =========================================================================
    root:
      strut:
        id: mansion
        name: castle-foundation
        material: granite
        blueprint: floors
        elevation: 0
        multiple:
          nx: 9
          ny: 8
      components:
        crafts:
          struts:
            # -----------------------------------------------------------------
            # OUTER FORTRESS BASTION WALLS (ELEVATION 0)
            # -----------------------------------------------------------------
            - id: mansion
              name: west-bastion-wall
              material: granite
              blueprint: walls
              elevation: 0
              position:
                x: 0
                y: 0
              multiple:
                nx: 2
                ny: 7
            - id: mansion
              name: east-bastion-wall
              material: granite
              blueprint: walls
              elevation: 0
              position:
                x: 672
                y: 0
              multiple:
                nx: 2
                ny: 7
            - id: mansion
              name: north-sanctum-wall
              material: granite
              blueprint: walls
              elevation: 0
              position:
                x: 192
                y: 0
              multiple:
                nx: 5
                ny: 1
            - id: mansion
              name: southwest-gatehouse-wall
              material: granite
              blueprint: walls
              elevation: 0
              position:
                x: 0
                y: 672
              multiple:
                nx: 4
                ny: 1
            - id: mansion
              name: southeast-gatehouse-wall
              material: granite
              blueprint: walls
              elevation: 0
              position:
                x: 480
                y: 672
              multiple:
                nx: 4
                ny: 1

            # -----------------------------------------------------------------
            # CORNER WATCHTOWERS (64x192 EXPANSION COLUMNS, ELEVATION 0)
            # -----------------------------------------------------------------
            - id: tower
              name: northwest-watchtower
              material: granite
              elevation: 0
              position:
                x: 0
                y: 0
              multiple:
                nx: 1
                ny: 1
            - id: tower
              name: northeast-watchtower
              material: granite
              elevation: 0
              position:
                x: 800
                y: 0
              multiple:
                nx: 1
                ny: 1
            - id: tower
              name: southwest-watchtower
              material: granite
              elevation: 0
              position:
                x: 0
                y: 576
              multiple:
                nx: 1
                ny: 1
            - id: tower
              name: southeast-watchtower
              material: granite
              elevation: 0
              position:
                x: 800
                y: 576
              multiple:
                nx: 1
                ny: 1

            # -----------------------------------------------------------------
            # INTERIOR THRONE ROOM PARTITION WALLS (ELEVATION 0)
            # -----------------------------------------------------------------
            - id: mansion
              name: throne-partition-west
              material: feldspar
              blueprint: halls
              elevation: 0
              position:
                x: 192
                y: 288
              multiple:
                nx: 2
                ny: 1
            - id: mansion
              name: throne-partition-east
              material: feldspar
              blueprint: halls
              elevation: 0
              position:
                x: 480
                y: 288
              multiple:
                nx: 2
                ny: 1

            # -----------------------------------------------------------------
            # VISITORS' ATRIUM PAVING, CARPET & COLONNADE (ELEVATION 0)
            # -----------------------------------------------------------------
            - id: avenue
              name: atrium-west-colonnade-walk
              material: marble
              blueprint: designs
              elevation: 0
              position:
                x: 288
                y: 384
              multiple:
                nx: 3
                ny: 9
            - id: avenue
              name: atrium-east-colonnade-walk
              material: marble
              blueprint: designs
              elevation: 0
              position:
                x: 480
                y: 384
              multiple:
                nx: 3
                ny: 9
            - id: carpet
              name: atrium-processional-carpet
              material: red
              blueprint: designs
              elevation: 0
              position:
                x: 384
                y: 384
              multiple:
                nx: 1
                ny: 4
            - id: pillar
              name: gate-pillar-west
              material: feldspar
              elevation: 0
              position:
                x: 384
                y: 672
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: gate-pillar-east
              material: feldspar
              elevation: 0
              position:
                x: 464
                y: 672
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: atrium-pillar-sw
              material: feldspar
              elevation: 0
              position:
                x: 336
                y: 576
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: atrium-pillar-se
              material: feldspar
              elevation: 0
              position:
                x: 512
                y: 576
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: atrium-pillar-nw
              material: feldspar
              elevation: 0
              position:
                x: 336
                y: 480
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: atrium-pillar-ne
              material: feldspar
              elevation: 0
              position:
                x: 512
                y: 480
              multiple:
                nx: 1
                ny: 1

            # -----------------------------------------------------------------
            # THRONE ROOM FLOORING, DAIS & ROYAL COLONNADE (ELEVATION 0)
            # Note: Central Dais (x: 384..480, y: 96..192) is left empty
            #       to receive the forthcoming Throne Asset.
            # -----------------------------------------------------------------
            - id: hallway
              name: throne-room-floor
              material: red
              blueprint: solids
              elevation: 0
              position:
                x: 192
                y: 96
              multiple:
                nx: 5
                ny: 2
            - id: carpet
              name: throne-room-runner
              material: red
              blueprint: stripes
              elevation: 0
              position:
                x: 384
                y: 192
              multiple:
                nx: 1
                ny: 2
            - id: avenue
              name: throne-empty-dais
              material: marble
              blueprint: designs
              elevation: 0
              position:
                x: 384
                y: 96
              multiple:
                nx: 3
                ny: 3
            - id: pillar
              name: throne-arch-pillar-west
              material: feldspar
              elevation: 0
              position:
                x: 384
                y: 288
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: throne-arch-pillar-east
              material: feldspar
              elevation: 0
              position:
                x: 464
                y: 288
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: throne-dais-pillar-west
              material: feldspar
              elevation: 0
              position:
                x: 352
                y: 96
              multiple:
                nx: 1
                ny: 1
            - id: pillar
              name: throne-dais-pillar-east
              material: feldspar
              elevation: 0
              position:
                x: 496
                y: 96
              multiple:
                nx: 1
                ny: 1

          # -------------------------------------------------------------------
          # STAIRWELLS TO THE ROOF (ELEVATION 0 -> ELEVATION 1)
          # -------------------------------------------------------------------
          stairs:
            - id: steps
              name: west-roof-stairs
              material: marble
              blueprint: up
              delta: 1
              elevation: 0
              position:
                x: 192
                y: 384
              multiple:
                nx: 1
                ny: 1
            - id: steps
              name: east-roof-stairs
              material: marble
              blueprint: up
              delta: 1
              elevation: 0
              position:
                x: 608
                y: 384
              multiple:
                nx: 1
                ny: 1
            - id: steps
              name: southwest-bastion-stairs
              material: feldspar
              blueprint: left
              delta: 1
              elevation: 0
              position:
                x: 192
                y: 576
              multiple:
                nx: 1
                ny: 1
            - id: steps
              name: southeast-bastion-stairs
              material: feldspar
              blueprint: right
              delta: 1
              elevation: 0
              position:
                x: 608
                y: 576
              multiple:
                nx: 1
                ny: 1

        # ---------------------------------------------------------------------
        # GROUND LEVEL OBJECTS: GATES, PLATES, CHESTS & SIGNS (ELEVATION 0)
        # ---------------------------------------------------------------------
        objects:
          gates:
            - id: postern
              name: atrium-main-gate
              material: granite
              elevation: 0
              switch: true
              link: atrium-gate-plate
              position:
                x: 400
                y: 688
          plates:
            - id: stone-switch
              name: atrium-gate-plate
              material: granite
              elevation: 0
              switch: true
              link: atrium-main-gate
              position:
                x: 424
                y: 656
          chests:
            - id: trunk
              name: throne-treasury-west
              material: gold
              elevation: 0
              switch: false
              content: []
              position:
                x: 256
                y: 112
            - id: trunk
              name: throne-treasury-east
              material: gold
              elevation: 0
              switch: false
              content: []
              position:
                x: 576
                y: 112
            - id: trunk
              name: atrium-guard-chest-west
              material: iron
              elevation: 0
              switch: false
              content: []
              position:
                x: 208
                y: 624
            - id: trunk
              name: atrium-guard-chest-east
              material: iron
              elevation: 0
              switch: false
              content: []
              position:
                x: 624
                y: 624
          signs:
            - id: plaque
              name: atrium-welcome-plaque
              material: marble
              elevation: 0
              persona: castle_dawn_atrium
              lexicon: spring
              position:
                x: 356
                y: 540
            - id: poster
              name: throne-imperial-decree
              material: red
              elevation: 0
              persona: empress_jasilynn_decree
              lexicon: spring
              position:
                x: 304
                y: 112

    # =========================================================================
    # BRANCHES: WALKABLE ROOF BASTIONS, LANDINGS & BATTLEMENTS (ELEVATION 1)
    # =========================================================================
    branches:
      # -----------------------------------------------------------------------
      # 1. WEST ROOF BASTION DECK (x: 0..192, y: 0..768, ELEVATION 1)
      # -----------------------------------------------------------------------
      - strut:
          id: mansion
          name: west-roof-bastion
          material: granite
          blueprint: flats
          elevation: 1
          position:
            x: 0
            y: 0
          multiple:
            nx: 2
            ny: 8
        components:
          crafts:
            struts:
              - id: avenue
                name: west-roof-walkway
                material: feldspar
                blueprint: stripes
                elevation: 1
                position:
                  x: 64
                  y: 64
                multiple:
                  nx: 2
                  ny: 20
              - id: crenellation
                name: west-roof-outer-battlement
                material: granite
                blueprint: vertical
                elevation: 1
                position:
                  x: 0
                  y: 0
                multiple:
                  nx: 1
                  ny: 24
              - id: crenellation
                name: west-roof-north-battlement
                material: granite
                blueprint: horizontal
                elevation: 1
                position:
                  x: 0
                  y: 0
                multiple:
                  nx: 6
                  ny: 1
              - id: crenellation
                name: west-roof-south-battlement
                material: granite
                blueprint: horizontal
                elevation: 1
                position:
                  x: 0
                  y: 736
                multiple:
                  nx: 6
                  ny: 1
          objects:
            signs:
              - id: plaque
                name: roof-overlook-plaque
                material: feldspar
                elevation: 1
                persona: castle_dawn_roof
                lexicon: spring
                position:
                  x: 144
                  y: 336

      # -----------------------------------------------------------------------
      # 2. EAST ROOF BASTION DECK (x: 672..864, y: 0..768, ELEVATION 1)
      # -----------------------------------------------------------------------
      - strut:
          id: mansion
          name: east-roof-bastion
          material: granite
          blueprint: flats
          elevation: 1
          position:
            x: 672
            y: 0
          multiple:
            nx: 2
            ny: 8
        components:
          crafts:
            struts:
              - id: avenue
                name: east-roof-walkway
                material: feldspar
                blueprint: stripes
                elevation: 1
                position:
                  x: 64
                  y: 64
                multiple:
                  nx: 2
                  ny: 20
              - id: crenellation
                name: east-roof-outer-battlement
                material: granite
                blueprint: vertical
                elevation: 1
                position:
                  x: 160
                  y: 0
                multiple:
                  nx: 1
                  ny: 24
              - id: crenellation
                name: east-roof-north-battlement
                material: granite
                blueprint: horizontal
                elevation: 1
                position:
                  x: 0
                  y: 0
                multiple:
                  nx: 6
                  ny: 1
              - id: crenellation
                name: east-roof-south-battlement
                material: granite
                blueprint: horizontal
                elevation: 1
                position:
                  x: 0
                  y: 736
                multiple:
                  nx: 6
                  ny: 1

      # -----------------------------------------------------------------------
      # 3. NORTH ROOF RAMPART BRIDGE (x: 192..672, y: 0..96, ELEVATION 1)
      #    Note: Southern edge (y: 96) is left unrailed over the Throne Room
      #          to allow Gravity drop testing from Elevation 1 -> Elevation 0.
      # -----------------------------------------------------------------------
      - strut:
          id: mansion
          name: north-roof-rampart
          material: granite
          blueprint: flats
          elevation: 1
          position:
            x: 192
            y: 0
          multiple:
            nx: 5
            ny: 1
        components:
          crafts:
            struts:
              - id: avenue
                name: north-rampart-runner
                material: marble
                blueprint: designs
                elevation: 1
                position:
                  x: 0
                  y: 32
                multiple:
                  nx: 15
                  ny: 1
              - id: crenellation
                name: north-rampart-outer-battlement
                material: granite
                blueprint: horizontal
                elevation: 1
                position:
                  x: 0
                  y: 0
                multiple:
                  nx: 15
                  ny: 1
          objects:
            chests:
              - id: trunk
                name: north-rampart-cache
                material: gold
                elevation: 1
                switch: false
                content: []
                position:
                  x: 224
                  y: 32

      # -----------------------------------------------------------------------
      # 4. WEST STAIRWELL ROOF LANDING (x: 192..384, y: 288..384, ELEVATION 1)
      #    Receives ascents from west-roof-stairs (x: 192, y: 384).
      #    Leaves north/east edges open for Gravity drop testing.
      # -----------------------------------------------------------------------
      - strut:
          id: mansion
          name: west-stair-roof-landing
          material: feldspar
          blueprint: flats
          elevation: 1
          position:
            x: 192
            y: 288
          multiple:
            nx: 2
            ny: 1
        components:
          crafts:
            struts:
              - id: avenue
                name: west-landing-inlay
                material: marble
                blueprint: designs
                elevation: 1
                position:
                  x: 0
                  y: 32
                multiple:
                  nx: 6
                  ny: 1

      # -----------------------------------------------------------------------
      # 5. EAST STAIRWELL ROOF LANDING (x: 480..672, y: 288..384, ELEVATION 1)
      #    Receives ascents from east-roof-stairs (x: 608, y: 384).
      #    Leaves north/west edges open for Gravity drop testing.
      # -----------------------------------------------------------------------
      - strut:
          id: mansion
          name: east-stair-roof-landing
          material: feldspar
          blueprint: flats
          elevation: 1
          position:
            x: 480
            y: 288
          multiple:
            nx: 2
            ny: 1
        components:
          crafts:
            struts:
              - id: avenue
                name: east-landing-inlay
                material: marble
                blueprint: designs
                elevation: 1
                position:
                  x: 0
                  y: 32
                multiple:
                  nx: 6
                  ny: 1

      # -----------------------------------------------------------------------
      # 6. SOUTH-WEST GATEHOUSE ROOF (x: 192..384, y: 672..768, ELEVATION 1)
      # -----------------------------------------------------------------------
      - strut:
          id: mansion
          name: southwest-gatehouse-roof
          material: granite
          blueprint: flats
          elevation: 1
          position:
            x: 192
            y: 672
          multiple:
            nx: 2
            ny: 1
        components:
          crafts:
            struts:
              - id: crenellation
                name: southwest-gatehouse-battlement
                material: granite
                blueprint: horizontal
                elevation: 1
                position:
                  x: 0
                  y: 64
                multiple:
                  nx: 6
                  ny: 1

      # -----------------------------------------------------------------------
      # 7. SOUTH-EAST GATEHOUSE ROOF (x: 480..672, y: 672..768, ELEVATION 1)
      # -----------------------------------------------------------------------
      - strut:
          id: mansion
          name: southeast-gatehouse-roof
          material: granite
          blueprint: flats
          elevation: 1
          position:
            x: 480
            y: 672
          multiple:
            nx: 2
            ny: 1
        components:
          crafts:
            struts:
              - id: crenellation
                name: southeast-gatehouse-battlement
                material: granite
                blueprint: horizontal
                elevation: 1
                position:
                  x: 0
                  y: 64
                multiple:
                  nx: 6
                  ny: 1

```

---

### 2. Library Configuration (Sign Personas & Seasonal Lexicons)

Per the **Asset Guidelines**, each Sign Persona declared in `castle-dawn` (`castle_dawn_atrium`, `empress_jasilynn_decree`, and `castle_dawn_roof`) defines all four required seasonal lexicon keys (`spring`, `summer`, `autumn`, `winter`) under the active plot key in `src/data/config/library/main.yaml`.

**Location**: `src/data/config/library/main.yaml`

```yaml
library:
  default:
    castle_dawn_atrium:
      spring: "CASTLE DAWN — ATRIUM OF THE CRIMSON AURORA. Petitioners to Empress Jasilynn must await audience beneath the feldspar colonnade. Ascend the marble stairwells only by imperial writ."
      summer: "CASTLE DAWN — ATRIUM OF THE CRIMSON AURORA. Though the solstice sun warms the granite bastions, the Empress's judgment remains unyielding. Keep to the crimson carpet."
      autumn: "CASTLE DAWN — ATRIUM OF THE CRIMSON AURORA. Harvest tributes for the Crown must be cataloged in the iron trunks before approaching the northern sanctum."
      winter: "CASTLE DAWN — ATRIUM OF THE CRIMSON AURORA. Mind the frost upon the upper stairwells; the parapet overlooks are unrailed and the drop to the flagstones is unforgiving."
    empress_jasilynn_decree:
      spring: "BY DECREE OF EMPRESS JASILYNN: The Obsidian Throne is being forged anew in red feldspar and gold. None shall step upon the marble dais on pain of exile."
      summer: "BY DECREE OF EMPRESS JASILYNN: All provinces within sight of the Dawn Ramparts owe fealty and tithe to the Sovereign Sanctum."
      autumn: "BY DECREE OF EMPRESS JASILYNN: Let the banners of Castle Dawn hang heavy as the dusk; those who falter in service shall be cast from the high battlements."
      winter: "BY DECREE OF EMPRESS JASILYNN: In the season of long shadows, the Empress watches from the northern parapet. Kneel before the empty dais."
    castle_dawn_roof:
      spring: "PARAPET WARNING: The inner atrium ledges are unguarded during spring thaw. Step beyond the feldspar masonry at your own peril."
      summer: "PARAPET WARNING: High winds sweep the Castle Dawn battlements. Maintain footing near the atrium drop-off."
      autumn: "PARAPET WARNING: Falling leaves obscure the parapet brink. A single misstep plunges straight to the lower court."
      winter: "PARAPET WARNING: Ice coats the upper granite flats. Stepping off the inner ledge will drop you directly to the ground tier."

```

---

### 3. Asset Property & Material Index Adjustments

Per the **Indexing Guidelines**, the following property and material adjustments ensure proper hitboxes, intra-substrate render priorities, and sensor behavior for the Assets used in `castle-dawn`:

1. **`src/assets/crafts/stairs/main.yaml`**:
* Expand `steps` hitboxes (`up`, `left`, `right`) to span the full $64 \times 96\text{ px}$ footprint so players entering from any point along the staircase width/length trigger elevation transitions reliably.
* Set `priority: 2` so `steps` (`substrate: -1`) always renders above adjacent `corridors` (`carpet`, `avenue`, `hallway`, `substrate: -1`).



```yaml
crafts:
  stairs:
    steps:
      dimensions:
        w: 64
        l: 96
      priority: 2
      mass: -1
      material:
        genus: geologics
      blueprints: inclines
      hitboxes:
        up:
          - position:
              x: 0
              y: 0
            dimensions:
              w: 64
              l: 96
        left:
          - position:
              x: 0
              y: 0
            dimensions:
              w: 64
              l: 96
        right:
          - position:
              x: 0
              y: 0
            dimensions:
              w: 64
              l: 96

```

2. **`src/assets/crafts/struts/main.yaml`** (Priority Adjustments):
* Set `priority: 1` on `avenue` and `carpet` so decorative runners on `substrate: -1` always render on top of `hallway` base floors (`priority: 0`, `substrate: -1`) when sharing a baseline.
* Set `priority: 1` on `pillar` and `tower`, and `priority: 2` on `crenellation`, so columns, watchtowers, and battlements on `substrate: 0` always render cleanly in front of coplanar `walls` and `halls` (`priority: 0`, `substrate: 0`).



```yaml
    avenue:
      dimensions:
        w: 32
        l: 32
      priority: 1
      mass: 0
      hitboxes: null
      material:
        genus: geologics
      blueprints: corridors
    # -----------------------------------------
    carpet:
      dimensions:
        w: 96
        l: 96
      priority: 1
      mass: 0
      hitboxes: null
      material:
        genus: chromatics
        host: cotton
      blueprints: corridors
    # -----------------------------------------
    pillar:
      dimensions:
        w: 16
        l: 32
      priority: 1
      mass: 0
      hitboxes: null
      material:
        genus: geologics
      blueprints: columns
    # -----------------------------------------
    tower:
      dimensions:
        w: 64
        l: 64
      priority: 1
      mass: 0
      hitboxes: null
      material:
        genus: geologics
      blueprints: columns
    # -----------------------------------------
    crenellation:
      dimensions:
        w: 32
        l: 32
      priority: 2
      mass: 0
      material:
        genus: geologics
      blueprints: orientations
      hitboxes:
        horizontal:
          - position:
              x: 0
              y: 0
            dimensions:
              w: 32
              l: 10
        vertical:
          - position:
              x: 0
              y: 0
            dimensions:
              w: 9
              l: 32

```

3. **`src/assets/objects/plates/main.yaml` & `src/data/config/materials/main.yaml**`:
* Add `material: { genus: geologics }` to `stone-switch` in `src/assets/objects/plates/main.yaml` and register `plates: -1` under `materials.substrates` in `src/data/config/materials/main.yaml` so pressure plates render on `Substrates.OVERLAYS (-1)` beneath sprites rather than occluding sprites on `Substrates.STANDARD (0)`.



```yaml
# src/assets/objects/plates/main.yaml
objects:
  plates:
    stone-switch:
      mass: -1
      dimensions:
        w: 15
        l: 14
      count: 2
      material:
        genus: geologics
      hitboxes: null

```

---

### 4. Codebase Bug Reports

##### Bug B017: Door Shadow Projection `ChannelTypes.TINT` Tuple Unpacking Crash

**STATUS**: OPEN
**SEVERITY**: CRITICAL

**Description**

In `app/assets/frames/objects.py`, `ObjectFrame.channels()` emits a 5-element tuple `(0, 0, 0, 0, 110)` for `ChannelTypes.TINT` when `isinstance(state, DoorState) and state.projection == LayerProjections.OUT.value`. However, in `app/game/screen.py`, `Screen.draw()` unpacks `ChannelTypes.TINT` payloads into 8 variables (`ox, oy, ow, ol, r, g, b, a = payload`). Rendering any layer that contains a projected `out` door shadow immediately raises `ValueError: not enough values to unpack (expected 8, got 5)`.

**Steps to Replicate**

1. Instantiate or decompose any `Door` asset with `outlayer` and `out` configured so `Decomposer.project_door()` creates its reciprocal shadow door (`projection = 'out'`).
2. Render the layer containing the `out` door projection via `Screen.draw()`.
3. Observe `ValueError: not enough values to unpack (expected 8, got 5)` at `app/game/screen.py:255`.

**Proposed Remeditation**

Update `ObjectFrame.channels()` in `app/assets/frames/objects.py` to emit the full 8-tuple `(ox, oy, ow, ol, r, g, b, a)` using `properties.dimensions.w` and `properties.dimensions.l`:

```python
if isinstance(state, DoorState) and state.projection == LayerProjections.OUT.value:
    w = properties.dimensions.w if properties.dimensions else 0
    l = properties.dimensions.l if properties.dimensions else 0
    directives.append((
        ChannelTypes.TINT.value,
        (0, 0, w, l, 0, 0, 0, 110)
    ))

```

##### Bug B018: Stairs Only Emit Hitboxes at Base Elevation Preventing Descent

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `app/assets/hitboxes/crafts.py`, `MaterialHitbox.elevations()` and `MaterialHitbox.get()` only emit hitboxes at `target_e = max(0, state.elevation)`. When a Sprite ascends a `steps` asset (`StairState`) from `elevation = 0` with `delta = 1`, the Sprite's elevation becomes `1`. Because the stair's `MaterialHitbox` returns `[]` for `elevation = 1`, the Sprite can no longer intersect the stair sensor at `elevation = 1` to descend back to `elevation = 0` (and in `Ontology Docs: Assets`, the descent velocity condition for `up` and `down` stairs also typos `vx` instead of `vy`).

**Steps to Replicate**

1. Deploy a `steps` Craft (`elevation = 0, delta = 1, blueprint = 'up'`) leading to an `elevation = 1` surface.
2. Move a Sprite north (`vy` less than `0`) onto `steps` so its `elevation` transitions from `0` to `1`.
3. Move the Sprite south (`vy` greater than `0`) onto `steps` from `elevation = 1` and observe that `steps.hitbox.get(properties, state, elevation=1)` returns `[]`, preventing descent.

**Proposed Remeditation**

In `MaterialHitbox.elevations()` and `MaterialHitbox.get()` (or a dedicated `StairHitbox` schema), include both endpoints of `StairState` transitions (`base_e` and `base_e + state.delta`):

```python
if isinstance(state, StairState):
    base_e = max(0, state.elevation if state.elevation is not None else 0)
    return [base_e, max(0, base_e + state.delta)]

```

##### Bug B019: Decomposer `anchor(parent)` Double-Counts Branch `pseudo_y`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `app/services/generators/game/decomposer.py`, `_resolve_anchor()` computes `self_y = self_state.position.y`, which for a component of a branch strut is already expressed in the local coordinate frame of `parent` (where the parent strut's local origin is `y = 0`). However, when `target_ref == "parent"`, `_resolve_anchor()` sets `target_y = parent_context.get("pseudo_y", 0)` instead of `0`. This shifts the computed `anchor` of every component using `anchor(parent)` inside a branch strut by `parent.pseudo_y`, corrupting its `ground_y` sort order whenever `parent.pseudo_y != 0`.

**Steps to Replicate**

1. Define a Composition branch whose `strut` has `position: { x: 0, y: 200 }` and `dimensions.l = 96`.
2. Add a child component on that branch with `position: { x: 0, y: 48 }`, `dimensions.l = 48`, and `anchor: anchor(parent)`.
3. Unpack the Composition via `Decomposer.unpack()` and observe that `component.state.anchor` resolves to `200` instead of `0`, yielding `ground_y = 596` instead of `396`.

**Proposed Remeditation**

In `Decomposer._resolve_anchor()`, set `target_y = 0` when `target_ref == "parent"` (since `self_y` is already relative to `parent`), and when `target_ref == "root"` on a same-layer branch component, account for `parent_context.get("pseudo_y", 0)` in the child's offset from `root`.

##### Bug B020: Decomposer `_multiply_expansion` and `_multiply_perimeter` Overwrite `state.anchor`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `app/services/generators/game/decomposer.py`, `_multiply_simple()` preserves `base_anchor = int(state.anchor or 0)`, but `_multiply_expansion()` sets `seg_anchor = int(base_ground - (seg_y + l))` and `_multiply_perimeter()` sets `north_anchor = int(north_bottom - l)` (and `0` for `south`, `east`, `west`) without adding `int(state.anchor or 0)`. Any explicit `anchor` or `anchor(...)` macro configured on `columns` (`pillar`, `tower`) or `enclosures` (`palisade`) is discarded during multiplication.

**Steps to Replicate**

1. Configure a `pillar` or `tower` component in a Composition with a non-zero `anchor` (e.g., `anchor: 32` or `anchor: anchor(parent)`).
2. Unpack via `Decomposer.multiply()` and inspect the spawned `crowns`, `shafts`, and `bases` units.
3. Observe that `state.anchor` on the parent state was ignored rather than added to each segment's `seg_anchor`.

**Proposed Remeditation**

In `_multiply_expansion()` and `_multiply_perimeter()`, compute `base_anchor = int(state.anchor or 0)` and add `base_anchor` to the segment anchor passed to `self._spawn_unit()`.

##### Bug B021: `Decomposer._hydrate_state` Fails to Namespace `SwitchState.link`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

When `Decomposer._hydrate_state()` unpacks components in a Composition, it rewrites each component's `name` to `<base_inst>-<parent_name>-<comp_name>-<inc>` (e.g., `gate-strut-castle-foundation-1-atrium-main-gate-1`). However, `_hydrate_state()` does not transform the `link` attribute on `SwitchState` (`Gate` and `Plate` assets), leaving `state.link` as the raw pseudo-state string (`atrium-main-gate`). Consequently, plates and gates unpacked from a Composition cannot resolve their linked target on the `Board`.

**Steps to Replicate**

1. Add a `Plate` (`link: my-gate`) and a `Gate` (`name: my-gate`) to a Composition.
2. Unpack the Composition onto the `Board`.
3. Observe that the `Gate` is named `gate-strut-<root>-1-my-gate-1`, while `plate.state.link` remains `'my-gate'`, causing lookup of the linked gate to fail.

**Proposed Remeditation**

In `Decomposer._unpack_components()`, resolve `SwitchState.link` against `scope_lookup` (or across a composition-wide component name map) and format `kwargs["link"]` using the target component's hydrated `<base_inst>-<parent_name>-<target_name>-<inc>` nomenclature.

##### Bug B022: `SwitchHitbox` Disables `Plate` Sensor Collisions Once Activated

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `app/assets/hitboxes/objects.py` (and `Ontology Docs: Assets`), `SwitchHitbox.get()` returns `[]` whenever `state.switch` is `True`. While this is intended for `Gates` (which become passable when open), assigning `SwitchHitbox` to `Plates` (`mass = -1` sensors) causes a `Plate` to lose all hitboxes the moment `state.switch` becomes `True`, preventing it from ever detecting subsequent collisions to toggle back off.

**Steps to Replicate**

1. Deploy a `stone-switch` Plate (`mass = -1`) with `SwitchHitbox` and `switch = False`.
2. Intersect the Plate with a Sprite so `plate.state.switch` flips to `True` (or deploy it with `switch = True`).
3. Call `plate.hitboxes` (`SwitchHitbox.get()`) and observe that it returns `[]`, permanently disabling collision detection for the sensor.

**Proposed Remeditation**

Assign `StaticHitbox` (instead of `SwitchHitbox`) to `objects.plates` in `src/data/config/recipes/main.yaml` so sensor plates retain their detection footprint in both switch states while `mass: -1` bypasses physical collision resolution.