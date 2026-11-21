**Guidelines: Coverage**

$$
\text{Ideal Test} \equiv \text{Fixture} \to \text{Setup} \to \text{Assertion}
$$

* Ensure all new tests are marked with a `@pytest.mark.<marker>` annotation.
* Add any new fixtures to the appropriate fixture module.
* Treat `tests.unit.fixtures` as a test bed for constructing [Application](#application) objects. Fixtures should not be created in an adhoc manner; instead, fixtures should exemplify and construct the application dependency tree prior to the execution of tests.  
* If a test requires a specific edge case, request the fixture and mutate its attributes explicitly in the test setup.
* **Spatial Tests** When conducting SpatialMechanic or MotionMechanic tests, **isolate** all test variables. Setup the tests *well* outside the locations of the Objects, Fluids, Crafts, etc. deployed in the Testbed State. This will ensure the test occurs in a location free of interactions with other Assets and remove the possibility of failures due to extraneous factors.
* **Invariance** When making assertions, do not use arbitary values. Parameterize the assertion by finding the **invariant** quantity of the test. If the Testbed State File or Asset Properties are altered, this should **not** affect the success of the assertion, i.e. all tests should be decoupled from the specific values of Properties and State. The hardcoded quantities in the test assertions should represent constants that do **not** change when the State is changed.

**Example: Variant Test**

```python
def test_kinematic_movement_orthogonal(
    mock_board,
    mock_payload,
):
    mock_player = mock_board.player()
    payload = mock_payload(goals=[PlayerGoals.UP.value])

    kinematic.update([mock_player], payload, 1.0)

    assert mock_player.state.velocity.vx == 0.0
    assert mock_player.state.velocity.vy == -20
```

**Example: Invariant Test**

```python
def test_kinematic_movement_orthogonal(
    mock_board,
    mock_payload,
):
    mock_player = mock_board.player()
    speed = float(mock_player.state.character.speed)
    payload = mock_payload(goals=[PlayerGoals.UP.value])

    kinematic.update([mock_player], payload, 1.0)

    assert mock_player.state.velocity.vx == 0.0
    assert mock_player.state.velocity.vy == -speed
```