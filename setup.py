import os
from setuptools import Extension, setup
from Cython.Build import cythonize

script_path = os.path.dirname(
    os.path.realpath(__file__)
)

static_path = [
    'src',
    'onta',
    'engine',
    'static'
]

# exts = [
#     Extension(
#         name='calculator',
#         sources=['src/onta/engine/static/calculator.pyx']
#     ),
#     Extension(
#         name='formulae',
#         sources=['src/onta/engine/static/formulae.pyx']
#     ),
#     Extension(
#         name='paths',
#         sources=['src/onta/engine/static/paths.pyx']
#     )
# ]

setup(
    zip_safe=False,
    ext_modules=cythonize(["src/onta/engine/static/*.pyx"])
)