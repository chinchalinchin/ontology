# Task: Ontology - Implement

**Priorities**

- Implement the next task(s) on the [Task Board](#view-ontology-task-board).

**Implementation Guidelines**

- Let the data model validators do their job. All data must pass through strict Pydantic TydeAdaptor validation before it is loaded into the game. Do not worry about excessively checking the existence of attributes on objects to prevent RuntimeErrors. The models are there for a reason. 
- If a solution requires duck-typing, it is a probably a bad solution.
- Do **NOT** go outside the specifications and implement functionality you *think* should be implemented. If you notice something that is not addressed by the current state of the [Task Board](#view-ontology-task-board), open a new [Backlog Task](#template-backlog) or file a [Bug Report](#template-bug-report).
- Keep in mind: while generality and reusability is good, this should not come at the expense of readability. Do not implement a solution unless you think others can understand it.
- Always approach problems from a functional perspective, i.e. break the problem up into the smallest chunks and modularize as much as possible. 