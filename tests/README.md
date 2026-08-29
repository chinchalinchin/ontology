# Ontology: Tests

## Index

* `exploratory/sdl/graphics`: Exploratory Cythonized SDL rendering test.
* `exploratory/sdl/sound`: Exploratory Cythonized SDL mixing test.

### Exploratory

**exploratory/sdl/graphics**

```bash
cd ontology/tests/exploratory/sdl/graphics
python setup.py build_ext --inplace
python -c "import test; test.run_test()"
```

**exploratory/sdl/sound**

```bash
cd ontology/tests/exploratory/sdl/sound
python setup.py build_ext --inplace
python -c "import test; test.play_audio(b'bite.wav', b'arabesque.mp3')"
```

**exploratory/sdl/typography**

```bash
cd ontology/tests/exploratory/sdl/sound
python setup.py build_ext --inplace
python -c "import test; test.run_text_viewer()"
```

### Unit

TODO