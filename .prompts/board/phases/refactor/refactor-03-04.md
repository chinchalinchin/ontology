#### Refactor: Phase 03.04 - Projectiles

**Overview** 

Projectiles are currently stubbed and their mechanics are largely unimplemented. The goal of this refactor is to implement Projectiles.

**Notes**

- Possible Approaches:
    - Manually construct Projectile frame rows corresponding to Directions.
    - Create a RotationFrame to operate on a single Projectile frame.
- RotationFrame: Assume Projectile always facing to the right in the Asset file. 
    - `if direction == RIGHT: rotate(0 degrees)`
    - `if direction == DOWN: rotate(90 degrees)`
    - `if direction == LEFT: rotate(180 degrees)`
    - `if direction == UP: rotate(270 degrees or -90 degrees)` (whichever is less expensive computationally, if it matters)

**Consideration**: Only matters for line-segment projectiles, like arrows or bolts. Doesn't matter for circular projectiles like cannonballs or magic. May not be worth formalizing this distinction, as the instances of perfect circular projectiles are likely not to be numerous.