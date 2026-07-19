from setuptools import setup, Extension
from Cython.Build import cythonize

# Define the C extension
ext_modules = [
    Extension(
        "sdl2_renderer",              # Name of the resulting Python module
        sources=["libs/sdl2.pyx"],# Your Cython source file
        libraries=["SDL2", "SDL2_image"], # The C libraries to link against
    )
]

setup(
    name="Cython SDL2 Render Example",
    ext_modules=cythonize(ext_modules, compiler_directives={'language_level': "3"}),
)