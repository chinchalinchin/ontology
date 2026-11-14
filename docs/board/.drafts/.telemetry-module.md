#### Backlog: TODO T000 - Telemetry Module

**Overview**

The current debugging architecture relies on static post-mortem state dumps written during process teardown. This prevents developers from inspecting transient state transformations during active execution, such as Symplectic Euler velocity integration, RRT trajectory convergence, dynamic hydrological moisture diffusion, and Intention Finite Automata state transitions.

This proposal defines `app.telemetry`: an asynchronous, non-blocking telemetry and state introspection daemon embedded into the game engine lifecycle. It provides an interface to query the `Board` database in real time during live 60 Hz simulation without disrupting frame pacing or violating the zero-heap allocation design principles of the inner loop.

##### Specification

`app.telemetry` operates via a lightweight IPC/socket probe and a dedicated `CoreMechanic` pipeline:

1. **Architecture & Threading Model**:

* `TelemetryServer`: Operates on an independent daemon thread, serving queries via an IPC domain socket (`/tmp/ontology-telemetry.sock`) or loopback TCP (`127.0.0.1:9229`).
* `TelemetryMechanic` (`app.mechanics.core.telemetry`): Registered in `Engine.core`. Executes on every engine tick at the boundary between physics integration and Screen rasterization. It consumes inbound probe requests, executes deterministic queries against the `Board`, and dispatches structured serialization payloads across a thread-safe lock-free buffer (`queue.SimpleQueue`).
* Concurrency Safety: Python GIL locking during frame mutation is avoided by constraining Board queries strictly to the synchronous execution of `TelemetryMechanic.update()`. The background thread handles network I/O and payload serialization exclusively.

2. **Query Grammar**:

* `GET /assets?category=<regex>&instance=<regex>&id=<regex>&name=<regex>&layer=<str>&elevation=<int>`
* `GET /metrics`: Fixed-tick delta, FPS, entity count per bucket, spatial grid occupancy, and active RRT node allocations.
* `GET /hydrology?layer=<str>&x=<int>&y=<int>`: Live evaluation of `board.moisture(layer, x, y)` and `board.fluid(layer, Position(x, y))`.
* `GET /character/<name>`: Focused telemetry stream of NPC Psyche, Goal, Trajectory, and Intention vectors.

3. **Output Transports**:

* Compact binary/JSON payloads for high-frequency consumption.
* Streaming CLI subcommands (`python main.py telemetry --stream --instances sprites`).

##### Architectural Analysis I

1. **State Isolation & GIL Contention**:

Querying the `Board` directly from an external socket thread introduces race conditions against Cython pointer dereferencing and state mutations in `physics.pyx`. Executing queries through a `CoreMechanic` guarantees tick-boundary serialization where asset positions, velocities, and bounding boxes are static.

2. **Allocation Overhead**:

Continuous polling must not cause GC frame stutter. The telemetry pipeline utilizes pre-allocated primitive dictionaries and Cython-to-primitive conversions (`Asset.primitive()`) for spatial queries, delegating JSON serialization to the background worker thread.

3. **Live Engine Debugging**:

Enables attaching headless observer terminals or curses monitors to a running engine session, recording anomalous NPC oscillations, tracking RRT path generation retries (`trajectory.stalled`), and validating moisture fields on demand.

##### Goals

###### Goal: Non-Blocking Tick Boundary Querying

Implement `TelemetryMechanic` within `app.mechanics.core` to process queued query commands synchronously at tick completion:

```python
class TelemetryMechanic(Mechanic):
    def update(self, board: Board, delta: float, bus: Bus) -> None:
        while not self.inbound_queue.empty():
            query = self.inbound_queue.get_nowait()
            result = self.evaluate_query(board, query)
            self.outbound_queue.put_nowait(result)

```

###### Goal: Daemon IPC Server

Construct `TelemetryServer` in `app.telemetry.server` managing socket connections and serializing query responses asynchronously.

###### Goal: Live CLI Client Integration

Expose a new `telemetry` subcommand in `main.py` allowing developers to inspect a live engine process:

```bash
python main.py telemetry --instances sprites --names npc_merchant

```

##### Tasks

**1. Task: Protocol Definition and Data Models**

*Objective*: Design internal request/response schemas for live engine queries in `app.telemetry.models`.

* [ ] Subtask: Define `TelemetryRequest` and `TelemetryResponse` dataclasses supporting regex filtering parameters.
* [ ] Subtask: Implement zero-copy primitive serialization wrappers for `Board` state entities.

**2. Task: Telemetry Mechanic Implementation**

*Objective*: Integrate telemetry query resolution into the engine loop via `app.mechanics.core.telemetry`.

* [x] Subtask: Construct `TelemetryMechanic` inheriting from base `Mechanic`.
* [x] Subtask: Integrate `board.instances()`, `board.categories()`, and `predicates` query filters into the execution loop.
* [x] Subtask: Register `TelemetryMechanic` in `MechanicsFactory` under core mechanics pipelines.

**3. Task: IPC Transport Daemon**

*Objective*: Build the asynchronous IPC server in `app.telemetry.server`.

* [~] Subtask: Implement non-blocking domain socket and loopback socket listener.
* [ ] Subtask: Implement queue synchronizer communicating with `TelemetryMechanic`.
* [ ] Subtask: Wire daemon initialization into `Orchestrator.orchestrate()`.

**4. Task: CLI Telemetry Command**

*Objective*: Add client-side inspection tooling in `cli.py`.

* [ ] Subtask: Add `telemetry` subparser with filter arguments mirroring the state dump options.
* [ ] Subtask: Implement continuous terminal streaming and single-shot query output formatters.