# Ontology: Tests 

## Tests: Exploratory

**exploratory/sdl/graphics**

```bash
cd ontology/tests/exploratory/sdl/graphics
python setup.py build_ext --inplace
python -c "import test; test.run_test()"
```

**exploratory/sdl/sound/loading**

```bash
cd ontology/tests/exploratory/sdl/sound/loading
python setup.py build_ext --inplace
python -c "import test; test.play_audio(b'bite.wav', b'arabesque.mp3')"
```

**exploratory/sdl/typography**

```bash
cd ontology/tests/exploratory/sdl/typography
python setup.py build_ext --inplace
python -c "import test; test.run_text_viewer()"
```