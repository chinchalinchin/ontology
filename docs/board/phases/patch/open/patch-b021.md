##### Bug 021: Sub-Pixel Integer Truncation in `physics.collide` Fails to Separate 1px Dynamic Overlaps

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/libs/core/math/physics.pyx` (`collide()`), inverse-mass proportional displacements `shift_x1 = overlap_x * p1` and `shift_x2 = overlap_x * p2` are truncated to integers via `int(shift_x1)` and `int(shift_x2)` before being applied to `pos1` and `pos2`. Whenever two dynamic bodies ($m_1 > 0, m_2 > 0 \implies p_1 \in (0, 1), p_2 \in (0, 1)$) overlap by `1.0` pixel (or `2.0` pixels with unequal masses such as $m_1 = 10, m_2 = 5$ where $2 \times \frac{1}{3} = 0.66$), `int(shift)` truncates to `0` for one or both bodies, leaving the hitboxes overlapping after resolution while still applying elastic velocity transfer.

**Steps to Replicate**

1. Instantiate two `crates` ($m_1 = 1, m_2 = 1$) with `32x32` hitboxes at `pos1 = Position(0, 0)` and `pos2 = Position(31, 0)` (`overlap_x = 1.0`).
2. Call `physics.collide(pos1, hb, Velocity(10.0, 0.0), 1.0, False, pos2, hb, Velocity(-10.0, 0.0), 1.0, False)`.
3. Observe `pos1.x == 0` and `pos2.x == 31` (zero spatial separation).

**Proposed Remeditation**

Use ceiling/rounding on the lighter body's shift or assign the integer remainder `int(overlap_x) - int(shift_x1)` to `shift_x2` so the total applied integer displacement always equals `int(overlap_x)` (and similarly for `overlap_y`).
