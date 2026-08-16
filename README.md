# Ontology

## Setup

Install and build the application dependencies.

### Install

Cython needs the actual C development headers to compile agains

* **macOS:** `brew install sdl2 sdl2_image`
* **Linux (Debian/Ubuntu):** `sudo apt install libsdl2-dev libsdl2-image-dev`

### Build

To compile the C extensions, run the following command in your terminal:

```bash
python setup.py build_ext --inplace
```

### Debug

```bash
# 0. Clean up state dumps.
rm -rf **/*state-dump.md

# 1.Render Background
python src/cli.py \
  --dump \
  --log-level DEBUG \
  prerender world-01 \
  --layer 0 \
  --out /home/grant/Projects/ontology/build

# 2.Render Stateful Assets
python src/cli.py  \
  --dump \
  --log-level DEBUG \
  render world-01 \
  --layer 0 \
  --out /home/grant/Projects/ontology/build
```

### Helper Scripts

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
## Usage

### Cython

With the separated extensions, you can now import each compiled binary natively and directly into your Python scripts like so:

```python
import libs.core
import libs.math
from libs import render
from libs import registry
```

### VSCode

```json
{
  "python.analysis.extraPaths": [
    "./libs"
  ]
}
```

## Index

This section provides an overview of the project's directory and file structure.

* `setup.py`: Script for compiling Cython libraries.
* `main.py`: Application entrypoint.

### /docs

`mkdocs` documentation markdown files.

### /libs

Cython interfaces and headers.

* `/libs/core`: Core Cython models and functions.
* `/libs/graphics`: Graphics rendering and asset storage.

### /scripts

Helper scripts.

* `concatenate`: Script to concatenate image files into a row of frames.
* `transpose`: Script to transpose a column of frames into a row of frames.

### /src

Application source code.

* `cli.py`: Application command line interface.
* `/src/app/`: Application packages.
* `/src/assets/`: Application assets.
* `/src/data/`: Application data.

### /tests

Various test

* `sdl`: Exploratory Cythonized SDL rendering test.

## References

* [Cython](https://pypi.org/project/Cython/)
* [SDL2](https://wiki.libsdl.org/SDL2/FrontPage)
* [LiberatedPixelCup](https://lpc.opengameart.org/static/LPC-Style-Guide/build/styleguide.html)
