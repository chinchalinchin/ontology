from setuptools import setup, Extension
from Cython.Build import cythonize

# Homebrew paths for both Apple Silicon (/opt/homebrew) and Intel (/usr/local)
include_dirs = ["/opt/homebrew/include", "/usr/local/include"]
library_dirs = ["/opt/homebrew/lib", "/usr/local/lib"]

ext_modules = [
    Extension(
        "libs.core.models",
        sources=["libs/core/models.pyx"],
    ),
    Extension(
        "libs.core.input",
        sources=["libs/core/input.pyx"],
        libraries=["SDL2"],
    ),
    Extension(
        "libs.core.math",
        sources=["libs/core/math.pyx"],
    ),
    Extension(
        "libs.graphics.render",
        sources=["libs/graphics/render.pyx"],
        libraries=["SDL2", "SDL2_image"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
    ),
    Extension(
        "libs.graphics.registry",
        sources=["libs/graphics/registry.pyx"],
        libraries=["SDL2", "SDL2_image"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
    )
]

setup(
    name="Ontology Cython Libraries",
    ext_modules=cythonize(ext_modules, compiler_directives={'language_level': "3"}),
)