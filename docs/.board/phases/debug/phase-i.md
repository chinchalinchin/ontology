#### Debug - Phase I

## SDL Tests

```bash
cd ontology/tests/sdl
python setup.py build_ext --inplace
python -c "import test; test.run_test()"
python -c "import test; test.run_test_headless()"
```

## Command Line Test

* [x] **Verification:** Ensure the `prender` and `render` command line function still works 