**Constraint: Coverage**

* Do **not** test code you haven't seen.
* Do **not** create fixtures in the test itself; Tests should request fixtures and use them.
* Do **not** use MagicMocks unless *absolutely* necessary. Unit tests should not be a blackbox probe; they should test live code execution. 
    * The only actions that should be mocked are filesystem access and image rendering.
* Do **not** test how a Mechanic does its job (e.g., asserting internal method calls) unless it delegates to a Cython module. Test the result on the Board.
* Let the Application do its job. Do **not** validate fixtures or perform typing checking in the unit test setup. This defeats the purpose of a unit test; the Application should be performing all logic and validation. A unit test should be isolated to setting up test conditions and making assertions of results.


