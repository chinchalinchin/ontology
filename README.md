# Ontology

## Development Setup

Install and build the application dependencies.

### 1. Install System Dependencies

Cython needs the actual C development headers to compile agains

* **macOS:** `brew install sdl2 sdl2_image`
* **Linux (Debian/Ubuntu):** `sudo apt install libsdl2-dev libsdl2-image-dev`

### 2. Build Cython Libraries

To compile the C extensions, run the following command in your terminal:

```bash
python setup.py build_ext --inplace
```

*  **The `--inplace` flag:** This instructs setuptools to copy the final compiled binaries (`.so` or `.pyd`) from the `build/lib...` directory directly into your project's `libs/` namespace. Without this flag, the binaries are trapped in the root `build/` directory.
* **Build Outputs:** Because the `setup.py` splits the modules, this command will generate four distinct shared object files inside the `libs/` directory (e.g., `core.<arch>.so`, `math.<arch>.so`, `render.<arch>.so`, and `registry.<arch>.so`).
*  **Cleanup:** Python only looks for the final `.so` files when executing the program. Once compilation is complete, you can safely delete the entire `build/` directory, the generated `.c` files, and the intermediate `.o` object files.


### 3. Importing into Python

With the separated extensions, you can now import each compiled binary natively and directly into your Python scripts like so:

```python
import libs.core
import libs.math
from libs import render
from libs import registry
```

### 4. VSCode Linting Configuration

By default, VSCode's Python language server (Pylance) cannot read compiled `.so` binaries or natively parse `.pyx` Cython syntax for autocomplete. To get VSCode to recognize your libraries, you have two options:

**Option A: Generate Type Stubs (Recommended)**

Create `.pyi` stub files (`core.pyi`, `math.pyi`, `render.pyi`, `registry.pyi`) inside the `libs/` directory that mirror the definitions of your `.pyx` classes and functions. Pylance will automatically read these stubs to provide rich linting, docstrings, and autocomplete.

**Option B: Configure Pylance to Resolve the Binaries**

Update your workspace settings to help the linter resolve imports from the `libs/` directory. Add the following to your `.vscode/settings.json` file:

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
