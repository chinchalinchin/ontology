#### Refactor: Phase 10.02 - Shoreline Reindexing

**Overview**

- Integrate Shorelines with Seasonality by adding a compound field to the secondary key relation ShorelineIndex, so the Shoreline frame being rendered is a function of the three-tuple `(tile, fluid, season)`. 
- Shoreline Frames will still have Cardinal rows, but they will now have Season columns, i.e. a Shoreline is identified as a cell in a sheet by (Direction, Season)
- General Phase-related optimzations.

##### Architectural Analysis I

###### Optimizations

1. Inner-Loop Heap Allocation in `SeasonMechanics._probes`

In `src/app/game/logic/mechanics/world/seasons.py`:

```python
@staticmethod
def _probes(resource: Asset) -> List[Position]:
    ...
    return [
        Position(mid_x, mid_y),
        Position(mid_x, pos.y - 1),
        Position(mid_x, pos.y + l),
        Position(pos.x - 1, mid_y),
        Position(pos.x + w, mid_y)
    ]

```

`SeasonMechanics.update()` executes at $60\text{ Hz}$. For every active `Resource` on the board, `_probes()` instantiates five heap-allocated Python `Position` objects each tick to query `board.fluid()`. For dense environments (such as an orchard or forest with 100+ trees), this generates $\sim 30{,}000$ transient Python allocations per second, violating the engine's driving principle of zero heap allocation in inner loops.

2. High-Frequency Evaluation of Declarative ISL Stage Transitions

In `SeasonMechanics.update()`:

```python
executor = self.executors.get(resource.properties.lifespan)
...
next_stage = executor.evaluate(resource.state.stage, locals)

```

Biological stage transitions are evaluated every frame ($16.6\text{ ms}$) across all resources. While moisture diffusion must integrate continuously with frame delta time ($\Delta t$), biological growth checks (which depend on macro seasons and discrete moisture thresholds) do not require $60\text{ Hz}$ AST/lambda evaluation. Throttling stage evaluation to period boundaries or a dedicated low-frequency accumulator (e.g., $1\text{ Hz}$) would eliminate unnecessary CPU overhead.

3. Texture Overdraw in `Screen.reconstruct()`

In `Screen.reconstruct()`:

```python
def reconstruct(self, tiles: List[Asset], calendar: CalendarState) -> None:
    back_tiles, fore_tiles = self._prerender(tiles, calendar)
    render.construct(self.bg_canvas, back_tiles)
    render.construct(self.fg_canvas, fore_tiles)

```

`render.construct()` executes `SDL_RenderCopy` calls directly onto the existing target texture. While opaque `back_tiles` overwrite underlying pixels cleanly, transparent foreground canopy tiles (`fg_canvas`) will overdraw new seasonal pixels directly on top of previous season textures without an intermediate clear pass.

##### Bug Reports

###### Bug B018: Transient Heap Allocation in SeasonMechanics._probes() Inner Loop

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

In `SeasonMechanics._probes(resource)`, five discrete `Position` dataclass instances are constructed every frame for every resource asset on the board. In dense maps, this creates tens of thousands of short-lived Python objects per second, contributing to garbage collection latency.

**Proposed Remediation**

Refactor `Board.fluid()` to accept raw coordinate integers (`board.fluid_at(layer, x, y)`), or pre-calculate and cache the probe offset tuples $(x, y)$ on `ResourceState` during hydration.

##### Goals 

###### Goal: Shoreline Seasonal Indexing (Phase 10.02)

Procedural shorelines currently bind strictly to `(tile_id, fluid_id)` without temporal awareness. When seasonal tiles transition from green turf to winter snowpack, shoreline borders remain rendered in their spring/summer green fringe. Shoreline asset keys must integrate the active calendar season into `CardinalFrame` indexing.

###### Goal: Low-Frequency Stage Transition Throttling

Decouple `SeasonMechanics` stage transition checks from the $60\text{ Hz}$ frame loop. Hydrological moisture diffusion will continue to integrate per tick via $\Delta t$, while AST/lambda rule evaluations via `executor.evaluate()` run conditionally only when a macro-temporal period advances or when accumulated moisture crosses defined discrete thresholds.

##### Tasks

**1. Task: Shoreline Seasonal Keying**

*Objective*: Synchronize procedural shoreline textures with temporal substrate seasons.

* [ ] Subtask: Update `GeographyProperties` to support multi-season shoreline atlas definitions.
* [ ] Subtask: Update `CardinalFrame.eras(id, calendar)` to append `calendar.season` to generated frame keys (`{id}-{season}-{direction}`).
* [ ] Subtask: Update `Screen.reconstruct()` to invalidate and reconstruct shoreline geometry alongside background tiles.

**2. Task: SeasonMechanics Execution Throttling**

*Objective*: Remove high-frequency ISL AST evaluation from the $60\text{ Hz}$ loop.

* [ ] Subtask: Add `_transition_tick: float` accumulator to `SeasonMechanics`.
* [ ] Subtask: Restrict `executor.evaluate()` invocations to run only once per second or when `period_changed == True`.
* [ ] Subtask: Optimize `_probes()` to use integer primitives rather than transient `Position` models.