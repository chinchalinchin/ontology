import os
from setuptools import setup
from Cython.Build import cythonize

script_path = os.path.dirname(
    os.path.realpath(__file__)
)
static_path = os.path.join(
    script_path,
    'src',
    'onta',
    'engine',
    'static'
)

setup(
    zip_safe=False,
    ext_modules=[
        cythonize(
            os.path.join(static_path, 'calculator.pyx')
        ),
        cythonize(
            os.path.join(static_path, 'formulae.pyx')
        ),
        cythonize(
            os.path.join(static_path, 'paths.pyx')
        )
    ]
)