**Guideline: Fixtures**

If a test requires a specific Asset, apply the following criteria for determining how to pull the fixture:

* If the tag is `app.asset` (`app_asset`), use the `mock_asset()` fixture to isolate the desired Asset object.
* If the tag is `app.component` (`app_component`), use the `mock_board` and query the Board interfaces.
* If the tag is `app.mechanics` (`app_mechanic`), use the `mock_mechanic()` fixture to isolate the desired Mechanic object.

If you encounter a situation not described by these conditions or an edge case, the motivating principle should always be: *let the application do its job*.

