from setuptools import setup

import sys
import os

script_path = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.join(script_path,'src'))

from onta.engine.static.calculator import cc as calculate_cc
from onta.engine.static.formulae import cc as formula_cc
from onta.engine.static.paths import cc as paths_cc

setup(
    ext_modules=[
        calculate_cc.distutils_extension(),
        formula_cc.distutils_extension(),
        paths_cc.distutils_extension(),
    ]
)