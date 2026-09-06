from setuptools import setup, Extension
from Cython.Build import cythonize

# Homebrew paths for both Apple Silicon (/opt/homebrew) and Intel (/usr/local)
include_dirs = ["/opt/homebrew/include", "/usr/local/include"]
library_dirs = ["/opt/homebrew/lib", "/usr/local/lib"]

ext_modules = [
    Extension(
        "libs.core.models",
        sources=["src/libs/core/models.pyx"],
    ),
    Extension(
        "libs.core.input",
        sources=["src/libs/core/input.pyx"],
        libraries=["SDL2"],
    ),
    Extension(
        "libs.core.math.geometry",
        sources=["src/libs/core/math/geometry.pyx"],
    ),
    Extension(
        "libs.core.math.physics",
        sources=["src/libs/core/math/physics.pyx"],
    ),
    Extension(
        "libs.core.math.space",
        sources=["src/libs/core/math/space.pyx"],
    ),
    Extension(
        "libs.graphics.render",
        sources=["src/libs/graphics/render.pyx"],
        libraries=["SDL2", "SDL2_image", "SDL2_ttf"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
    ),
    Extension(
        "libs.graphics.registry",
        sources=["src/libs/graphics/registry.pyx"],
        libraries=["SDL2", "SDL2_image", "SDL2_ttf"],
        include_dirs=include_dirs,
        library_dirs=library_dirs
    )
]

setup(
    name="Ontology Cython Libraries",
    package_dir={"": "src"}, # Maps the root package namespace to the src/ directory
    ext_modules=cythonize(
        ext_modules, 
        include_path=["src"],
        compiler_directives={
            'language_level': "3",
        }
    ),
)