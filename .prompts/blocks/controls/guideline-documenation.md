**Guideline: Documentation**

* `@TODO(phase: Optional[str])`: Markup by the **User** to denote key areas that need re-evaluated. If present, review the note and consider using a [Backlog Template `with(not grooming)`](#template-backlog) to open an item in the Backlog, or a [Bug Report](#template-bug-report) to isolate a logical error.
    * `phase`: If `phase` has not been started on the [Task Board](#ontology-task-board), ignore this markup. If `phase = None`, review the note unconditionally.