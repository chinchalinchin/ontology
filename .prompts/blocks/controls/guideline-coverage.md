**Guidelines: Coverage**

$$
\text{Ideal Test} = \text{Fixture} \to \text{Setup} \to \text{Assertion}
$$

* Ensure all new tests are marked with a `@pytest.mark.<workflow>` annotation.
* Add any new fixtures to the appropriate fixture module.
* Treat `tests.unit.fixtures` as a test bed for constructing application objects. Fixtures should not be created in an adhoc manner; instead, fixtures should exemplify and construct the application dependency tree prior to the execution of tests.  
* If a test requires a specific edge case, request the fixture and mutate its attributes explicitly in the test setup.

**Guideline: Testbed**

* Address: `/src/data/state/world-testbed`

Unit tests utilize a dedicated testbed State fixture stored in the Application Data Directory alongside the actual State files.

When the tests bootstrap, the Loader is patched to point to the testbed State fixture. The Application Properties and Configuration are loaded from the same locations they are pulled from during the normal course of the Application. In other words, unit tests utilize a mock State, but they hydrate that State with actual Properties and Configuration loaded by the Application. 