from sdl import run_test, run_test_headless
from setuptools import setup, Extension
from Cython.Build import cythonize

ext = Extension(
    "test",
    sources=["sdl/test.pyx"],
    libraries=["SDL2", "SDL2_image"],
    include_dirs=["/opt/homebrew/include", "/usr/local/include"],
    library_dirs=["/opt/homebrew/lib", "/usr/local/lib"]
)

setup(ext_modules=cythonize([ext], compiler_directives={'language_level': "3"}))

run_test_headless()