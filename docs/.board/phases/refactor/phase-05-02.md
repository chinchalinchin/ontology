#### Refactor: Phase 05.02 - Simplification

**Overview** 

With the introduction of Widgets and Mechanics, the application architecture needs to be re-evaluated to see if any simplification can be introduced.

!!! "definition"
    Simplification = Simple, readable patterns

**Service Dependency Injection**

It has become clear the Orchestrator is acting as the dependency injection system. It passes many different services down to the core game components, e.g. Cradle and Device get injected into the Board, Provider and Mechanics get injected into the Engine, etc. 

Analyze the application and determine if an annotation-based registration would be better for these services.

**Boilerplate Reduction**

While considering annotations, consider if annotations should be added to Factory objects rather than hardcoding them (via Enums) into the Factory maps.

**Package Organization**

The Package structure was "grown organically" as the application developed up to this point. Examine the package structure and determine if it is optimally organized. If there is a better logical grouping, suggest one.

##### Tasks

1. **Task: Centralize Input Polling (High Priority)**

*Objective*: Prevent `_last_state` mutation bugs during the game loop.

- [ ] Remove `board.device.poll()` from all individual `Mechanic` implementations. 
- [ ] Update `Engine._play()` to call `poll()` once per tick and pass the `DevicePayload` alongside the `bus` to the Mechanics interface.

2. **Task: Implement Annotation-Based Registration**

*Objective*: Decouple class bindings from the Factory to reduce boilerplate.

- [] Create a `@register(Enum)` decorator in the `Factory`. 
- [] Refactor `Mechanic`, `Animation`, `Frame`, and `Controller` classes to self-register on module initialization. 
- [] Remove all hardcoded mapping dictionaries from `app.services.factory`.