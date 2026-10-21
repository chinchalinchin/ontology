**Constraint: Coverage**

- Do **not** test code you haven't seen.
- Do **not** create fixtures in the test itself; Tests should request fixtures and use them.
- Do **not** use MagicMocks unless *absolutely* necessary. Unit tests should not be a blackbox probe; they should test live code execution.
- Do **not** test how a Mechanic does its job (e.g., asserting internal method calls) unless it delegates to a Cython module. Test the result on the Board.