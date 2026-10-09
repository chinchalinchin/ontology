from setuptools import Extension, setup
from Cython.Build import cythonize

ext = Extension(
    name="sound",
    sources=["sound.pyx"],
    libraries=["SDL2"],
)

setup(
    ext_modules=cythonize([ext], compiler_directives={"language_level": "3"}),
)