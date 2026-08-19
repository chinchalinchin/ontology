# Ontology: Tests

## /tests/sdl/graphics

Exploratory Cythonized SDL Rendering Test

```bash
cd ontology/tests/sdl/graphics
python setup.py build_ext --inplace
python -c "import test; test.run_test()"
python -c "import test; test.run_test_headless()"
```

## /tests/sdl/sound

```bash
cd ontology/tests/sdl/sound
python setup.py build_ext --inplace
python -c "import test; test.play_audio(b'bite.wav', b'arabesque.mp3')"
```