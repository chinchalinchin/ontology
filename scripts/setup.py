from setuptools import setup
from Cython.Build import cythonize


setup(
    zip_safe=False,
    ext_modules=cythonize(["src/onta/engine/static/*.pyx"])
)