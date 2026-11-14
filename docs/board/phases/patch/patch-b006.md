##### Bug B006: Raycast Boundary Grazing

**STATUS**: OPEN
**SEVERITY**: CLOSED

**Description**

The `geometry.los` calculation (and specifically the Liang-Barsky `bisects` implementation) contains a fatal edge-case. If a Sprite grazes or touches the physical boundary of an obstacle (like the map perimeter), `bisects` will permanently evaluate to `True` (Intersection) for *every* raycast, regardless of direction.

If a Sprite touches the `y=1` top perimeter, the ray's origin \(y_1\) equals the boundary. In `bisects`, \(q_3 = y_{max} - y_1 = 1 - 1 = 0\). This results in \(r = 0\). The algorithm updates \(u_1\) or \(u_2\) to $0$, satisfying the \(u_1 \le u_2\) intersection condition at \(t=0\). The Sprite is now permanently "blind" because the raycast origin is technically intersecting the obstacle. This triggers the RRT planner, which immediately fails for the exact same reason, returning an empty path, clearing the goal, and triggering an infinite loop of RRT failures.

**Steps to Replicate** 

1. Place a Sprite exactly adjacent to an obstacle or map perimeter.
2. Assign the Sprite a goal moving away from the obstacle.
3. `geometry.los` will return `False` (Blocked) despite the path being completely clear.

**Proposed Remediation**

In `libs/core/math/geometry.pyx`, add an epsilon padding or strict inequality check to ignore intersections at \(t=0\). If \(u_1 = 0\) or \(r = 0\), the ray originates on the boundary and should not be considered an occlusion unless the vector is directed *into* the obstacle.

**Root Cause Analysis**

In `bisects` (`libs/core/math/geometry.pyx`), the Liang-Barsky line clipping algorithm tests clipping parameters along each boundary $k \in \{0, 1, 2, 3\}$:

$$p_k = -\Delta P \cdot \hat{n}_k, \quad q_k = (P_1 - B_k) \cdot \hat{n}_k, \quad r = \frac{q_k}{p_k}$$

When $p_k > 0$, the vector is directed from the interior toward the exterior across boundary $k$ (an exit transition). When a Sprite grazes a boundary edge (e.g., $y_1 = ry + rl$), $q_k = 0$, yielding $r = 0 / p_k = 0.0$.

The original loop evaluated:

```python
elif p[i] > 0:
    if r < u1:
        return False
    elif r < u2:
        u2 = r

```

Because $u_1 = 0.0$, the condition `r < u1` ($0.0 < 0.0$) evaluated to `False`. The exit parameter $u_2$ was updated to $0.0$. At loop termination:

```python
if u1 > u2:
    return False
return True

```

Because $u_1 = 0.0$ and $u_2 = 0.0$, the condition `u1 > u2` ($0.0 > 0.0$) evaluated to `False`, returning `True` (collision detected). Mathematically, for any outward-pointing vector ($p_k > 0$) originating on or outside boundary $k$ ($q_k \le 0$):

$$q_k(t) = q_k - t \cdot p_k < 0 \quad \forall \; t > 0$$

The ray moves strictly into the exterior of half-space $k$ for all $t > 0$. The ray segment $(0, 1]$ has an empty intersection with the bounding box. Treating $[0.0, 0.0]$ as an occlusion blinds the entity. Furthermore, rays running parallel and coincident to boundary edges ($p_k = 0, q_k = 0$) were permitted through without early exit.

**Implementation**

In `src/libs/core/math/geometry.pyx`, introduce an epsilon tolerance ($\epsilon = 10^{-5}$) to ignore degenerate intersections at $t=0$, prune parallel edge-grazing rays, and reject single-point tangent contacts:

```python
cpdef bint bisects(
    float x1, 
    float y1, 
    float x2, 
    float y2, 
    float rx, 
    float ry, 
    float rw, 
    float rl
):
    """
    Liang-Barsky line clipping algorithm to check if a segment intersects an AABB.
    Returns True if the line segment intersects the rectangle interior, False otherwise.
    """
    cdef float dx = x2 - x1
    cdef float dy = y2 - y1
    cdef float p[4]
    cdef float q[4]
    cdef float EPS = 1e-5
    
    p[0] = -dx
    q[0] = x1 - rx
    p[1] = dx
    q[1] = (rx + rw) - x1
    p[2] = -dy
    q[2] = y1 - ry
    p[3] = dy
    q[3] = (ry + rl) - y1

    cdef float u1 = 0.0
    cdef float u2 = 1.0
    cdef int i
    cdef float r

    for i in range(4):
        if p[i] == 0:
            # Line is parallel to clipping edge: ignore if on or outside boundary
            if q[i] <= EPS:
                return False
        else:
            r = q[i] / p[i]
            if p[i] < 0:
                # Directed into half-space (entry)
                if r > u2:
                    return False
                elif r > u1:
                    u1 = r
            elif p[i] > 0:
                # Directed out of half-space (exit)
                # If exit occurs at or before ray origin, vector is directed away
                if r <= u1 + EPS:
                    return False
                elif r < u2:
                    u2 = r

    # Require non-degenerate penetration depth to count as occlusion
    if u1 >= u2 - EPS:
        return False
        
    return True
```