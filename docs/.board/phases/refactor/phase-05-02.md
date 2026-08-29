#### Refactor: Phase 05.02 - Simplification

**Overview** 

With the introduction of Widgets and Mechanics, the application architecture needs to be re-evaluated to see if any simplification can be introduced.

!!! "definition"
    Simplification = Simple, readable patterns

**Service Dependency Injection**

It has been clear the Orchestrator is acting as the dependency injection system. It passes many different services down to the core game components, e.g. Cradle and Device get injected into the Board, Provider and Mechanics get injected into the Engine, etc. 

Analyze the application and determine if an annotation-based registration would be better for these services.

**Boilerplate Reduction**

While considering annotations, consider if annotations should be added to Factory objects rather than hardcoding them (via Enums) into the Factory maps.

**Package Organization**

The Package structure was "grown organically" as the application developed up to this point. Examine the package structure and determine if it is optimally organized. If there is a better logical grouping, suggest one.

##### Tasks

**1. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO

**2. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO