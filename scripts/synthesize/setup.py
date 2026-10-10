from setuptools import Extension, setup
from Cython.Build import cythonize

# Homebrew paths for both Apple Silicon (/opt/homebrew) and Intel (/usr/local)
include_dirs = [
    "/opt/homebrew/include",
    "/opt/homebrew/include/SDL2",
    "/usr/local/include",
    "/usr/local/include/SDL2",
]
library_dirs = [
    "/opt/homebrew/lib", 
    "/usr/local/lib"
]

ext = Extension(
    name="sound",
    sources=["sound.pyx"],
    libraries=["SDL2"],
    include_dirs=include_dirs,
    library_dirs=library_dirs
)

setup(
    ext_modules=cythonize([ext], compiler_directives={"language_level": "3"}),
)