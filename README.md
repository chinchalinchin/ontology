# Ontology

[![ontology-tests](https://github.com/chinchalinchin/ontology/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/chinchalinchin/ontology/actions/workflows/tests.yml)

- [Documentation](https://chinchalinchin.github.io/ontology/)

## Setup

Install and build the application dependencies.

### Install

Cython needs the actual C development headers to compile against,

* **macOS:** `brew install sdl2 sdl2_image`
* **Linux (Debian/Ubuntu):** `sudo apt install libsdl2-dev libsdl2-image-dev`

### Build

To compile the C extensions, run the following command in your terminal:

```bash
python setup.py build_ext --inplace
```

### Usage

```bash
# 0. Clean Up Dump Logs
rm *dump.md

# 1. Configure Command Line Arguments
export LOG_LEVEL=INFO
export WORLD=world-01
export LAYER=0
export BUILD_DIR=/home/grant/Projects/ontology/build

# 1. DEBUG: Render Background
python src/cli.py \
  --dump-state \
  --dump-sdl \
  --log-level $LOG_LEVEL \
    prerender $WORLD \
    --layer $LAYER \
    --out $BUILD_DIR

# 2. DEBUG: Render Stateful Assets
python src/cli.py  \
  --dump-state \
  --dump-sdl \
  --log-level $LOG_LEVEL \
    render $WORLD \
    --layer $LAYER \
    --out $BUILD_DIR

# 3. APP: Start Game Engine
python src/cli.py  \
  --dump-state \
  --dump-sdl \
  --log-level $LOG_LEVEL \
    start $WORLD
```

## Information

### Cython

With the separated extensions, you can import each compiled binary natively and directly into your Python scripts like so:

```python
import libs.core
import libs.math
from libs import render
from libs import registry
```

**VSCode**

To add the Cython libraries to the Pylance linter in VSCODE,

```json
{
  "python.analysis.extraPaths": [
    "./libs"
  ]
}
```

### Scripts

```bash
# 1. Concatenate: Take all images in a directory and concatenate horizontally into a single row of frames.
python ./scripts/concatenate/main.py \
  -d /path/ \
  -o /path/result.png

# 2. Transpose: Convert a vertical column of frames into a horizontal row of frames.
python ./scripts/concatenate/main.py \
  -v int \
  -f /path/ \
  -o /path/result.png
```

## Index

This section provides an overview of the project's directory and file structure.

* `setup.py`: Script for compiling Cython libraries.
* `main.py`: Application entrypoint.

### /docs

`mkdocs` documentation markdown files.


### /scripts

Helper scripts.

* `/scripts/concatenate`: Script to concatenate image files into a row of frames.
* `/scripts/transpose`: Script to transpose a column of frames into a row of frames.

### /src

Application source code.

* `cli.py`: Application command line interface.
* `/src/libs`: Cython packages.
* `/src/app/`: Application packages.
* `/src/assets/`: Application assets.
* `/src/data/`: Application data.

### /tests

Various test

* `/tests/sdl/graphics`: Exploratory Cythonized SDL rendering test.
* `/tests/sdl/sound`: Exploratory Cythonized SDL mixing test.

## References

* [Cython](https://pypi.org/project/Cython/)
* [SDL2](https://wiki.libsdl.org/SDL2/FrontPage)
* [LiberatedPixelCup](https://lpc.opengameart.org/static/LPC-Style-Guide/build/styleguide.html)
