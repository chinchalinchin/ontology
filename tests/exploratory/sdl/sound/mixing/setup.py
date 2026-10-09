from setuptools import Extension, setup
from Cython.Build import cythonize

ext = Extension(
    name="fur_elise",
    sources=["test.pyx"],
    libraries=["SDL2"],
)

setup(
    ext_modules=cythonize([ext], compiler_directives={"language_level": "3"}),
)