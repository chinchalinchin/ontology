from setuptools import setup, Extension
from Cython.Build import cythonize

# Homebrew paths for both Apple Silicon (/opt/homebrew) and Intel (/usr/local)
include_dirs = ["/opt/homebrew/include", "/usr/local/include"]
library_dirs = ["/opt/homebrew/lib", "/usr/local/lib"]

ext_modules = [
    Extension(
        "sdl2_renderer",
        sources=["libs/sdl2.pyx"],
        libraries=["SDL2", "SDL2_image"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
    )
]

setup(
    name="Cython SDL2 Render Example",
    ext_modules=cythonize(ext_modules, compiler_directives={'language_level': "3"}),
)