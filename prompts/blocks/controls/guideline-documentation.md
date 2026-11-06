**Guideline: Documentation**

Treat code as ground truth, but recognize the application is in development and this ground truth will evolve over time. Documentation is an ideal that may not yet be implemented in the code (or it may have been modified to accomodate the realities of code execution); it serves as a design document. It should be respected and consulted for the general direction of the project, but not always enforced. Because the application is currently in development, the documentation may touch on areas that have not yet been implemented or it may assert things of the code that are no longer true. Documentation is in flux while design occurs, so it is open for debate if something is inconsistent or contradictory. Assist in elaborating the nebulous or vague concepts in the documentation.

* Documentation Markup:
    * `@TODO(phase: Optional[str])`: Markup by the **User** to denote key areas that need re-evaluated. If present, review the note and consider using a [Backlog Template `with(not grooming)`](#template-backlog) to open an item in the Backlog, or a [Bug Report](#template-bug-report) to isolate a logical error.
        * `phase`: If `phase` has not been started on the [Task Board](#ontology-task-board), ignore this markup. If `phase = None`, review the note unconditionally.

