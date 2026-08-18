from setuptools import setup, Extension
from Cython.Build import cythonize

ext = Extension(
    "test",                     # The name of your compiled module
    sources=["test.pyx"],        # Your cython source file
    libraries=["SDL2", "SDL2_mixer"],  # <--- Add SDL2_mixer back here
    include_dirs=["/usr/include/SDL2"],  # <--- ADD THIS LINE
)

setup(
    ext_modules=cythonize([ext])
)