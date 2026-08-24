from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "test",
        ["test.pyx"],
        libraries=["SDL2", "SDL2_ttf"]
    )
]

setup(
    name="Ontology Engine Text Viewer",
    ext_modules=cythonize(extensions, compiler_directives={'language_level': "3"})
)