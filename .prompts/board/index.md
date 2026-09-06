This is the Task Board for the project. Below is a backlog of completed and pending Tasks. Tasks are divided into Phases. Phases are not necessarily sequential.

!!! "Task Progress Key"
  `[ ]`: Open
  `[~]`: In Progress
  `[?]`: Needs Further Analysis
  `[x]`: Closed/Implemented
  `[!]`: DO NOT COMPLETE

**Table of Contents**

- Phases:
  - Implement:
    - [x]: [Phase 01: Renderer](./phases/implement/phase-01.md)
    - [x]: [Phase 02: Player](./phases/implement/phase-02.md)
    - [x]: [Phase 03: Finetuning](./phases/implement/phase-03.md)
    - [x]: [Phase 04: Physics](./phases/implement/phase-04.md)
    - [x]: [Phase 05: Widgets](./phases/implement/phase-05.md)
    - [~]: [Phase 06: Editor](./phases/implement/phase-06.md)
    - [x]: [Phase 07: Intentions](./phases/implement/phase-07.md)
    - [x]: [Phase 08: Compositions](./phases/implement/phase-08.md)
    - [ ]: [Phase 09: Commerce](./phases/implement/phase-09.md)
    - [ ]: [Phase 10: Towns](./phases/implement/phase-10.md)
  - Refactor:
    - [x]: [Phase 01.01: Orchestration](./phases/refactor/phase-01-01.md)
    - [x]: [Phase 02.01: Frames](./phases/refactor/phase-02-01.md)
    - [x]: [Phase 02.02: Registry Indexing](./phases/refactor/phase-02-02.md)
    - [x]: [Phase 02.03: Equipment Animations](./phases/refactor/phase-02-03.md)
    - [x]: [Phase 02.04: Engine](./phases/refactor/phase-02-04.md)
    - [x]: [Phase 04.01: Mechanics](./phases/refactor/phase-04-01.md)
    - [x]: [Phase 04.02: Consolidation](./phases/refactor/phase-04-02.md)
    - [x]: [Phase 04.03: Motion](./phases/refactor/phase-04-03.md)
    - [x]: [Phase 05.01: Typography](./phases/refactor/phase-05-01.md)
    - [x]: [Phase 05.02: Simplification](./phases/refactor/phase-05-02.md)
    - [x]: [Phase 05.03: ScrollController, Library & Plots](./phases/refactor/phase-05-03.md)
    - [~]: [Phase 05.04: ExchangeController & Loot](./phases/refactor/phase-05-04.md)
    - [x]: [Phase 05.05: Main Menu & Saving](./phases/refactor/phase-05-05.md)
    - [~]: [Phase 05.06: EventHandlers & EventContent](./phases/refactor/phase-05-06.md)
    - [ ]: [Phase 05.07: InventoryController](./phases/refactor/phase-05-07.md)
    - [x]: [Phase 07.01: Speak Intentions](./phases/refactor/phase-07-01.md)
    - [~]: [Phase 07.02: Interact Intentions](./phases/refactor/phase-07-02.md)
  - Patch:
    - [x]: [Bug B000: Attacking Glitch](./phases/patch/bug-b000.md)
    - [ ]: [Bug B001: Relayering Instantied Assets](./phases/patch/bug-b001.md)
    - [ ]: [Bug B002: Board Cache Wipe](./phases/patch/bug-b002.md)
    - [ ]: [Bug B003: Painter's Algorithm String Exception](./phases/patch/bug-b003.md)
    - [x]: [Bug B004: Friction Regression](./phases/patch/bug-b004.md)
  - Report:
    - [x]: [2026-08-16: SDL Pipeline Failure](./phases/report/2026-08-16.md)
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