from setuptools import setup

import sys
import os

script_path = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.join(script_path,'src'))

from onta.engine.static.calculator import cc_calculator
from onta.engine.static.formulae import cc_formulae
from onta.engine.static.paths import cc_paths

# doesn't work. 
# tracking on: https://numba.discourse.group/t/setuptools-cant-find-my-gcc-compiler/1506/2

setup(
    ext_modules=[
        cc_calculator.distutils_extension(),
        cc_formulae.distutils_extension(),
        cc_paths.distutils_extension(),
    ]
)