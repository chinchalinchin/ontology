from setuptools import setup

import sys
import os


script_path = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.join(script_path,'src'))


from onta.engine.static.calculator import cc as calc_cc
from onta.engine.static.formulae import cc as form_cc

# calc_cc.compile()
# form_cc.compile()

setup(
    ext_modules=[
        calc_cc.distutils_extension(),
        form_cc.distutils_extension()
    ]
)