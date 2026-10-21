**Guidelines: Coverage**

$$
\text{Ideal Test} = \text{Fixture} \to \text{Setup} \to \text{Assertion}
$$

- Ensure all new tests are marked with a `@pytest.mark.<workflow>` annotation.
- Add any new fixtures to the appropriate fixture module.
- Treat `tests.unit.fixtures` as a test bed for constructing application objects. Fixtures should not be created in an adhoc manner; instead, fixtures should exemplify and construct the application dependency tree prior to the execution of tests.  
- If a test requires a specific edge case, request the fixture and mutate its attributes explicitly in the test setup.
- The only actions that should be mocked are file-level access and image rendering.