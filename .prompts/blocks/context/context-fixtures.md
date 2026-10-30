**Context: Fixtures**

Application fixtures have recently been reorganized and streamlined for reuse, rather than recreating them for every single test. This is an ongoing effort. The goal is to remove all blackbox testing with MagicMocks. All unit tests should be testing live code, with the exception of mocked image rendering.

Massive changes were introduced as a result of Phase 07.04. Many of the unit tests are currently failing. Rather than simply getting the old tests to work in the new Material framework (which now includes HitboxSchema and other fundamental changes, such as elevations and substrates), the entire Fixture framework is being condensed to reduce boilerplate even further. In the current phase, Fixture Factories are being integrated into the test pipeline. 

* Asset may need added to the `world-testbed` to restore the unit tests.