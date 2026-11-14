**Guideline: Testbed**

* Address: `/src/data/state/world-testbed`

Unit tests utilize a dedicated testbed State fixture stored in the Application Data Directory alongside the actual State files.

When the tests bootstrap, the Loader is patched to point to the testbed State fixture. The Application Properties and Configuration are loaded from the same locations they are pulled from during the normal course of the Application. In other words, unit tests utilize a mock State, but they hydrate that State with the actual Properties and Configuration loaded by the Application. 

* **Spatial Tests** When conducting SpatialMechanic or MotionMechanic tests, **isolate** all test variables. Setup the tests *well* outside the locations of the Objects, Fluids, Crafts, etc. deployed in the Testbed State. This will ensure the test occurs in a location free of interactions with other Assets.
