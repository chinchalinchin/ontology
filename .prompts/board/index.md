This is the Task Board for the project. Below is a backlog of completed and pending Tasks. Tasks are divided into Phases. Phases are not necessarily sequential.

!!! "Task Progress Key"
  `[ ]`: Open
  `[~]`: In Progress
  `[?]`: Needs Further Analysis
  `[x]`: Closed/Implemented
  `[!]`: DO NOT COMPLETE

!!! "Phase Actions"
  - Implement: Complex, multi-task development of new functionality.
  - Refactor: Refactoring tasks for existing functionality.
  - Patch: Tasks for fixing logical bugs and address issues.
  - Achieve: Short, encapsulated tasks.

**Table of Contents**

- Actions:
  - Implement:
    - [x]: [Phase 01: Renderer](./phases/implement/phase-01.md)
    - [x]: [Phase 02: Player](./phases/implement/phase-02.md)
    - [x]: [Phase 03: Physics](./phases/implement/phase-03.md)
    - [x]: [Phase 04: Widgets](./phases/implement/phase-04.md)
    - [~]: [Phase 05: Editor](./phases/implement/phase-05.md)
    - [x]: [Phase 06: Intentions](./phases/implement/phase-06.md)
    - [x]: [Phase 07: Compositions](./phases/implement/phase-07.md)
    - [x]: [Phase 08: Pathfinding](./phases/implement/phase-08.md)
    - [ ]: [Phase 09: Commerce](./phases/implement/phase-09.md)
    - [ ]: [Phase 10: Towns](./phases/implement/phase-10.md)
  - Refactor:
    - Phase 01:
      - [x]: [Phase 01.01: Orchestration](./phases/refactor/refactor-01-01.md)
    - Phase 02:
      - [x]: [Phase 02.01: Frames](./phases/refactor/refactor-02-01.md)
      - [x]: [Phase 02.02: Registry](./phases/refactor/refactor-02-02.md)
      - [x]: [Phase 02.03: Equipment](./phases/refactor/refactor-02-03.md)
      - [x]: [Phase 02.04: Engine](./phases/refactor/refactor-02-04.md)
      - [x]: [Phase 02.05: Finetuning](./phases/refactor/refactor-02-05.md)
    - Phase 03:
      - [x]: [Phase 03.01: Mechanics](./phases/refactor/refactor-03-01.md)
      - [x]: [Phase 03.02: Consolidation](./phases/refactor/refactor-03-02.md)
      - [x]: [Phase 03.03: Motion](./phases/refactor/refactor-03-03.md)
    - Phase 05:
      - [x]: [Phase 04.01: Typography](./phases/refactor/refactor-04-01.md)
      - [x]: [Phase 04.02: Simplification](./phases/refactor/refactor-04-02.md)
      - [x]: [Phase 04.03: EventHandlers](./phases/refactor/refactor-04-03.md)
      - [x]: [Phase 04.04: MenuContext](./phases/refactor/refactor-04-04.md)
    - Phase 06:
      - [x]: [Phase 06.01: Expressions](./phases/refactor/refactor-06-01.md)
    - Phase 08:
      - [~]: [Phase 08.01: Obstable Geometry](./phases/refactor/refactor-08-01.md)
  - Patch:
    - [x]: [Bug B000: Attacking Glitch](./phases/patch/bug-b000.md)
    - [ ]: [Bug B001: Relayering Instantied Assets](./phases/patch/bug-b001.md)
    - [ ]: [Bug B002: Board Cache Wipe](./phases/patch/bug-b002.md)
    - [ ]: [Bug B003: Painter's Algorithm String Exception](./phases/patch/bug-b003.md)
    - [x]: [Bug B004: Friction Regression](./phases/patch/bug-b004.md)
    - [x]: [Bug B005: Speak Regression](./phases/patch/bug-b005.md)
    - [x]: [Bug B006: Raycast Boundary Grazing](./phases/patch/bug-b006.md)
  - Achieve:
    - [x]: [Goal 01: Boundaries](./phases/achieve/goal-01.md)
    - [x]: [Goal 02: ScrollController, Library & Plots](./phases/achieve/goal-02)
    - [~]: [Goal 03: ExchangeController & Loot](./phases/achieve/goal-03.md)
    - [x]: [Goal 04: Main Menu & Saving](./phases/achieve/goal-04.md)
    - [ ]: [Goal 05: InventoryController](./phases/achieve/goal-05.md)
    - [x]: [Goal 06: Speak Intentions](./phases/achieve/goal-06.md)
    - [x]: [Goal 07: Door Interact Intentions](./phases/achieve/goal-07.md)
- Backlog:
  - [Telemetry Menu](./backlog/todo-t000.md)

#### Bug Report Template

For ancillary or tangential bugs detected, use the following template to open new Bugs,

```markdown
{% for bug in bugs %}
##### Bug {{ bug.id }}: {{ bug.title }}

**STATUS**: OPEN
**SEVERITY**: {{ bug.severity }}

**Description**

{{ bug.description }}

{% if is_reproducible(bug) %}
**Steps to Replicate** 

{{ bug.steps }}
{% endif %}

**Proposed Remeditation**

{{ remediation }}

{% endfor %}
```

#### Phase Template

To add new Tasks to the backlog, use the following template,

```markdown
#### Backlog: {{ title }}

**Overview** 

{{ overview }}

{% for goal in goals %}
##### Goal: {{ goal.title }}

{{ goal.description | architectural_discussion or pseduo_code }}

{% endfor %}

{% for task in tasks %}
##### Tasks

**{{ loop.index }}. Task: {{ task.title }}**

*Objective*: {{ task.objective }}

{% for subtask in task $}
- [] Subtask: {{ subtask.description }}
{% endfor %}

{% endfor %}
```