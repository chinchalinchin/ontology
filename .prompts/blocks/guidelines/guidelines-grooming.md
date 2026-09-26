# Task: Ontology - Groom

**Priority**

Discuss the design and architecture of this application with respect to the current phase of the [Task Board](#view-ontology-task-board). Do not implement anything; instead step back and examine the big picture. Focus on the logical flow of the application. Suggest improvements, if applicable. Discuss what needs modified in the task backlog, if changes are required. Ensure tasking aligns with architecture. Break everything down, step-by-step.

Treat code as ground truth, but recognize the application is in development and this ground truth will evolve over time. Documentation is an ideal that may not yet be implemented in the code (or it may have been modified to accomodate the realities of code execution); it serves as a design document. It should be respected and consulted for the general direction of the project, but not always enforced. Because the application is currently in development, the documentation may touch on areas that have not yet been implemented. Documentation is in flux while design occurs, so it is open for debate, if something is inconsistent or contradictory. Assist in elaborating the nebulous or vague concepts in the documentation.

**Grooming Guidelines**

- Create or modify tasks on the [Task Board](#view-ontology-task-board) to achieve the next Phase of the application. Lay out, step-by-step, what must be done. Follow the [Backlog Template](#template-backlog).
- (*Optional*) Suggest updates to the [Documentation](#view-ontology-documentation) to solidify the architecture and design of the application. Use the [Documentation Template](#template-documentation) to propose changes.
- (*Optional*) Be on the lookout for bugs. Use the [Bug Report Template](#template-bug-report) to raise any issues you find.

**Application Constraints**

Changes that violate these constraints will be rejected.

- Code should never alter Asset Properties. Asset Properties are static and never change.
- The only code that should alter a Sprite's Intention is TransitionMechanics. 
- The only code that should alter a Sprite's Goal is CognitionMechanics. 

**Other Notes**

- Keep in mind, this is a 2D game engine that is cropping pre-rendered assets on the fly, not rendering fully-textured ray-traced 3D graphics from scratch. 
- Do not suggest C-level optimizations at this stage of the application.
- Do not worry about Python GIL locks yet, unless concerns are severe.
- Do not raise issues for tasks already added in the backlog if you have nothing add. There is no reason to reiterate what has already been groomed.
- Let the data model validators do their job. All data must pass through strict Pydantic TydeAdaptor validation before it is loaded into the game. Do not worry about excessively checking the existence of attributes on objects to prevent RuntimeErrors. The models are there for a reason.
- If a solution requires duck-typing, it is a probably a bad solution.
