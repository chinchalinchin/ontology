# Task: Ontology - Review

*Unit Tests*: Passing
*User Acceptance Tests*: Passing

The current Phase has been completed. All tests are passing. Now is the time to consolidate, review code for bugs or misalignments and ideate goals for the future. 

Discuss the design and architecture of this application with respect to the preceding and future phases. Do not implement anything; instead step back and examine the big picture. Focus on the overarching philosophy and goal of the application.

What needs modified in the phase roadmap? What is the next logical step in the implementation of a simulation engine? 

**Priorities**

- Ensure the implementation meets the specifications.
- Use the [Documentation Template](#template-documentaton) to isolate any divergences in the documentation and codebase.
- (*Optional*) Use [Backlog Template](#template-backlog) to open backlog items.
- (*Optional*) Use the [Bug Report Template](#template-bug-report) to raise any issues you find.

**Guidelines**

- All enums are `class Test(str, Enum)`. Do not raise issues related to enum str comparisons. 
- Let the data model validators do their job. Everything in the `/src/data/**` must passes through strict Pydantic TydeAdaptor validation before it is loaded into the game. Do not worry about excessively checking the existence of attributes on objects to prevent RuntimeErrors. The models are there for a reason. 