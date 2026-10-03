
#### Backlog: Transverse Fluids

**Overview**

Resolve the 2.5D elevation collapse where entities immersed in fluid fields are erroneously intercepted by bridge decks. When an asset's trajectory or environmental velocity vector aligns with a water corridor passing underneath a bridge, the entity should clear underneath the bridge deck, render below the bridge structure, and maintain fluid momentum.

##### Goal: Ingress Elevation State & Trajectory Discrimination

Introduce an operational check in `fields.py` that distinguishes between entities stepping onto a bridge deck from adjacent dry terrain versus entities flowing under the bridge deck from an upstream fluid channel.

```python
# Conceptual discrimination in fields.py
is_submerged = getattr(asset.state.mutators.triggers, "submerged", False)
bridge_orientation = bridge.state.orientation

# If already submerged and moving along the fluid vector transverse to the bridge span,
# the entity passes beneath the bridge deck:
if is_submerged:
    # Bridge runs horizontal (East-West) across a vertical (North-South) stream:
    if bridge_orientation == Orientations.HORIZONTAL.value and abs(asset.state.velocity.vy) > 0:
        continue  # Bypass bridge surface interception; pass underneath
    # Bridge runs vertical (North-South) across a horizontal (East-West) stream:
    elif bridge_orientation == Orientations.VERTICAL.value and abs(asset.state.velocity.vx) > 0:
        continue  # Bypass bridge surface interception; pass underneath

```

##### Goal: Underpass Z-Ordering & Visual Occlusion

When an entity passes beneath a bridge deck, dynamically clamp its effective depth below the bridge deck (`bridge.state.depth = 1`) so that the deck renders over the submerged entity while maintaining the entity's position in the fluid current.

##### Tasks

**1. Task: Bridge Deck Ingress Resolution**

*Objective*: Prevent `fields.py` from intercepting submerged dynamic entities whose velocity vectors carry them through the waterway beneath a transverse bridge deck.

* [ ] Subtask: Define transverse alignment predicates in `src/app/game/logic/modules/motion/fields.py` comparing `bridge.state.orientation` with stream `source` direction.
* [ ] Subtask: If `asset.state.mutators.triggers.submerged` is `True` upon entering bridge bounds and flow is transverse to the span, bypass surface interception and maintain immersion velocity.
* [ ] Subtask: Write unit test validating a floating crate passing under a perpendicular bridge deck without clearing its `submerged` state or losing velocity.

**2. Task: Visual Sorting for Bridge Underpass Entities**

*Objective*: Ensure assets passing beneath bridges are drawn below the bridge deck according to the Painter's Algorithm.

* [ ] Subtask: In `Screen.draw()`, if an entity is submerged and intersecting a bridge underpass, ensure its sorting key sorts below the bridge deck (`depth: 1`, `height: 0`).
* [ ] Subtask: Write unit test asserting that a submerged sprite under a bridge deck has a lower draw priority tuple than the bridge segment.