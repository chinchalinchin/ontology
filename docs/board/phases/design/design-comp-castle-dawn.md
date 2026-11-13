#### Design: Composition C000 - Castle Dawn

* **Purpose**: Testing Gravity and Elevation in Phase 07.03. Testing implementations of Columns from Phase 07.04.

##### Composition: Specification

The reclusive and otherwordly abode of Evil Empress Jasilynn.

* Layers:
    * `atrium-layer`
    * `stairwell-right-layer`
    * `stairwell-left-layer`
    * `throne-layer`
* Room Circuits:
    * Ground Exterior <-> Atrium
    * Atrium <-> Throne Room
    * Atrium <-> Stairwells
    * Stairwells <-> Roof Exterior
* Features:
    * Roof has crenellation to stop Player from floating over the level until Gravity is implemented.
    * Atrium has a pair of elevated surfaces symmetrically arranged, with Doors on either surface leading to Stairwells (hallways with Stairs) that lead in turn to the Roof.
        * *Note*: Door Shadows should be projected into the Stairwell layers.
    * Throne Access: Door leading to the Throne Room.
        * *Note*: Door Shadow should be projected into the Throne Room layer.
* Aesthetics:
    * Atrium: Imposing and vast, disportionate to the exterior size, i.e. the interior is somehow larger than the exterior, as though the Evil Empress held sway over space itself. 
    * Throne Room: Ominous, the central source of the Evil Empress's nefarious magic.
    * Stairwell: Isolating, as though the Player did not belong.
    * Exterior: Strikes fear into the hearts of the citizens.

##### Composition: Model

```yaml
compositions:
    castle-dawn:
        root:
            strut: TODO
            components: TOODO
        branches: TODO
```

##### Composition: Tasks

* [] **Atrium**: 
    * [] Right Stairwell Access
    * [] Left Stairwell Access
    * [] Throne Access
    * [] Aesthetics and Vanity
* [] **Stairwells**
    * [] Roof Access
    * [] Atrium Access
    * [] Aesthetics and Vanity
* [] **Throne Room**
    * [] Throne Access
    * [] Aesthetics and Vanity
* [] **Archer's Roof**:
    * [] Atrium Access
    * [] Crenellation
    * [] Aesthetics and Vanity
