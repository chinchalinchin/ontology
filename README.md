# Ontology

## Development Setup

Install and build the application dependencies,

```bash
# 1. Install Dependencies
## MacOS
brew install sdl2 sdl2_image
## Linux
sudo apt install libsdl2-dev libsdl2-image-dev

# 2. Build Cython Libraries
python setup.py build_ext --inplace
```

## Index

This section provides an overview of the project's directory and file structure.

- `setup.py`: Script for compiling Cython libraries.
- `main.py`: Application entrypoint.

### /docs

`mkdocs` documentation markdown files.

### /libs

- `sdl2.pyx`: Cython interfaces for SDL2 rendering (currently toy example to illustrate functionality)

### /src

- `cli.py`: Application command line interface.
- `/src/app`: Application source code.
- `/src/assets`: Application assets.
- `/src/data`: Application data.


## References

- [Cython](https://pypi.org/project/Cython/)
- [SDL2](https://wiki.libsdl.org/SDL2/FrontPage)