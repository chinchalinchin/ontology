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
# 1.Render Background
python src/cli.py prerender world-01 \
  --layer 0 \
  --out /home/grant/Projects/ontology/build

# 2.Render Stateful Assets
python src/cli.py render world-01 \
  --layer 0 \
  --out /home/grant/Projects/ontology/build
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

* `render.pyx`: Cython interfaces for SDL2 rendering.
* `registry.pyx`: Cython class for storing textures.
* `core.pyx`: Cython data classes.
* `math.pyx`: Cython calculations.

### /src

Application source code.

* `cli.py`: Application command line interface.
* `/src/app/`: Application packages.
* `/src/assets/`: Application assets.
* `/src/data/`: Application data.

## References

* [Cython](https://pypi.org/project/Cython/)
* [SDL2](https://wiki.libsdl.org/SDL2/FrontPage)
* [LiberatedPixelCup](https://lpc.opengameart.org/static/LPC-Style-Guide/build/styleguide.html)
